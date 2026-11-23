"""Frozen nominal R12 tensor quadrature and common-coordinate field comparisons."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

import numpy as np
from numpy.polynomial.legendre import leggauss

from scripts import m7r11_wave as r11

REF = r11.ROOT / "references/m7r12"
PANELS = 48
FROZEN = json.loads((r11.REFERENCE / "summary.json").read_text())
PORTS = json.loads(r11.PORTS.read_text())
MIRRORS = json.loads(r11.MIRRORS.read_text())["candidates"]["expansion"]["mirror_prescriptions"]
ptr = ctypes.c_void_p


def kernels(folder):
    functions = []
    for source, symbol, flags in [(r11.REFERENCE / "layer.cpp", "layer", []),
                                  (REF / "single_layer.cpp", "reflected",
                                   ["-march=native", "-ffast-math"])]:
        lib = folder / (symbol + ".so")
        subprocess.run(["g++", "-shared", "-fPIC", "-O3", "-fopenmp", *flags,
                        str(source), "-o", str(lib)], check=True)
        fn = getattr(ctypes.CDLL(str(lib)), symbol)
        fn.restype = None
        functions.append(fn)
    return functions


def check_inputs():
    for name, digest in FROZEN["inputs"].items():
        if hashlib.sha256((r11.ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Frozen input mismatch: {name}")


def axis(half, order, edge):
    ends = np.linspace(-half, half, PANELS + 1)
    ends = np.r_[np.linspace(*ends[:2], edge+1)[:-1], ends[1:-1],
                 np.linspace(*ends[-2:], edge+1)[1:]]
    nodes, weights = leggauss(order)
    widths = np.diff(ends)[:, None]
    return ((ends[:-1, None] + (nodes+1)*widths/2).ravel(),
            (weights*widths/2).ravel())


def patch(mirror, order, edge):
    normal, origin, curv, half = [np.array(mirror[name]["value"]) for name in
        ("illuminated_normal", "vertex_m", "principal_curvature_ts_per_m", "half_aperture_ts_m")]
    tangent = np.cross(r11.S, normal)
    u, wu = axis(half[0], order, edge)
    v, wv = axis(half[1], order, edge)
    x, y = np.meshgrid(u, v, indexing="ij")
    sag = (curv[0]*x*x + curv[1]*y*y)/2
    xyz = origin + x[..., None]*tangent + y[..., None]*r11.S + sag[..., None]*normal
    area_normal = normal - (curv[0]*x[..., None])*tangent - (curv[1]*y[..., None])*r11.S
    jac = np.linalg.norm(area_normal, axis=-1)
    return (xyz.reshape(-1, 3), (area_normal/jac[..., None]).reshape(-1, 3),
            (jac*np.outer(wu, wv)).ravel(), x.ravel(), y.ravel())


def layer(fn, src, dst, density):
    weighted = density * (src[2]/(4*np.pi))
    arrays = [np.ascontiguousarray(src[0].T),
              np.ascontiguousarray([weighted.real, weighted.imag]),
              np.ascontiguousarray(dst[0]), np.ascontiguousarray(dst[1])]
    result = np.empty((len(dst[0]), 2), dtype=np.complex128)
    p, a, d, n = [v.ctypes.data_as(ptr) for v in arrays]
    fn(len(weighted), p, a, len(result), d, n, ctypes.c_double(r11.K), result.ctypes.data_as(ptr))
    return result.T


def even_evaluate(evaluate, dst):
    # Centered nominal source and both axes-aligned patches are symmetric in world Y.
    n = round(np.sqrt(len(dst[0])))
    pos = dst[4] > 0
    if n*n != len(pos) or pos.sum()*2 != len(pos):
        raise ValueError("Expected even tensor grid centered on y=0")
    e, dn = evaluate(tuple(a[pos] for a in dst))
    def both(a):
        positive = a.reshape(n, n//2)
        return np.column_stack((positive[:, ::-1], positive)).ravel()
    return both(e), both(dn)


def relative(a, b):
    return float(np.linalg.norm(a-b) / np.linalg.norm(b))


def replay(direct, out):
    controls = r11.controls(direct)
    return compare_replay(controls, r11.run(direct, 324, False, out), out)


def compare_replay(controls, row, out):
    original = next(r for r in FROZEN["runs"] if r["surface_nodes"] == 324
                    and r["edge_subdivisions"] == 1)
    with np.load(out/"target-324-mid.npz") as new, np.load(r11.REFERENCE/"nominal-target.npz") as old:
        errors = {k: relative(new[k], old[k]) for k in old.files}
    diffs = [abs(row[k]-original[k])/abs(original[k]) for k in ("launch_flux","M1_over_launch","M2_over_M1")]
    diffs.extend(abs(a[k]-b[k])/abs(b[k]) for a,b in zip(row["target"],original["target"])
                 for k in ("eta_diagnostic","target_flux_over_launch","residual_over_launch"))
    if max(max(errors.values()), max(diffs)) > 1e-10:
        raise ValueError("R11 nominal replay failed")
    return dict(controls=controls, field_relative=errors, max_ledger_relative=max(diffs), row=row)


def metric(dst, e, dn, launch_flux, m2_power):
    mode = r11.gaussian(PORTS["target"], dst)
    power = r11.flux(e, dn, dst[2])
    return dict(eta=float(abs(np.vdot(mode, e))**2/(np.vdot(mode,mode).real*np.vdot(e,e).real)),
                target_over_launch=power/launch_flux, residual_over_launch=(m2_power-power)/launch_flux)


def probe_grid():
    # Common interior, edge and corner coordinates; positive and negative sagittal positions.
    m = r11.mirror_surface(MIRRORS[1], 17, False, 1)
    return tuple(a.reshape((17,17)+a.shape[1:])[::2,::2].reshape((-1,)+a.shape[1:]) for a in m)


def run(direct, reflected, out, orders, edge, wide):
    # Negative order denotes an independent uniform midpoint rule of that size.
    first, second = [patch(m, order, edge) if order > 0 else
                     r11.mirror_surface(m, -order, False, 1)
                     for m, order in zip(MIRRORS, orders)]
    launch = r11.plane(PORTS["source"]["position_m"]["value"], 24e-6, 64)
    field = r11.gaussian(PORTS["source"], launch)
    launch_flux = FROZEN["runs"][0]["launch_flux"]
    e1, dn1 = even_evaluate(lambda dst: r11.propagate(direct, launch, dst, field, True), first)
    density = -2*dn1
    probes = probe_grid()
    probe_e, probe_dn = layer(reflected, first, probes, density)
    control_e, control_dn = r11.propagate(direct, first, probes, density)
    errors = [relative(probe_e, control_e), relative(probe_dn, control_dn)]
    if max(errors) > 1e-10:
        raise ValueError("Independent single-layer kernel mismatch")
    e2, dn2 = even_evaluate(lambda dst: layer(reflected, first, dst, density), second)
    m1_power, m2_power = [-r11.flux(e, dn, geom[2]) for e,dn,geom in ((e1,dn1,first),(e2,dn2,second))]
    row = dict(orders=orders, edge=edge, M1_over_launch=m1_power/launch_flux,
               M2_over_M1=m2_power/m1_power, common_kernel_relative=errors, target=[])
    tag = f"q{orders[0]}-{orders[1]}-edge{edge}"
    np.savez_compressed(out/f"probes-{tag}.npz", xyz_m=probes[0], normals=probes[1],
                        E=probe_e, dE_dn=probe_dn)
    size = round(np.sqrt(len(e2)))
    positive = np.s_[:,size//2:]
    np.savez_compressed(out/f"M2-{tag}.npz", u_m=second[3].reshape(size,size)[:,0],
                        v_positive_m=second[4].reshape(size,size)[0,size//2:],
                        area_m2=second[2].reshape(size,size)[positive],
                        E=e2.reshape(size,size)[positive], dE_dn=dn2.reshape(size,size)[positive])
    # For a fixed pitch, crop the same field at smaller exact cell boundaries.
    for pitch, half in ([(1.,48)] if not wide else [(2.,192),(1.,96),(.5,48)]):
        n = round(2*half/pitch)
        target = r11.plane(PORTS["target"]["position_m"]["value"],half*1e-6,n)
        e, dn = even_evaluate(lambda dst: layer(reflected, second, dst, -2*dn2), target)
        for window in (24,48,96,192):
            if window > half:
                break
            keep = (abs(target[3]) < window*1e-6) & (abs(target[4]) < window*1e-6)
            values = metric(tuple(a[keep] for a in target), e[keep],dn[keep],launch_flux,m2_power)
            row["target"].append(dict(pitch_um=pitch, half_window_um=window, **values))
        np.savez_compressed(out/f"target-{tag}-{pitch:g}um.npz", ts_m=target[3].reshape(n,n)[:,0],
                            E=e.reshape(n,n), dE_dx=dn.reshape(n,n))
    (out/f"{tag}.json").write_text(json.dumps(row,indent=2,allow_nan=False)+"\n")
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    parser.add_argument("--replay",action="store_true")
    parser.add_argument("--orders",type=int,nargs=2,default=(6,6))
    parser.add_argument("--edge",type=int,default=1)
    parser.add_argument("--wide",action="store_true")
    args = parser.parse_args()
    check_inputs()
    args.directory.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        direct,reflected = kernels(Path(tmp))
        if args.replay:
            data = replay(direct,args.directory)
            (args.directory/"replay.json").write_text(json.dumps(data,indent=2)+"\n")
        else:
            data = run(direct,reflected,args.directory,args.orders,args.edge,args.wide)
        print(json.dumps(data),flush=True)


if __name__ == "__main__":
    main()
