"""Case-specific Kirchhoff physical-optics reference for the frozen R8 expansion."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import platform
import tempfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "references/m7r11"
PORTS = ROOT / "examples/m7r6_smf_glass_1310.json"
MIRRORS = ROOT / "references/m7r8/summary.json"
K = 2*np.pi / 1.31e-6
S = np.array([0., 1., 0.])


def rule(half, n, gauss=False, edge_bins=1):
    if gauss:
        nodes, weights = np.polynomial.legendre.leggauss(2)
        centers, widths = rule(half, n//2)
        return ((centers[:, None] + widths[:, None]*nodes/2).ravel(),
                (widths[:, None]*weights/2).ravel())
    step = 2*half/n
    centers = -half + (np.arange(n)+0.5)*step
    widths = np.full(n, step)
    if edge_bins > 1:
        offsets = ((np.arange(edge_bins)+0.5)/edge_bins-0.5)*step
        centers = np.r_[centers[0]+offsets, centers[1:-1], centers[-1]+offsets]
        edges = np.full(edge_bins, step/edge_bins)
        widths = np.r_[edges, widths[1:-1], edges]
    return centers, widths


def surface(origin, normal, axes, curvature, half, count, gauss=False, edge_bins=1):
    u, wu = rule(half[0], count, gauss, edge_bins)
    v, wv = rule(half[1], count, gauss, edge_bins)
    x,y = np.meshgrid(u,v,indexing="ij")
    du,dv = x*curvature[0], y*curvature[1]
    point = (origin + x[...,None]*axes[0] + y[...,None]*axes[1]
             + ((du*x+dv*y)/2)[...,None]*normal)
    oriented = normal-du[...,None]*axes[0]-dv[...,None]*axes[1]
    jacobian = np.linalg.norm(oriented,axis=-1)
    return (point.reshape(-1,3), (oriented/jacobian[...,None]).reshape(-1,3),
            (jacobian*np.outer(wu,wv)).ravel(), x.ravel(), y.ravel())


def plane(origin, half, count):
    return surface(origin, np.array([1.,0.,0.]), ([0.,0.,-1.],S),
                   (0,0), (half,half), count)


def propagate(kernel, src, dst, amplitude, launch=False):
    out = np.empty(len(dst[0]),complex)
    grad = np.empty_like(out)
    arrays = [src[0],src[1],np.asarray(amplitude*src[2],complex),dst[0],dst[1]]
    p,n,a,d,m = [np.ascontiguousarray(v) for v in arrays]
    args = [v.ctypes.data_as(ctypes.c_void_p) for v in (p,n,a,d,m,out,grad)]
    kernel(len(p),*args[:3],len(d),*args[3:5],ctypes.c_double(K),
           ctypes.c_bool(launch),*args[5:])
    return out,grad


def controls(kernel):
    waist, distance = 25e-6, 0.4e-3
    origin = np.zeros(3)
    launch = plane(origin,4.5*waist,100)
    def gaussian(u,v,z):
        scale = 1-2j*z/(K*waist**2)
        return np.exp(-1j*K*z-(u*u+v*v)/(waist**2*scale))/scale
    def error(actual, expected):
        return float(np.linalg.norm(actual-expected)/np.linalg.norm(expected))
    src = gaussian(*launch[3:],0)
    target = plane([distance,0,0],2*waist,12)
    field,_ = propagate(kernel,launch,target,src,True)
    free = error(field,gaussian(*target[3:],distance))
    # Flat mirror normal toward the source. Compare at the launch plane to 2z.
    mirror = plane([distance,0,0],4.5*waist,100)
    mirror = (mirror[0],-mirror[1],*mirror[2:])
    _,dn = propagate(kernel,launch,mirror,src,True)
    detector = plane(origin,2*waist,12)
    reflected,_ = propagate(kernel,mirror,detector,-2*dn)
    flat = error(reflected,-gaussian(*detector[3:],2*distance))
    # Gauss radial quadrature with analytic azimuthal integration on axis.
    z, radius = 0.6e-3,80e-6
    nodes, weights = np.polynomial.legendre.leggauss(48)
    rho = (nodes+1)*radius/2
    points = np.stack((0*rho,rho,0*rho),axis=1)
    disk = (points,np.tile([1.,0.,0.],(len(rho),1)),np.pi*radius*rho*weights)
    axial,_ = propagate(kernel,disk,plane([z,0,0],1e-6,1),np.ones(len(rho)),True)
    r = np.hypot(z,radius)
    aperture = float(abs(axial[0]-(np.exp(-1j*K*z)-z/r*np.exp(-1j*K*r))))
    results = dict(gaussian_relative_L2=free, flat_relative_L2=flat, disk_absolute=aperture)
    print(results,flush=True)
    if not (free<1e-3 and flat<1e-3 and aperture<1e-4):
        raise ValueError("Control gate failed")
    return results


def gaussian(port, plane_data):
    radius = np.array(port["mfd_ts_m"]["value"])/2
    powers = port["wavefront_curvature_ts_per_m"]["value"]
    t,s = plane_data[3:]
    return (np.sqrt(2/(np.pi*radius.prod())) * np.exp(-(t/radius[0])**2-(s/radius[1])**2
            -0.5j*K*(powers[0]*t*t+powers[1]*s*s)))


def mirror_surface(m, count, gauss, edge_bins):
    get = lambda key: np.asarray(m[key]["value"])
    n = get("illuminated_normal")
    return surface(get("vertex_m"),n,(np.cross(S,n),S),get("principal_curvature_ts_per_m"),
                   get("half_aperture_ts_m"),count,gauss,edge_bins)


def flux(e,dn,weights):
    return float(-np.sum(weights*np.imag(e.conj()*dn))/K)


def run(kernel, count, gauss, directory, edge_bins=1):
    ports = json.loads(PORTS.read_text())
    mirrors = json.loads(MIRRORS.read_text())["candidates"]["expansion"]["mirror_prescriptions"]
    launch = plane(ports["source"]["position_m"]["value"],24e-6,64)
    field = gaussian(ports["source"],launch)
    # Forward plane-wave flux of the prescribed Dirichlet launch field.
    pitch = 48e-6/64
    kt = np.fft.fftfreq(64,pitch)*2*np.pi
    kz_ratio = np.sqrt(np.maximum(0,1-(kt[:,None]**2+kt**2)/K**2))
    launch_flux = float(pitch**2*np.sum(abs(np.fft.fft2(field.reshape(64,64),norm="ortho"))**2*kz_ratio))
    src = launch
    accepted = []
    for i,m in enumerate(mirrors):
        patch = mirror_surface(m,count,gauss,edge_bins)
        e,dn = propagate(kernel,src,patch,field,launch=i==0)
        accepted.append(-flux(e,dn,patch[2]))
        field,src = -2*dn,patch
    rows = []
    for pitch_um, window_um in [(2,48),(1,48),(.5,48),(.5,24),(.5,12)]:
        size = round(2*window_um/pitch_um)
        dst = plane(ports["target"]["position_m"]["value"],window_um*1e-6,size)
        e,dn = propagate(kernel,src,dst,field)
        mode = gaussian(ports["target"],dst)
        eta = abs(np.vdot(mode,e))**2/(np.vdot(e,e).real*np.vdot(mode,mode).real)
        power = flux(e,dn,dst[2])
        rows.append(dict(pitch_um=pitch_um,half_window_um=window_um,eta_diagnostic=float(eta),
                         target_flux_over_launch=power/launch_flux,
                         residual_over_launch=(accepted[1]-power)/launch_flux))
        if pitch_um==.5 and window_um==48:
            suffix = f"-edge{edge_bins}" if edge_bins > 1 else ""
            np.savez_compressed(directory/f"target-{count}-{'gauss' if gauss else 'mid'}{suffix}.npz",
                                ts_m=dst[3].reshape(size,size)[:,0],E=e.reshape(size,size),
                                dE_dx=dn.reshape(size,size))
    return dict(surface_nodes=count,edge_subdivisions=edge_bins,edge_rule="gauss2" if gauss else "midpoint",
                launch_flux=launch_flux,M1_over_launch=accepted[0]/launch_flux,
                M2_over_M1=accepted[1]/accepted[0],target=rows)


def finish_summary(data, directory):
    """Record discrepancies before any engineering decision on the relay."""
    rows = data["runs"]
    fine = next(r for r in rows if r["surface_nodes"] == 324 and r["edge_subdivisions"] == 1)
    by_window = {v["half_window_um"]: v for v in fine["target"] if v["pitch_um"] == 0.5}
    by_pitch = {v["pitch_um"]: v for v in fine["target"] if v["half_window_um"] == 48}
    def eta(row):
        return row["target"][2]["eta_diagnostic"]
    mid216 = next(r for r in rows if r["surface_nodes"] == 216 and
                  r["edge_subdivisions"] == 1 and r["edge_rule"] == "midpoint")
    cross = rows[-1]
    data["diagnostics"] = {
        "target_pitch_last_delta": abs(by_pitch[1]["eta_diagnostic"] - eta(fine)),
        "target_window_last_delta": abs(by_window[24]["eta_diagnostic"] - eta(fine)),
        "surface_last_delta": abs(eta(mid216) - eta(fine)),
        "finest_edge_cross_delta": abs(eta(cross) - eta(fine)),
        "archived_field_sha256": hashlib.sha256(
            (directory / "target-324-mid.npz").read_bytes()).hexdigest(),
    }
    data["fixed_case_decision"] = {
        "numerical_U": None, "nominal_threshold": "Uncomputed",
        "qualified_aperture_throughput": None, "perturbed_overlap": None,
        "actual_total_coupling": None,
        "reason": "An independent converged curved-surface field and a supported uncertainty bound are required.",
    }
    data["runtime"] = {"python": sys.version.split()[0], "numpy": np.__version__,
                       "platform": platform.system(),
                       "compiler": subprocess.check_output(
                           ["g++", "--version"], text=True).splitlines()[0]}
    (directory / "summary.json").write_text(json.dumps(data,indent=2,allow_nan=False)+"\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    args = parser.parse_args()
    dst = args.directory
    dst.mkdir(parents=True,exist_ok=False)
    with tempfile.TemporaryDirectory() as tmp:
        lib = Path(tmp)/"layer.so"
        subprocess.run(["g++","-shared","-fPIC","-O3","-fopenmp",str(REFERENCE/"layer.cpp"),
                        "-o",str(lib)],check=True)
        kernel = ctypes.CDLL(str(lib)).layer
        kernel.restype = None
        data = dict(inputs={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in (PORTS,MIRRORS,ROOT/"references/m7r7/case.json")},
                    controls=controls(kernel),runs=[])
        for count, gauss, edge_bins in [(96,False,1),(144,False,1),(216,False,1),(216,True,1),
                                        (324,False,1),(216,False,2),(216,False,4),(324,False,4)]:
            row = run(kernel,count,gauss,dst,edge_bins)
            data["runs"].append(row)
            (dst/"summary.json").write_text(json.dumps(data,indent=2,allow_nan=False)+"\n")
            print(count,gauss,row["M2_over_M1"],row["target"][2],flush=True)
        finish_summary(data, dst)


if __name__=="__main__":
    main()
