/**
 * YouTube Shorts Redroid Studio — Frontend Engine
 * Real-time WebSocket logging, interactive upload automation & hardware controls.
 */

document.addEventListener("DOMContentLoaded", () => {
  // State
  let currentAccount = "01";
  let selectedVideoPath = null;
  let isUploading = false;
  let isPaused = false;
  let timerInterval = null;
  let startTime = null;
  let ws = null;
  let logHistoryRaw = [];

  // Helper for safe JSON fetching with meaningful errors
  async function safeFetchJson(url, options = {}) {
    const res = await fetch(url, options);
    const text = await res.text();
    let data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      if (!res.ok) {
        throw new Error(`Server returned ${res.status}: ${text || res.statusText}`);
      }
      throw new Error(`Unexpected server response: ${text}`);
    }
    if (!res.ok) {
      const msg = data.detail || data.error || data.message || `Request failed with status ${res.status}`;
      throw new Error(msg);
    }
    return data;
  }

  // DOM Elements
  const accountSelect = document.getElementById("accountSelect");
  const customAccountInput = document.getElementById("customAccountInput");
  const adbStatusBadge = document.getElementById("adbStatusBadge");
  const adbStatusText = document.getElementById("adbStatusText");
  const btnScrcpy = document.getElementById("btnScrcpy");
  const btnStartContainer = document.getElementById("btnStartContainer");
  const btnStopContainer = document.getElementById("btnStopContainer");
  const btnCleanDrafts = document.getElementById("btnCleanDrafts");

  const dropzone = document.getElementById("dropzone");
  const videoFileInput = document.getElementById("videoFileInput");
  const fileSelectedPill = document.getElementById("fileSelectedPill");
  const selectedFileName = document.getElementById("selectedFileName");
  const selectedFileSize = document.getElementById("selectedFileSize");
  const btnRemoveFile = document.getElementById("btnRemoveFile");
  const serverFilesSelect = document.getElementById("serverFilesSelect");

  const shortTitle = document.getElementById("shortTitle");
  const tagPills = document.querySelectorAll(".tag-pill");
  const soundQuery = document.getElementById("soundQuery");
  const tsPills = document.querySelectorAll(".ts-pill");
  const customTimestampInput = document.getElementById("customTimestampInput");
  const mediaName = document.getElementById("mediaName");

  const btnLaunchUpload = document.getElementById("btnLaunchUpload");
  const liveControlBar = document.getElementById("liveControlBar");
  const btnPauseResume = document.getElementById("btnPauseResume");
  const pauseBtnIcon = document.getElementById("pauseBtnIcon");
  const pauseBtnText = document.getElementById("pauseBtnText");
  const btnStopUpload = document.getElementById("btnStopUpload");

  const terminalOutput = document.getElementById("terminalOutput");
  const terminalContainer = document.getElementById("terminalContainer");
  const chkAutoScroll = document.getElementById("chkAutoScroll");
  const logFilterInput = document.getElementById("logFilterInput");
  const btnCopyLogs = document.getElementById("btnCopyLogs");
  const btnClearLogs = document.getElementById("btnClearLogs");
  const terminalTimer = document.getElementById("terminalTimer");

  const statTarget = document.getElementById("statTarget");
  const statJobStatus = document.getElementById("statJobStatus");
  const statPauseState = document.getElementById("statPauseState");

  // ==========================================
  // 1. Toast Notifications
  // ==========================================
  function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  // ==========================================
  // 2. WebSocket Log Streaming Engine
  // ==========================================
  function connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/logs`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      document.getElementById("wsStatusBadge").className = "status-pill status-online";
    };

    ws.onmessage = (event) => {
      const text = event.data;
      if (text === "pong") return;
      appendTerminalLog(text);
    };

    ws.onclose = () => {
      document.getElementById("wsStatusBadge").className = "status-pill status-offline";
      setTimeout(connectWebSocket, 2000);
    };

    ws.onerror = () => {
      ws.close();
    };

    // Heartbeat ping every 25s
    setInterval(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send("ping");
      }
    }, 25000);
  }

  function appendTerminalLog(rawText) {
    logHistoryRaw.push(rawText);
    const filter = logFilterInput.value.toLowerCase().trim();

    const lines = rawText.split("\n");
    for (const line of lines) {
      if (!line.trim()) continue;

      const div = document.createElement("div");
      div.className = "terminal-line";

      const lower = line.toLowerCase();
      if (lower.includes("[success]") || lower.includes("uploaded successfully")) {
        div.classList.add("success");
      } else if (lower.includes("[error]") || lower.includes("failed") || lower.includes("exception") || lower.includes("keyboardinterrupt")) {
        div.classList.add("error");
      } else if (lower.includes("[system]")) {
        div.classList.add("system");
      } else if (lower.includes("[+]")) {
        div.classList.add("info");
      } else if (lower.includes("[warn]")) {
        div.classList.add("warn");
      } else if (lower.includes("paused") || lower.includes("⏸")) {
        div.classList.add("pause");
      }

      div.textContent = line;

      if (filter && !lower.includes(filter)) {
        div.style.display = "none";
      }

      terminalOutput.appendChild(div);
    }

    if (chkAutoScroll.checked) {
      terminalContainer.scrollTop = terminalContainer.scrollHeight;
    }
  }

  // Filter logs on search input
  logFilterInput.addEventListener("input", () => {
    const filter = logFilterInput.value.toLowerCase().trim();
    const lineElements = terminalOutput.querySelectorAll(".terminal-line");
    lineElements.forEach((el) => {
      if (!filter || el.textContent.toLowerCase().includes(filter)) {
        el.style.display = "";
      } else {
        el.style.display = "none";
      }
    });
  });

  // Clear Terminal
  btnClearLogs.addEventListener("click", () => {
    terminalOutput.innerHTML = '<div class="terminal-line system">[SYSTEM] Console cleared.</div>';
    logHistoryRaw = [];
  });

  // Copy Logs to Clipboard
  btnCopyLogs.addEventListener("click", () => {
    const allText = logHistoryRaw.join("");
    navigator.clipboard.writeText(allText).then(() => {
      showToast("All logs copied to clipboard!", "success");
    }).catch(() => {
      showToast("Failed to copy logs.", "error");
    });
  });

  // ==========================================
  // 3. System Status & Telemetry Polling
  // ==========================================
  function getActiveAccount() {
    if (accountSelect.value === "custom") {
      return customAccountInput.value.trim() || "5555";
    }
    return accountSelect.value;
  }

  async function pollStatus() {
    const acc = getActiveAccount();
    try {
      const res = await fetch(`/api/status?account=${encodeURIComponent(acc)}`);
      if (!res.ok) return;
      const data = await res.json();

      // ADB Status Badge
      if (data.adb_status === "online") {
        adbStatusBadge.className = "status-pill status-online";
        adbStatusText.textContent = `ADB Online (${data.target})`;
      } else {
        adbStatusBadge.className = "status-pill status-offline";
        adbStatusText.textContent = `ADB Offline (${data.target})`;
      }

      statTarget.textContent = data.target;

      // Upload State
      if (data.is_uploading) {
        isUploading = true;
        statJobStatus.textContent = "UPLOADING...";
        statJobStatus.className = "stat-val";
        statJobStatus.style.color = "var(--accent-amber)";
        btnLaunchUpload.disabled = true;
        btnLaunchUpload.style.opacity = "0.5";
        liveControlBar.classList.remove("bar-hidden");

        if (!startTime) {
          startTime = data.active_job?.start_time ? data.active_job.start_time * 1000 : Date.now();
          startTimer();
        }
      } else {
        if (isUploading) {
          // Just finished
          stopTimer();
        }
        isUploading = false;
        statJobStatus.textContent = "IDLE";
        statJobStatus.className = "stat-val stat-idle";
        statJobStatus.style.color = "";
        btnLaunchUpload.disabled = false;
        btnLaunchUpload.style.opacity = "1";
        liveControlBar.classList.add("bar-hidden");
      }

      // Pause State
      isPaused = data.is_paused;
      if (isPaused) {
        statPauseState.textContent = "PAUSED (WAITING)";
        statPauseState.style.color = "var(--accent-amber)";
        btnPauseResume.classList.add("paused");
        pauseBtnIcon.textContent = "▶";
        pauseBtnText.textContent = "Resume";
      } else {
        statPauseState.textContent = "ACTIVE (RUNNING)";
        statPauseState.style.color = "var(--accent-emerald)";
        btnPauseResume.classList.remove("paused");
        pauseBtnIcon.textContent = "⏸";
        pauseBtnText.textContent = "Pause";
      }
    } catch (e) {
      console.error("Status poll error:", e);
    }
  }

  // Timer helper
  function startTimer() {
    if (timerInterval) clearInterval(timerInterval);
    timerInterval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      const mins = String(Math.floor(elapsed / 60)).padStart(2, "0");
      const secs = String(elapsed % 60).padStart(2, "0");
      terminalTimer.textContent = `${mins}:${secs}`;
    }, 1000);
  }

  function stopTimer() {
    if (timerInterval) clearInterval(timerInterval);
    timerInterval = null;
    startTime = null;
  }

  // ==========================================
  // 4. Target Account Selector
  // ==========================================
  accountSelect.addEventListener("change", () => {
    if (accountSelect.value === "custom") {
      customAccountInput.classList.remove("custom-acc-hidden");
      customAccountInput.focus();
    } else {
      customAccountInput.classList.add("custom-acc-hidden");
    }
    pollStatus();
  });

  customAccountInput.addEventListener("input", () => {
    pollStatus();
  });

  // ==========================================
  // 5. Hardware Actions (Scrcpy, Start, Stop, Clean)
  // ==========================================
  btnScrcpy.addEventListener("click", async () => {
    const acc = getActiveAccount();
    showToast("Launching Scrcpy desktop view...", "info");
    try {
      const data = await safeFetchJson("/api/container/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "scrcpy", account: acc })
      });
      if (data.success) {
        showToast("Scrcpy launched successfully!", "success");
      } else {
        showToast(`Scrcpy launch error: ${data.error || 'Failed'}`, "error");
      }
    } catch (e) {
      showToast(`Scrcpy launch failed: ${e.message}`, "error");
    }
  });

  btnStartContainer.addEventListener("click", async () => {
    const acc = getActiveAccount();
    showToast(`Starting container ${acc}...`, "info");
    try {
      await safeFetchJson("/api/container/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "start", account: acc })
      });
    } catch (e) {
      showToast(`Container start error: ${e.message}`, "error");
    }
  });

  btnStopContainer.addEventListener("click", async () => {
    const acc = getActiveAccount();
    showToast(`Stopping container ${acc}...`, "info");
    try {
      await safeFetchJson("/api/container/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "stop", account: acc })
      });
    } catch (e) {
      showToast(`Container stop error: ${e.message}`, "error");
    }
  });

  btnCleanDrafts.addEventListener("click", async () => {
    const acc = getActiveAccount();
    if (!confirm(`Reset MediaStore and clean YouTube drafts for ${acc}?`)) return;
    showToast("Cleaning upload session...", "info");
    try {
      await safeFetchJson("/api/upload/clean", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ account: acc })
      });
    } catch (e) {
      showToast(`Clean drafts error: ${e.message}`, "error");
    }
  });

  // ==========================================
  // 6. File Dropzone & Server Media Library
  // ==========================================
  async function loadServerFiles() {
    try {
      const res = await fetch("/api/files");
      if (!res.ok) return;
      const data = await res.json();
      serverFilesSelect.innerHTML = '<option value="">-- Choose from server uploads --</option>';
      data.files.forEach((file) => {
        const opt = document.createElement("option");
        opt.value = file.path;
        opt.textContent = `${file.name} (${file.size_mb} MB)`;
        serverFilesSelect.appendChild(opt);
      });

      // If sample_short.mp4 exists, auto-select it if nothing selected
      if (!selectedVideoPath && data.files.length > 0) {
        selectFile(data.files[0].path, data.files[0].name, `${data.files[0].size_mb} MB`);
      }
    } catch (e) {
      console.error("Load files error:", e);
    }
  }

  function selectFile(path, name, sizeStr) {
    selectedVideoPath = path;
    selectedFileName.textContent = name;
    selectedFileSize.textContent = sizeStr || "";
    fileSelectedPill.classList.remove("file-pill-hidden");
    dropzone.style.display = "none";

    // Auto-fill title if empty
    if (!shortTitle.value.trim()) {
      const stem = name.replace(/\.[^/.]+$/, "").replace(/[_-]/g, " ");
      shortTitle.value = `${stem} #shorts`;
    }
  }

  function clearSelectedFile() {
    selectedVideoPath = null;
    fileSelectedPill.classList.add("file-pill-hidden");
    dropzone.style.display = "";
    videoFileInput.value = "";
    serverFilesSelect.value = "";
  }

  btnRemoveFile.addEventListener("click", clearSelectedFile);

  serverFilesSelect.addEventListener("change", () => {
    if (serverFilesSelect.value) {
      const selectedOption = serverFilesSelect.options[serverFilesSelect.selectedIndex];
      selectFile(serverFilesSelect.value, selectedOption.textContent.split(" (")[0], "");
    }
  });

  // Dropzone events
  dropzone.addEventListener("click", () => videoFileInput.click());

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", async (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  videoFileInput.addEventListener("change", () => {
    if (videoFileInput.files.length > 0) {
      handleFileUpload(videoFileInput.files[0]);
    }
  });

  async function handleFileUpload(file) {
    showToast(`Uploading ${file.name}...`, "info");
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/upload_file", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      if (data.success) {
        showToast("Video uploaded successfully!", "success");
        selectFile(data.path, data.filename, `${data.size_mb} MB`);
        loadServerFiles();
      } else {
        showToast("Upload failed.", "error");
      }
    } catch (e) {
      showToast(`Upload error: ${e}`, "error");
    }
  }

  // ==========================================
  // 7. Metadata Tags & Timestamp Pills
  // ==========================================
  tagPills.forEach((pill) => {
    pill.addEventListener("click", () => {
      const tag = pill.getAttribute("data-tag");
      if (!shortTitle.value.includes(tag)) {
        shortTitle.value = (shortTitle.value.trim() + " " + tag).trim();
      }
      shortTitle.focus();
    });
  });

  let selectedTimestamp = null;
  tsPills.forEach((pill) => {
    pill.addEventListener("click", () => {
      tsPills.forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      const ts = pill.getAttribute("data-ts");

      if (ts === "custom") {
        customTimestampInput.classList.remove("custom-ts-hidden");
        customTimestampInput.focus();
        selectedTimestamp = customTimestampInput.value.trim() || "0:15";
      } else {
        customTimestampInput.classList.add("custom-ts-hidden");
        selectedTimestamp = ts === "default" ? null : ts;
      }
    });
  });

  customTimestampInput.addEventListener("input", () => {
    selectedTimestamp = customTimestampInput.value.trim();
  });

  // ==========================================
  // 8. Launch Upload Automation
  // ==========================================
  btnLaunchUpload.addEventListener("click", async () => {
    if (!selectedVideoPath) {
      showToast("Please select a video file first!", "error");
      return;
    }

    const title = shortTitle.value.trim();
    if (!title) {
      showToast("Please enter a title for the Short!", "error");
      shortTitle.focus();
      return;
    }

    const payload = {
      video_path: selectedVideoPath,
      account: getActiveAccount(),
      title: title,
      sound: soundQuery.value.trim() || null,
      timestamp: selectedTimestamp,
      media_name: mediaName.value.trim() || null
    };

    try {
      const data = await safeFetchJson("/api/upload/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (data.success) {
        showToast("Upload automation launched!", "success");
        pollStatus();
      } else {
        showToast(`Launch failed: ${data.detail || data.error}`, "error");
      }
    } catch (e) {
      showToast(`Upload start failed: ${e.message}`, "error");
    }
  });

  // Pause / Resume Toggle
  btnPauseResume.addEventListener("click", async () => {
    const acc = getActiveAccount();
    const endpoint = isPaused ? "/api/upload/resume" : "/api/upload/pause";
    try {
      const data = await safeFetchJson(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ account: acc })
      });
      if (data.success) {
        pollStatus();
      }
    } catch (e) {
      showToast(`Pause/Resume error: ${e.message}`, "error");
    }
  });

  // Stop / Abort Upload
  btnStopUpload.addEventListener("click", async () => {
    if (!confirm("Are you sure you want to abort the current upload?")) return;
    try {
      await safeFetchJson("/api/upload/stop", { method: "POST" });
      pollStatus();
    } catch (e) {
      showToast(`Stop error: ${e.message}`, "error");
    }
  });

  // ==========================================
  // 9. Startup Initializations
  // ==========================================
  connectWebSocket();
  loadServerFiles();
  pollStatus();
  setInterval(pollStatus, 3000);
});
