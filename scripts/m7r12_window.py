"""Check tangential radiation from the archived nominal M2 single layer."""
import argparse
import json
from pathlib import Path

import numpy as np
from numpy.polynomial.legendre import legvander
from scipy.special import spherical_jn

from scripts import m7r12_quadrature as q
from scripts import m7r11_wave as r11


def grazing(path, order, edge):
    mirror = q.MIRRORS[1]
    def get(key):
        return np.array(mirror[key]["value"])
    n = get("illuminated_normal")
    tangent = np.cross(r11.S,n)
    curvature = get("principal_curvature_ts_per_m")
    a = get("half_aperture_ts_m")[0]
    d = get("vertex_m") - np.array(q.MIRRORS[0]["vertex_m"]["value"])
    d /= np.linalg.norm(d)
    if order > 0:
        nodes, ordinary = np.polynomial.legendre.leggauss(order)
        ends = np.linspace(-a,a,q.PANELS+1)
        ends = np.r_[np.linspace(*ends[:2],edge+1)[:-1],ends[1:-1],
                     np.linspace(*ends[-2:],edge+1)[1:]]
    else:
        count = -order
        order = 8
        ends = np.linspace(-a,a,count//order+1)
        nodes = (np.arange(order)+0.5)*2/order-1
        ordinary = np.full(order,2/order)
    with np.load(path) as field:
        u, v = field["u_m"],field["v_positive_m"]
        amp = -field["dE_dn"]*field["area_m2"]/np.pi  # -2/(4pi), doubled by Y symmetry
    centers, scale = (ends[1:]+ends[:-1])/2, np.diff(ends)/2
    if not np.allclose(u,(centers[:,None]+scale[:,None]*nodes).ravel(),rtol=0,atol=1e-15):
        raise ValueError("Surface axis mismatch")
    z = (get("vertex_m")[2]+tangent[2]*u[:,None]
         +n[2]*(curvature[0]*u[:,None]**2+curvature[1]*v**2)/2)
    values = []
    degree = np.arange(order)
    for sign in (-1,1):
        direction = np.array([0.,0.,float(sign)])
        slope = r11.K*((direction-d) @ tangent + ((direction-d) @ n)*curvature[0]*centers)
        alpha = slope*scale
        moments = (2*(1j)**degree*spherical_jn(degree, abs(alpha[:,None]))*
                   np.where((alpha[:,None]<0)&(degree%2==1),-1,1))
        fitted = moments @ np.linalg.inv(legvander(nodes,order-1))
        correction = (fitted/ordinary*np.exp(-1j*alpha[:,None]*nodes)).ravel()
        far = np.sum(amp*np.exp(1j*r11.K*sign*z)*correction[:,None])
        values.append(dict(world_Z=sign,real=float(far.real),imag=float(far.imag),abs=float(abs(far))))
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    path = parser.parse_args().directory
    results = {}
    for m1,m2,edge in [(14,14,1),(-512,14,1),(14,14,2),(14,14,4),(-640,-640,1)]:
        tag = f"q{m1}-{m2}-edge{edge}"
        results[tag] = grazing(path/f"M2-{tag}.npz",m2,edge)
    (path/"grazing.json").write_text(json.dumps(results,indent=2)+"\n")


if __name__ == "__main__":
    main()
