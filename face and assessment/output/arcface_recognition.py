"""
High-accuracy face recognition using InsightFace (ArcFace embeddings).
Exposes a compatible API: face_locations(), face_encodings(), compare_faces()
so it can drop-in replace the previous simple_face_detection backend.
"""
import threading
from typing import List, Tuple

import cv2
import numpy as np

try:
    from insightface.app import FaceAnalysis
except ImportError as e:
    raise RuntimeError(
        "insightface not installed. Run: pip install insightface onnxruntime"
    ) from e

from config import Config

# Singleton FaceAnalysis app, CPU mode for compatibility
_APP = None
_APP_LOCK = threading.Lock()


def _get_app() -> FaceAnalysis:
    global _APP
    if _APP is None:
        with _APP_LOCK:
            if _APP is None:
                app = FaceAnalysis(name='buffalo_l')  # robust pipeline (detector + recognizer)
                # ctx_id=-1 -> CPU. det_size can be larger for HD frames
                app.prepare(ctx_id=-1, det_size=(640, 640))
                _APP = app
    return _APP


def face_locations(frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """Return face bounding boxes as (top, right, bottom, left)."""
    app = _get_app()
    # InsightFace expects BGR np.ndarray as provided by OpenCV
    faces = app.get(frame)
    boxes: List[Tuple[int, int, int, int]] = []
    for f in faces:
        x1, y1, x2, y2 = f.bbox.astype(int)
        top, right, bottom, left = y1, x2, y2, x1
        boxes.append((top, right, bottom, left))
    return boxes


def face_encodings(frame: np.ndarray, boxes: List[Tuple[int, int, int, int]]) -> List[np.ndarray]:
    """Return 512-d ArcFace embeddings for faces in frame.
    boxes parameter is ignored (detector is run internally) for best alignment.
    """
    app = _get_app()
    faces = app.get(frame)
    encs: List[np.ndarray] = []
    for f in faces:
        if f.normed_embedding is None:
            # If not precomputed, compute via .embedding (auto-normalizes)
            emb = f.embedding
            # Normalize to unit length
            emb = emb / (np.linalg.norm(emb) + 1e-12)
        else:
            emb = f.normed_embedding
        encs.append(emb.astype(np.float32))
    return encs


def compare_faces(known_encodings: List[np.ndarray], face_encoding: np.ndarray, tolerance: float = None) -> List[bool]:
    """Compare with cosine similarity. Higher is more similar.
    Returns list of booleans for each known encoding.
    """
    if not known_encodings or face_encoding is None:
        return []

    # Ensure normalized
    ke = np.stack(known_encodings, axis=0).astype(np.float32)
    ke = ke / (np.linalg.norm(ke, axis=1, keepdims=True) + 1e-12)
    fe = face_encoding.astype(np.float32)
    fe = fe / (np.linalg.norm(fe) + 1e-12)

    # Cosine similarity
    sims = (ke @ fe)

    # Use ArcFace-specific similarity threshold
    thr = Config.ARC_FACE_SIM_THRESHOLD if tolerance is None else tolerance
    matches = sims >= thr
    return matches.tolist()


def face_distance(known_encodings: List[np.ndarray], face_encoding: np.ndarray) -> List[float]:
    """Return 1 - cosine similarity as a distance-like metric (lower is better)."""
    if not known_encodings or face_encoding is None:
        return []
    ke = np.stack(known_encodings, axis=0).astype(np.float32)
    ke = ke / (np.linalg.norm(ke, axis=1, keepdims=True) + 1e-12)
    fe = face_encoding.astype(np.float32)
    fe = fe / (np.linalg.norm(fe) + 1e-12)
    sims = (ke @ fe)
    dists = 1.0 - sims
    return dists.tolist()
