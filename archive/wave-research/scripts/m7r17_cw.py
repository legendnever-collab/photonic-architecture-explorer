"""Monochromatic finite-plate PO versus the local monochromatic straight-edge limit."""

import ctypes
import json
from pathlib import Path
import subprocess
import tempfile

import numpy as np
from scripts.m7r17_edge import WIDTH, LENGTH, SIN, PROBES, sommerfeld, comparisons
from scripts.m7r17_source import REF


def canonical(pol):
    k = 2 * np.pi
    h = 5e-5
    fields = []
    for x, _, z in PROBES:

        def f(a, b):
            return sommerfeld(a, b, k, -1 if pol == "TE" else 1)

        u = f(x, z)
        dx = (f(x + h, z) - f(x - h, z)) / (2 * h)
        dz = (f(x, z + h) - f(x, z - h)) / (2 * h)
        axial = np.array([0, u, 0])
        transverse = np.array([-1j * dz / k, 0, 1j * dx / k])
        fields.append(
            np.r_[axial, transverse] if pol == "TE" else np.r_[-transverse, axial]
        )
    return np.array(fields)


def run():
    rows = {}
    previous = {}
    with tempfile.TemporaryDirectory() as tmp:
        so = Path(tmp) / "plate.so"
        subprocess.run(
            [
                "g++",
                "-O3",
                "-shared",
                "-fopenmp",
                "-fPIC",
                str(REF / "plate.cpp"),
                "-o",
                str(so),
            ],
            check=True,
        )
        kernel = ctypes.CDLL(str(so)).plate
        kernel.argtypes = [ctypes.c_int] + [ctypes.c_double] * 5 + [ctypes.c_void_p]
        kernel.restype = None
        for density in (2, 4, 8, 16):
            te, tm = [], []
            for x, _, z in PROBES:
                out = np.empty(6, complex)
                kernel(density, WIDTH, LENGTH, SIN, x, z, out.ctypes.data)
                ey, hx, hz, ex, ez, hy = out
                te.append([0, ey, 0, hx, 0, hz])
                tm.append([ex, 0, ez, 0, hy, 0])
            rows[density] = {}
            for pol, field in [("TE", np.array(te)), ("TM", np.array(tm))]:
                ref = canonical(pol)
                row = comparisons(field, ref)
                if pol in previous:
                    row["mesh_change"] = comparisons(field, previous[pol])
                if density == 16:
                    for label, value in [("field", field), ("local_ref", ref)]:
                        row[label] = {
                            "real": value.real.tolist(),
                            "imag": value.imag.tolist(),
                        }
                previous[pol] = field
                rows[density][pol] = row
    return rows


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, allow_nan=False))
