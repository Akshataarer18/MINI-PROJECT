const $ = (id) => document.getElementById(id);
const state = {version: 1, content: "", log: []};

function timeNow() {
  return new Date().toLocaleTimeString([], {hour: "2-digit", minute: "2-digit", second: "2-digit"});
}
function setBanner(type, title, message) {
  const banner = $("resultBanner");
  banner.className = `result-banner ${type}`;
  const symbols = {neutral: "i", success: "✓", error: "×", warning: "!"};
  banner.querySelector(".result-symbol").textContent = symbols[type] || "i";
  banner.querySelector("b").textContent = title;
  banner.querySelector("p").textContent = message;
}
function updateVersion(version) {
  state.version = version;
  $("versionMetric").textContent = version;
  $("versionChip").textContent = version;
}
function updateCharCount() {
  $("charCount").textContent = $("documentContent").value.length.toLocaleString();
}
function renderLog() {
  const tbody = $("activityRows");
  if (!state.log.length) {
    tbody.innerHTML = '<tr class="empty-row"><td colspan="5">No actions yet. Submit an edit to see the engine response.</td></tr>';
    return;
  }
  tbody.innerHTML = state.log.slice(0, 12).map(item => {
    const klass = item.result === "ACCEPTED" ? "accepted" : item.result === "CONFLICT" ? "conflict" : "rejected";
    return `<tr>
      <td>${item.time}</td>
      <td><span class="table-user"><span class="mini-avatar">${escapeHtml(item.user.slice(0,1).toUpperCase())}</span>${escapeHtml(item.user)}</span></td>
      <td>${escapeHtml(item.operation)}</td>
      <td><span class="result-pill ${klass}">${item.result}</span></td>
      <td>v${item.version ?? "—"}</td>
    </tr>`;
  }).join("");
}
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}
function addLog(user, operation, result, version) {
  state.log.unshift({time: timeNow(), user, operation, result, version});
  renderLog();
  $("lastOperation").textContent = result;
  $("lastOperationTime").textContent = `Last action at ${timeNow()}`;
  $("conflictMetric").textContent = result === "CONFLICT" ? "Detected" : result === "REJECTED" ? "Blocked" : "Ready";
}
async function api(path, options = {}) {
  const response = await fetch(path, {cache: "no-store", ...options});
  let data;
  try { data = await response.json(); } catch { data = {message: "Server returned an unreadable response."}; }
  return {ok: response.ok, status: response.status, data};
}
async function loadDocument(updateEditor = true) {
  try {
    const result = await api("/api/document");
    if (!result.ok) throw new Error(result.data.message || "Unable to load document.");
    state.content = result.data.content;
    updateVersion(result.data.version);
    if (updateEditor) {
      $("documentContent").value = state.content;
      $("expectedVersion").value = state.version;
      updateCharCount();
    }
    $("serverStatus").textContent = "Online";
    return result.data;
  } catch (err) {
    $("serverStatus").textContent = "Offline";
    setBanner("error", "API unavailable", "Start the Python server with: python app.py");
    throw err;
  }
}
async function checkHealth() {
  try {
    const result = await api("/api/health");
    $("serverStatus").textContent = result.ok ? "Online" : "Offline";
    if (result.ok) await loadDocument();
  } catch {
    $("serverStatus").textContent = "Offline";
    setBanner("error", "Backend not connected", "Open a terminal in the project folder and run: python app.py");
  }
}
async function submitEdit({stale = false} = {}) {
  const button = $("submitEdit");
  button.disabled = true;
  const user = $("username").value;
  const expected = stale ? Math.max(1, state.version - 1) : Number($("expectedVersion").value);
  const payload = {
    username: user,
    content: $("documentContent").value,
    can_edit: $("permissionToggle").checked,
    expected_version: expected
  };
  try {
    const result = await api("/api/edit", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const data = result.data;
    const op = stale ? "Simulated stale edit" : "Submit document edit";
    addLog(user, op, data.status || "REJECTED", data.version ?? data.current_version ?? state.version);
    if (data.status === "ACCEPTED") {
      updateVersion(data.version);
      $("expectedVersion").value = data.version;
      state.content = data.content;
      setBanner("success", "Update accepted", `${data.message} Current document version is v${data.version}.`);
      $("conflictMetric").textContent = "Ready";
    } else if (data.status === "CONFLICT") {
      updateVersion(data.current_version);
      setBanner("warning", "Version conflict detected", `${data.message} Current server version is v${data.current_version}. Click “Load latest” to refresh.`);
      $("conflictMetric").textContent = "Detected";
    } else {
      setBanner("error", "Edit rejected", data.message || "The edit could not be accepted.");
    }
  } catch {
    setBanner("error", "Request failed", "Check that the Python API server is running.");
  } finally {
    button.disabled = false;
  }
}
$("documentContent").addEventListener("input", updateCharCount);
$("submitEdit").addEventListener("click", () => submitEdit());
$("reloadDocument").addEventListener("click", async () => {
  try {
    await loadDocument(true);
    setBanner("success", "Latest version loaded", `Document content and expected version are now set to v${state.version}.`);
  } catch {}
});
$("simulateStale").addEventListener("click", async () => {
  // Make sure the simulated request is stale when possible. If current version is 1,
  // first submit an accepted edit, then send an older version.
  try {
    await loadDocument(false);
    if (state.version === 1) {
      const first = await api("/api/edit", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          username: "Alice",
          content: state.content,
          can_edit: true,
          expected_version: 1
        })
      });
      if (first.data.status === "ACCEPTED") {
        updateVersion(first.data.version);
        addLog("Alice", "Setup version for demo", "ACCEPTED", first.data.version);
      }
    }
    const latest = await api("/api/document");
    if (latest.ok) updateVersion(latest.data.version);
    const oldVersion = Math.max(1, state.version - 1);
    $("expectedVersion").value = oldVersion;
    setBanner("neutral", "Sending stale request…", `Submitting an update using old version v${oldVersion}.`);
    await submitEdit({stale: true});
  } catch {}
});
$("clearLog").addEventListener("click", () => { state.log = []; renderLog(); });
checkHealth();
