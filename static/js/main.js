const state = {
  tab: "camera",
  mode: "basic",
  pred: null,
  busy: false,
  cameraActive: false,
  uploadImage: null,
  welcomeSaid: false
};

const els = {
  root: document.documentElement,
  tabs: document.querySelectorAll(".tab"),
  panelCamera: document.getElementById("panel-camera"),
  panelUpload: document.getElementById("panel-upload"),
  video: document.getElementById("video"),
  cameraShot: document.getElementById("camera-shot"),
  cameraEmpty: document.getElementById("camera-empty"),
  btnCameraStart: document.getElementById("btn-camera-start"),
  btnCameraStop: document.getElementById("btn-camera-stop"),
  captureBar: document.getElementById("capture-bar"),
  btnCapture: document.getElementById("btn-capture"),
  btnSpeak: document.getElementById("btn-speak"),
  btnTheme: document.getElementById("btn-theme"),
  fileInput: document.getElementById("file-input"),
  canvas: document.getElementById("canvas"),
  autoToggle: document.getElementById("auto-toggle"),
  autoSpeak: document.getElementById("auto-speak"),
  badgeTime: document.getElementById("badge-time"),
  badgeTime2: document.getElementById("badge-time2"),
  sourceStatus: document.getElementById("source-status"),
  announcer: document.getElementById("announcer"),
  bars: document.getElementById("bars"),
  dropzone: document.getElementById("dropzone"),
  uploadCard: document.getElementById("upload-card"),
  uploadImg: document.getElementById("upload-img"),
  btnChange: document.getElementById("btn-change"),
  dominant: document.querySelector(".dominant"),
  dominantSwatch: document.getElementById("dominant-swatch"),
  dominantName: document.getElementById("dominant-name"),
  dominantProb: document.getElementById("dominant-prob")
};

function setStatus(text, kind) {
  els.sourceStatus.textContent = text;
  els.announcer.classList.remove("show", "err");
  if (kind === "err") {
    els.announcer.textContent = text;
    els.announcer.classList.add("err");
  }
}

function currentList() {
  if (!state.pred) return null;
  return state.mode === "basic" ? state.pred.basic : state.pred.detail;
}

function speak(text) {
  if (!("speechSynthesis" in window) || !text) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "id-ID";
  utterance.rate = 0.95;
  const voice = window.speechSynthesis
    .getVoices()
    .find(v => /^id(-|_)?/i.test(v.lang));
  if (voice) utterance.voice = voice;
  window.speechSynthesis.speak(utterance);
}

function welcome() {
  if (state.welcomeSaid) return;
  state.welcomeSaid = true;
  speak("ColorSense siap. Gunakan mode Kamera untuk objek langsung, atau mode Unggah untuk memilih gambar. Tekan K atau U.");
}

ding.ctx = null;
function ding() {
  const audio = ding.ctx || (ding.ctx = new (window.AudioContext || window.webkitAudioContext)());
  if (audio.state === "suspended") audio.resume();
  [880, 1320].forEach((freq, i) => {
    const osc = audio.createOscillator();
    const gain = audio.createGain();
    const start = audio.currentTime + i * 0.09;
    osc.type = "sine";
    osc.frequency.value = freq;
    gain.gain.setValueAtTime(0.0001, start);
    gain.gain.exponentialRampToValueAtTime(0.18, start + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.0001, start + 0.12);
    osc.connect(gain).connect(audio.destination);
    osc.start(start);
    osc.stop(start + 0.14);
  });
}

document.addEventListener("pointerdown", welcome, { once: true, capture: true });
document.addEventListener("keydown", welcome, { once: true, capture: true });

function applyTheme(theme) {
  els.root.setAttribute("data-theme", theme);
  try {
    localStorage.setItem("colorsense-theme", theme);
  } catch (err) {}
}

(function initTheme() {
  let saved = null;
  try {
    saved = localStorage.getItem("colorsense-theme");
  } catch (err) {}
  applyTheme(saved === "dark" || saved === "light" ? saved : "light");
})();

function toggleTheme() {
  const next = els.root.getAttribute("data-theme") === "dark" ? "light" : "dark";
  applyTheme(next);
  speak(next === "dark" ? "Tema gelap" : "Tema terang");
}

function renderCameraState() {
  els.cameraEmpty.hidden = state.cameraActive;
  els.captureBar.hidden = !state.cameraActive;
}

function stopCamera(silent) {
  if (els.video.srcObject) {
    els.video.srcObject.getTracks().forEach(t => t.stop());
    els.video.srcObject = null;
  }
  state.cameraActive = false;
  els.video.hidden = true;
  els.cameraShot.hidden = true;
  renderCameraState();
  setStatus("Kamera dihentikan.");
  if (!silent) speak("Kamera dihentikan.");
}

async function startCamera() {
  if (state.cameraActive) return;
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, facingMode: "environment" },
      audio: false
    });
    els.video.srcObject = stream;
    await els.video.play();
    state.cameraActive = true;
    els.video.hidden = false;
    els.cameraShot.hidden = true;
    els.cameraEmpty.hidden = true;
    renderCameraState();
    setStatus("Kamera aktif. Arahkan objek, lalu tekan Spasi untuk deteksi.");
    speak("Kamera aktif. Arahkan objek, lalu tekan Spasi untuk deteksi.");
  } catch (err) {
    setStatus("Akses kamera ditolak. Gunakan mode Unggah Gambar.", "err");
    speak("Akses kamera ditolak. Silakan unggah gambar.");
    renderCameraState();
  }
}

function grabFrameDataUrl() {
  const video = els.video;
  if (!video.videoWidth) return null;
  const maxWidth = 640;
  const scale = Math.min(1, maxWidth / video.videoWidth);
  els.canvas.width = Math.round(video.videoWidth * scale);
  els.canvas.height = Math.round(video.videoHeight * scale);
  const ctx = els.canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, els.canvas.width, els.canvas.height);
  return els.canvas.toDataURL("image/jpeg", 0.9);
}

async function predict(dataUrl) {
  if (state.busy) return;
  state.busy = true;
  document.body.classList.add("is-analyzing");
  setStatus("Menganalisis gambar, mohon tunggu...");
  try {
    const response = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image: dataUrl })
    });
    const data = await response.json();
    if (!response.ok) {
      setStatus(data.error || "Gagal memproses gambar.", "err");
      speak("Gagal memproses gambar, coba lagi.");
      els.dominant.classList.remove("low");
      els.dominantName.textContent = "-";
      els.dominantProb.textContent = "Belum ada hasil deteksi";
      els.dominantSwatch.style.background = "transparent";
    } else {
      state.pred = data;
      render();
      const label = data.time_ms + " ms";
      els.badgeTime.hidden = false;
      els.badgeTime.textContent = label;
      els.badgeTime2.hidden = false;
      els.badgeTime2.textContent = label;
      ding();
      if (els.autoSpeak.checked) speak(buildResultSpeech());
      els.announcer.classList.remove("err");
    }
  } catch (err) {
    setStatus("Gagal menghubungi server.", "err");
    speak("Gagal menghubungi server.");
  } finally {
    state.busy = false;
    document.body.classList.remove("is-analyzing");
  }
}

function capture() {
  if (!state.cameraActive) {
    setStatus("Aktifkan kamera lebih dulu.", "err");
    return;
  }
  if (state.busy) return;
  const dataUrl = grabFrameDataUrl();
  if (!dataUrl) return;
  els.cameraShot.src = dataUrl;
  els.cameraShot.hidden = false;
  els.video.hidden = true;
  setStatus("Pratinjau tangkapan kamera.");
  predict(dataUrl);
}

function handleFile(file) {
  if (!file || !/^image\//.test(file.type)) {
    setStatus("File tidak didukung. Gunakan gambar JPG atau PNG.", "err");
    speak("Format file tidak didukung, gunakan gambar.");
    return;
  }
  const reader = new FileReader();
  reader.onload = () => {
    state.uploadImage = String(reader.result);
    els.uploadImg.src = state.uploadImage;
    els.dropzone.hidden = true;
    els.uploadCard.hidden = false;
    setStatus("Gambar diterima, menganalisis...");
    predict(state.uploadImage);
  };
  reader.readAsDataURL(file);
}

function openUploadPicker() {
  els.fileInput.click();
}

function switchTab(tab) {
  state.tab = tab;
  els.tabs.forEach(btn => {
    const active = btn.dataset.tab === tab;
    btn.classList.toggle("active", active);
    btn.setAttribute("aria-selected", String(active));
  });
  els.panelCamera.hidden = tab !== "camera";
  els.panelUpload.hidden = tab !== "upload";
  if (tab === "camera") {
    renderCameraState();
    if (state.cameraActive && els.video.srcObject) {
      els.video.hidden = false;
      els.cameraShot.hidden = true;
      setStatus("Mode kamera. Tekan Spasi untuk ambil.");
    } else {
      setStatus("Mode kamera. Tekan tombol Aktifkan Kamera.");
    }
  } else {
    if (state.cameraActive) stopCamera(true);
    if (state.uploadImage) {
      els.uploadImg.src = state.uploadImage;
      els.dropzone.hidden = true;
      els.uploadCard.hidden = false;
      setStatus("Mode unggah. Klik Ganti Gambar untuk memilih ulang.");
    } else {
      els.dropzone.hidden = false;
      els.uploadCard.hidden = true;
      setStatus("Mode unggah. Klik kotak atau seret gambar ke dalamnya.");
    }
  }
}

function render() {
  const list = currentList();
  if (!list) return;
  const top = list[0];
  els.dominant.classList.toggle("low", !top.active);
  els.dominantSwatch.style.background = top.hex;
  els.dominantName.textContent = top.name;
  els.dominantProb.textContent = top.active
    ? "Keyakinan " + top.prob + "%"
    : "Keyakinan " + top.prob + "% - rendah";
  els.bars.innerHTML = "";
  list.forEach(entry => {
    const row = document.createElement("div");
    row.className = "bar-row" + (entry.active ? "" : " inactive");
    row.style.setProperty("--dot-color", entry.hex);
    const label = document.createElement("span");
    label.className = "bar-label";
    label.textContent = entry.name;
    const dot = document.createElement("div");
    dot.className = "bar-dot";
    const track = document.createElement("div");
    track.className = "bar-track";
    const fill = document.createElement("div");
    fill.className = "bar-fill";
    fill.style.width = entry.prob + "%";
    track.appendChild(fill);
    const val = document.createElement("span");
    val.className = "bar-val";
    val.textContent = entry.prob + "%";
    row.append(label, dot, track, val);
    els.bars.appendChild(row);
  });
}

function buildResultSpeech() {
  const list = currentList();
  if (!list) return "Belum ada hasil deteksi.";
  const top = list[0];
  let text;
  if (top.active) {
    text = "Warna dominan: " + top.name + ", keyakinan " + speakPercent(top.prob) + " persen.";
  } else {
    text = "Warna dominan kemungkinan " + top.name + ", keyakinan " + speakPercent(top.prob) + " persen, rendah.";
  }
  const others = list.slice(1).filter(item => item.prob >= 40).slice(0, 2);
  if (others.length) {
    text += " Terlihat juga " + others.map(item => item.name).join(" dan ") + ".";
  }
  return text;
}

function speakPercent(number) {
  return String(number).replace(".", " koma ");
}

els.tabs.forEach(btn => {
  btn.addEventListener("click", () => {
    welcome();
    switchTab(btn.dataset.tab);
  });
});

els.btnCameraStart.addEventListener("click", startCamera);
els.btnCameraStop.addEventListener("click", () => stopCamera(false));
els.btnCapture.addEventListener("click", capture);
els.btnSpeak.addEventListener("click", () => speak(buildResultSpeech()));
els.btnTheme.addEventListener("click", toggleTheme);
els.btnChange.addEventListener("click", openUploadPicker);

els.dropzone.addEventListener("click", openUploadPicker);
els.dropzone.addEventListener("keydown", e => {
  if (e.code === "Enter" || e.code === "Space") {
    e.preventDefault();
    openUploadPicker();
  }
});
els.dropzone.addEventListener("dragover", e => {
  e.preventDefault();
  els.dropzone.classList.add("drag");
});
els.dropzone.addEventListener("dragleave", () => els.dropzone.classList.remove("drag"));
els.dropzone.addEventListener("drop", e => {
  e.preventDefault();
  els.dropzone.classList.remove("drag");
  handleFile(e.dataTransfer.files[0]);
});

els.fileInput.addEventListener("change", e => {
  handleFile(e.target.files[0]);
  e.target.value = "";
});

document.querySelectorAll('input[name="mode"]').forEach(radio => {
  radio.addEventListener("change", () => {
    state.mode = radio.value;
    render();
  });
});

setInterval(() => {
  if (state.tab === "camera" && state.cameraActive && els.autoToggle.checked && !state.busy) {
    capture();
  }
}, 3000);

document.addEventListener("keydown", event => {
  if (event.repeat || event.ctrlKey || event.altKey || event.metaKey) return;
  const tag = event.target.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA") return;
  if (event.code === "Space" && state.tab === "camera" && state.cameraActive) {
    event.preventDefault();
    welcome();
    capture();
  } else if (event.code === "KeyT") {
    event.preventDefault();
    speak(buildResultSpeech());
  } else if (event.code === "KeyU") {
    event.preventDefault();
    welcome();
    switchTab("upload");
    openUploadPicker();
  } else if (event.code === "KeyK") {
    event.preventDefault();
    welcome();
    switchTab("camera");
    startCamera();
  } else if (event.code === "KeyD") {
    event.preventDefault();
    toggleTheme();
  }
});

if ("speechSynthesis" in window) {
  window.speechSynthesis.onvoiceschanged = () => {};
}
