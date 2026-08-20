const API = "/api/calibration";

const statusBar = document.getElementById("status-bar");
const cameraFrame = document.getElementById("camera-frame");
const overlay = document.getElementById("overlay");
const confirmBtn = document.getElementById("confirm-btn");
const discardBtn = document.getElementById("discard-btn");
const recalibrateBtn = document.getElementById("recalibrate-btn");

const CORNER_LABELS = {
  a1: "a1 (coin bas-gauche)",
  h1: "h1 (coin bas-droit)",
  a8: "a8 (coin haut-gauche)",
  h8: "h8 (coin haut-droit)",
};

let draft = { nextCorner: null, previewGrid: null };

async function callApi(path, options) {
  let response;
  try {
    response = await fetch(API + path, options);
  } catch (err) {
    showWarning("Impossible de contacter le serveur de calibration.");
    throw err;
  }
  if (response.status === 503) {
    showWarning("Flux caméra indisponible — vérifiez la connexion à la caméra.");
  }
  return response;
}

function showWarning(message) {
  statusBar.textContent = message;
  statusBar.classList.add("warning");
}

function showInfo(message) {
  statusBar.textContent = message;
  statusBar.classList.remove("warning");
}

async function init() {
  const response = await callApi("/status");
  const data = await response.json();
  if (data.status === "confirmed") {
    showReadyView(data);
  } else {
    beginCalibration();
  }
}

function showReadyView(status) {
  showInfo(`Calibration active (confirmée le ${status.created_at}). Prêt à jouer.`);
  confirmBtn.hidden = true;
  discardBtn.hidden = true;
  recalibrateBtn.hidden = false;
  clearOverlay();
}

async function beginCalibration() {
  const response = await callApi("/start", { method: "POST" });
  const data = await response.json();
  draft = { nextCorner: data.next_corner, previewGrid: null };
  confirmBtn.hidden = true;
  discardBtn.hidden = false;
  recalibrateBtn.hidden = true;
  clearOverlay();
  updatePrompt();
}

function updatePrompt() {
  if (draft.nextCorner) {
    showInfo(`Cliquez sur le coin ${CORNER_LABELS[draft.nextCorner]}.`);
  } else {
    showInfo("Vérifiez la grille superposée, puis confirmez ou recommencez.");
  }
}

cameraFrame.addEventListener("click", async (event) => {
  if (discardBtn.hidden) {
    return; // pas de séquence de calibration en cours
  }
  const rect = cameraFrame.getBoundingClientRect();
  const x = ((event.clientX - rect.left) / rect.width) * cameraFrame.naturalWidth;
  const y = ((event.clientY - rect.top) / rect.height) * cameraFrame.naturalHeight;

  const response = await callApi("/point", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ x, y }),
  });

  if (response.status === 422) {
    const error = await response.json();
    showWarning(error.detail.message + " Recliquez sur le même coin.");
    return;
  }
  if (response.status !== 200) {
    return;
  }

  const data = await response.json();
  draft.nextCorner = data.next_corner;
  if (data.preview_grid) {
    draft.previewGrid = data.preview_grid;
    drawOverlay(data.preview_grid);
    confirmBtn.hidden = false;
  }
  updatePrompt();
});

confirmBtn.addEventListener("click", async () => {
  const response = await callApi("/confirm", { method: "POST" });
  if (response.status === 409) {
    showWarning("4 points requis avant de confirmer.");
    return;
  }
  const data = await response.json();
  showReadyView(data);
});

discardBtn.addEventListener("click", async () => {
  const response = await callApi("/discard", { method: "POST" });
  const data = await response.json();
  if (data.status === "confirmed") {
    showReadyView(data);
  } else {
    beginCalibration();
  }
});

recalibrateBtn.addEventListener("click", beginCalibration);

function clearOverlay() {
  const ctx = overlay.getContext("2d");
  ctx.clearRect(0, 0, overlay.width, overlay.height);
}

function drawOverlay(squares) {
  overlay.width = cameraFrame.clientWidth;
  overlay.height = cameraFrame.clientHeight;
  const scaleX = overlay.width / cameraFrame.naturalWidth;
  const scaleY = overlay.height / cameraFrame.naturalHeight;
  const ctx = overlay.getContext("2d");
  clearOverlay();
  ctx.strokeStyle = "#00ff88";
  ctx.lineWidth = 1;
  for (const square of squares) {
    const points = square.image_region;
    ctx.beginPath();
    points.forEach(([x, y], i) => {
      const px = x * scaleX;
      const py = y * scaleY;
      i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
    });
    ctx.closePath();
    ctx.stroke();
  }
}

init();
