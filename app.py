import base64
import io
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from flask import Flask, jsonify, render_template, request
from torchvision import transforms
from torchvision.models import mobilenet_v2

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"

ALL_LABELS = [
    "black", "blue", "brown", "gold", "green", "grey",
    "orange", "pink", "purple", "red", "silver", "white", "yellow"
]
NUM_CLASSES = len(ALL_LABELS)

BASIC_GROUPS = {
    "merah": ["red", "orange", "pink"],
    "biru": ["blue", "purple"],
    "hijau": ["green"],
    "kuning": ["yellow", "gold"],
    "putih": ["white", "silver"],
    "hitam": ["black", "grey"],
    "coklat": ["brown"],
}
BASIC_LABELS = list(BASIC_GROUPS.keys())

IDN = {
    "black": "hitam", "blue": "biru", "brown": "coklat", "gold": "emas",
    "green": "hijau", "grey": "abu-abu", "orange": "oranye", "pink": "pink",
    "purple": "ungu", "red": "merah", "silver": "perak", "white": "putih",
    "yellow": "kuning",
}
HEX = {
    "black": "#212121", "blue": "#1E88E5", "brown": "#6D4C41", "gold": "#DAA520",
    "green": "#43A047", "grey": "#9E9E9E", "orange": "#FB8C00", "pink": "#EC407A",
    "purple": "#8E24AA", "red": "#E53935", "silver": "#C0C0C0", "white": "#FFFFFF",
    "yellow": "#FDD835",
}

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

MODEL = mobilenet_v2(weights=None)
IN_FEATURES = MODEL.classifier[1].in_features
MODEL.classifier = nn.Sequential(
    nn.Dropout(p=0.3),
    nn.Linear(IN_FEATURES, 512),
    nn.ReLU(),
    nn.BatchNorm1d(512),
    nn.Dropout(p=0.2),
    nn.Linear(512, NUM_CLASSES),
)
CKPT = torch.load(MODELS_DIR / "best_model.pth", map_location="cpu", weights_only=False)
MODEL.load_state_dict(CKPT["model_state_dict"])
MODEL = MODEL.to(DEVICE).eval()

THRESHOLDS_DETAIL = np.array(CKPT["thresholds"], dtype=float)
THRESHOLDS_BASIC = np.array(CKPT.get("thresholds_basic", [0.5] * len(BASIC_LABELS)), dtype=float)

TRANSFORM = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


def read_image():
    if request.is_json:
        data = request.get_json(force=True, silent=True) or {}
        raw = data.get("image", "")
        if not raw:
            return None
        if raw.startswith("data:"):
            raw = raw.split(",", 1)[1]
        try:
            buf = base64.b64decode(raw)
        except Exception:
            return None
    else:
        f = request.files.get("image")
        if f is None:
            return None
        buf = f.read()
    try:
        return Image.open(io.BytesIO(buf)).convert("RGB")
    except Exception:
        return None


def build_entries(labels, probs, thresholds):
    entries = []
    for label, prob, thr in zip(labels, probs, thresholds):
        entries.append({
            "label": label,
            "name": IDN.get(label, label),
            "hex": HEX.get(label, "#9E9E9E"),
            "prob": round(float(prob) * 100, 1),
            "active": bool(float(prob) >= float(thr)),
        })
    entries.sort(key=lambda e: e["prob"], reverse=True)
    return entries


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "device": str(DEVICE)})


@app.route("/predict", methods=["POST"])
def predict():
    image = read_image()
    if image is None:
        return jsonify({"error": "Gambar tidak valid atau kosong."}), 400

    x = TRANSFORM(image).unsqueeze(0).to(DEVICE)
    t0 = time.time()
    with torch.no_grad():
        logits = MODEL(x)
    elapsed_ms = (time.time() - t0) * 1000
    probs_detail = torch.sigmoid(logits)[0].cpu().numpy()

    probs_basic = []
    idx_of = {label: i for i, label in enumerate(ALL_LABELS)}
    for members in BASIC_GROUPS.values():
        probs_basic.append(float(max(probs_detail[idx_of[m]] for m in members)))
    probs_basic = np.array(probs_basic)

    return jsonify({
        "detail": build_entries(ALL_LABELS, probs_detail, THRESHOLDS_DETAIL),
        "basic": build_entries(BASIC_LABELS, probs_basic, THRESHOLDS_BASIC),
        "time_ms": round(elapsed_ms, 1),
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8001, debug=False)
