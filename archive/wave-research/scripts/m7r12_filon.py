"""Linear-phase Filon cross-check of the frozen M1 single layer at M2."""
import argparse
import json
from pathlib import Path
import tempfile

import numpy as np
from numpy.polynomial.legendre import leggauss, legvander
from scipy.special import spherical_jn

from scripts import m7r12_quadrature as q
from scripts import m7r11_wave as r11


def fitted_weights(order, alpha):
    """Nodal integrals of Lagrange cardinals times exp(-i alpha x) on [-1,1]."""
    x, w = leggauss(order)
    degree = np.arange(order)
    moments = spherical_jn(degree, abs(alpha[..., None]))
    parity = np.where((alpha[...,None] < 0) & (degree % 2 == 1), -1, 1)
    coeff = moments * parity * ((2*degree+1)*(-1j)**degree)
    return (coeff @ legvander(x, order-1).T)*w


def control():
    # Independent analytic Fourier transform of a constant plus linear ramp.
    alpha = np.array([-51.3, -0.02, 0., 0.02, 51.3])
    x = leggauss(6)[0]
    val = fitted_weights(6,alpha) @ (1+0.4*x)
    exact = 2*np.sinc(alpha/np.pi).astype(complex)
    nz = alpha != 0
    a = alpha[nz]
    exact[nz] += .8j*(a*np.cos(a)-np.sin(a))/a**2
    err = float(max(abs(val-exact)))
    if err > 1e-12:
        raise ValueError("Fourier moment control failed")
    return err


def filon(direct, order, probes):
    m = q.MIRRORS[0]
    n, c, half = [np.array(m[key]["value"]) for key in
                  ("illuminated_normal","principal_curvature_ts_per_m","half_aperture_ts_m")]
    panels = q.PANELS
    p = q.patch(m, order, 1)
    src_pos = q.PORTS["source"]["position_m"]["value"]
    launch = r11.plane(src_pos,24e-6,64)
    field = r11.gaussian(q.PORTS["source"],launch)
    _, dn = q.even_evaluate(lambda d: r11.propagate(direct, launch,d,field,True),p)
    # p[2] includes the ordinary GL weights. Replace them with phase-fitted weights.
    nodes, w = leggauss(order)
    scale = half / panels
    local_jac_area = p[2].reshape(panels,order,panels,order)/(w[None,:,None,None]*w)
    amp = (-dn/(2*np.pi)).reshape(local_jac_area.shape)*local_jac_area
    centers = r11.mirror_surface(m,panels,False,1)
    xyz = centers[0].reshape(panels,panels,3)
    incident = xyz - src_pos
    incident /= np.linalg.norm(incident,axis=-1)[...,None]
    tangents = [base + curvature*uv.reshape(panels,panels,1)*n for base,curvature,uv
                in zip((np.cross(r11.S,n),r11.S), c, centers[3:])]
    results = []
    phase_steps = []
    for dst, normal in zip(*probes[:2]):
        arrival = dst-xyz
        arrival /= np.linalg.norm(arrival,axis=-1)[...,None]
        alpha,beta = [r11.K*s*np.sum((incident-arrival)*t,axis=-1)
                      for t,s in zip(tangents,scale)]
        # Remove the local linear part from the sampled integrand. Integrate that
        # same phase exactly against each polynomial cardinal in the two axes.
        wu = fitted_weights(order,alpha)*np.exp(1j*alpha[...,None]*nodes)
        wv = fitted_weights(order,beta)*np.exp(1j*beta[...,None]*nodes)
        delta = dst-p[0]
        r = np.linalg.norm(delta,axis=-1)
        wave = (np.exp(-1j*r11.K*r)/r).reshape(amp.shape)*amp
        value = wave*wu.transpose(0,2,1)[:,:,:,None]*wv[:,None,:,:]
        derivative = -(1/r+1j*r11.K)*(delta@normal)/r
        results.append([value.sum(),np.sum(value*derivative.reshape(amp.shape))])
        # Twice the half-panel slope divided by 324/48 midpoint cells per panel.
        phase_steps.append(2*panels/324*np.array([abs(alpha).max(),abs(beta).max()]))
    return np.array(results).T, np.array(phase_steps)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    args = parser.parse_args()
    q.check_inputs()
    args.directory.mkdir(exist_ok=True,parents=True)
    probes = q.probe_grid()
    data = dict(moment_control=control(),runs=[])
    with tempfile.TemporaryDirectory() as tmp:
        direct,_ = q.kernels(Path(tmp))
        for order in (3,4,6,8,10,12):
            (e,dn),steps = filon(direct,order,probes)
            np.savez_compressed(args.directory/f"filon-{order}.npz",xyz_m=probes[0],
                                normals=probes[1], E=e, dE_dn=dn)
            data["runs"].append(dict(order=order, max_phase_step_324_rad=steps.max(axis=0).tolist()))
        # Re-evaluate the published midpoint source integral at identical receivers.
        launch = r11.plane(q.PORTS["source"]["position_m"]["value"],24e-6,64)
        m1 = r11.mirror_surface(q.MIRRORS[0],324,False,1)
        f = r11.gaussian(q.PORTS["source"],launch)
        _,d1 = q.even_evaluate(lambda d:r11.propagate(direct,launch,d,f,True),m1)
        e,dn = r11.propagate(direct,m1,probes,-2*d1)
        np.savez_compressed(args.directory/"midpoint-324-probes.npz",xyz_m=probes[0],
                            normals=probes[1],E=e,dE_dn=dn)
    (args.directory/"filon.json").write_text(json.dumps(data,indent=2)+"\n")


if __name__ == "__main__":
    main()
