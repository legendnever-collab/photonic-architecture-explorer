"""Replay the R12 square-window diagnostics using the frozen reciprocal port."""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.special import log_ndtr

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "references/m7r12"
PORT = "examples/m7r6_smf_glass_1310.json"


def verify_hash(path, expected):
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError(f"Frozen input differs: {path.name}")


def review():
    archive = json.loads((ARCHIVE / "summary.json").read_text())
    verify_hash(ROOT / PORT, archive["inputs"][PORT])
    params = json.loads((ROOT / PORT).read_text())
    wavelength = params["wavelength_m"]["value"]
    port = params["target"]
    widths = np.array(port["mfd_ts_m"]["value"]) / 2
    curvature = port["wavefront_curvature_ts_per_m"]["value"]
    rows = []
    for filename in sorted(archive["sha256"]):
        if not filename.startswith("target-q14-14-edge1-"):
            continue
        path = ARCHIVE / filename
        verify_hash(path, archive["sha256"][filename])
        with np.load(path) as raw:
            axis, field = raw["ts_m"], raw["E"]
        pitch = axis[1] - axis[0]
        half_window = len(axis) * pitch / 2
        factors = [
            np.exp(-axis**2 * (1 / w**2 + 1j * np.pi * c / wavelength))
            for w, c in zip(widths, curvature, strict=True)
        ]
        mode = np.outer(*factors)
        projection = np.sum(mode.conj() * field)
        eta = abs(projection)**2 / (np.sum(abs(mode)**2) * np.sum(abs(field)**2))
        expected, = (r for r in archive["runs"]["q14-14-edge1"]["target"]
                     if np.isclose(r["half_window_um"], half_window * 1e6)
                     and np.isclose(r["pitch_um"], pitch * 1e6))
        if not np.isclose(eta, expected["eta"], rtol=0, atol=1e-12):
            raise ValueError(f"R12 projection mismatch: {filename}")
        # Union bound for the normalized fitted target's intensity outside the square.
        # log(erfc(sqrt(2)*L/w)) = log(2) + log(Phi(-2*L/w)).
        axis_logs = np.log(2) + log_ndtr(-2 * half_window / widths)
        rows.append(dict(file=filename, half_window_um=round(half_window * 1e6),
                         eta_window=float(eta),
                         target_tail_log10_upper=float(np.logaddexp(*axis_logs) / np.log(10))))
    if len(rows) != 2:
        raise ValueError("Expected both frozen R12 target windows")
    return rows


if __name__ == "__main__":
    print(json.dumps(review(), indent=2, allow_nan=False))
