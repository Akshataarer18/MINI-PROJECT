"""
SyncGuard E1 — Concurrency & Synchronization Engine
Educational Sprint 1 prototype.

Features:
- Thread-safe in-process document state.
- Permission gate (demo input; real E2 integration is not included).
- Optimistic version checking.
- Whole-document replacement with conflict detection.
- Version increments only after an accepted edit.

Limitations:
- In-memory only: restart the server to reset the document.
- Lock protects threads in this one process, not multiple processes/machines.
- Whole-document replacement is not character-level collaborative merging.
"""
from threading import Lock
from typing import Any, Dict


class ConcurrencyEngine:
    def __init__(self, initial_content: str = "Welcome to SyncGuard!\n\nEdit this shared document to try E1.") -> None:
        self._content = initial_content
        self._version = 1
        self._lock = Lock()

    @property
    def content(self) -> str:
        with self._lock:
            return self._content

    @property
    def version(self) -> int:
        with self._lock:
            return self._version

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {"content": self._content, "version": self._version}

    def apply_edit(self, username: str, new_content: str, can_edit: bool, expected_version: int) -> Dict[str, Any]:
        username = (username or "").strip()[:60]
        if not username:
            return {"status": "REJECTED", "message": "Please provide a user name."}
        if not isinstance(new_content, str):
            return {"status": "REJECTED", "message": "Document content must be text."}
        if len(new_content) > 20000:
            return {"status": "REJECTED", "message": "Document is too large (20,000 characters maximum)."}
        if not can_edit:
            return {"status": "REJECTED", "message": "Edit permission denied for this demo request."}
        try:
            expected_version = int(expected_version)
        except (TypeError, ValueError):
            return {"status": "REJECTED", "message": "A valid expected version is required."}

        with self._lock:
            if expected_version != self._version:
                return {
                    "status": "CONFLICT",
                    "message": "Your copy is out of date. Load the latest version before submitting again.",
                    "current_version": self._version,
                    "content": self._content,
                }
            self._content = new_content
            self._version += 1
            return {
                "status": "ACCEPTED",
                "message": "Update accepted. Document version incremented.",
                "user": username,
                "content": self._content,
                "version": self._version,
            }


def demo() -> None:
    engine = ConcurrencyEngine("Initial document")
    print("SyncGuard E1 — Concurrency & Synchronization Engine")
    print("=" * 58)
    print("1) Alice submits version 1:", engine.apply_edit("Alice", "Alice's saved edit", True, 1))
    print("2) Bob submits stale version 1:", engine.apply_edit("Bob", "Bob's stale edit", True, 1))
    print("3) Charlie has no edit permission:", engine.apply_edit("Charlie", "Blocked edit", False, 2))
    print("Final snapshot:", engine.snapshot())


if __name__ == "__main__":
    demo()
