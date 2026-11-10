"""Fixed 2D TE planar Control; external tmm kernel, never a production solver.

Run after reading docs/M4C_REFERENCE_PLAN.md. No actual guided mode or Target.
Convention: exp(+i omega t), exp(-i k.r); field arrays contain Ey, Z0 Hx, Z0 Hz.
"""
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import resource
import subprocess
import time

import numpy as np
from scipy.integrate import quad
import tmm

ROOT = Path(__file__).resolve().parents[1]
WAVELENGTH = 1.310e-6
W = 1.365e-6
N1, N2 = 1.5, 1.0
L = 80e-6
K0 = 2 * np.pi / WAVELENGTH
Z0 = 376.730313668  # ohms; normalization convention, cancels from ratios
CUT = 0.95 * N1
Z_PLANES = (0.0, 5e-6)


def library_coefficients(u):
    """u=kx/k0, propagating incidence; tmm chooses outgoing transmitted branch."""
    ai = np.arcsin(abs(u) / N1)
    at = tmm.snell(N1, N2, ai)
    return (np.conj(tmm.interface_r('s', N1, N2, ai, at)),
            np.conj(tmm.interface_t('s', N1, N2, ai, at)),
            np.conj(N2 * np.cos(at)))


def synth(a):
    # A(k)=integral E(x) exp(+ikx) dx; E(x)=integral A exp(-ikx) dk/(2pi).
    return np.fft.fftshift(np.fft.fft(a)) / L


def flux(fields, dx):
    return float(-np.sum(np.real(fields[0] * np.conj(fields[1]))) * dx / (2 * Z0))


def grid(n):
    dx = L / n
    x = (np.arange(n) - n // 2) * dx
    u = 2 * np.pi * np.fft.fftfreq(n, d=dx) / K0
    a = np.fft.ifft(np.fft.ifftshift(np.exp(-(x / W)**2))) * L
    mask = abs(u) < CUT
    a[~mask] = 0
    qi = np.sqrt(np.maximum(N1*N1 - u*u, 0))
    r, t, qt = (np.zeros(n, dtype=complex) for _ in range(3))
    for j in np.flatnonzero(mask):
        r[j], t[j], qt[j] = library_coefficients(u[j])
    pin_seed = float(np.sum(qi * abs(a)**2) / (L * 2 * Z0))
    scale = 1 / np.sqrt(pin_seed)
    a *= scale
    incident = np.array([synth(a), synth(-qi*a), synth(u*a)])
    reflected = np.array([synth(r*a), synth(qi*r*a), synth(u*r*a)])
    transmitted = []
    for z in Z_PLANES:
        az = a*t*np.exp(-1j*K0*qt*z)
        transmitted.append(np.array([synth(az), synth(-qt*az), synth(u*az)]))
    R = float(np.sum(qi * abs(r*a)**2) / (L*2*Z0))
    bins = qt.real * abs(t*a)**2 / (L*2*Z0)
    # Clamp no physics: tiny positive real(kz) under TIR from trig roundoff is
    # explicitly set to zero only for the propagating-flux diagnostics.
    bins[abs(u) >= N2] = 0
    T = float(np.sum(bins))
    sin_rms = float(np.sqrt(np.sum(bins * (u/N2)**2) / T))
    outside = float(np.sum(bins[abs(u) > N2*np.sin(0.1)]) / T)
    metrics = {'N': n, 'dx_m': dx, 'incident_flux_W_per_m': flux(incident, dx),
               'reflected_flux_W_per_m': flux(reflected, dx), 'R': R, 'T': T,
               'transmitted_flux_W_per_m': [flux(f, dx) for f in transmitted],
               'balance_abs': abs(1-R-T), 'rms_sin_theta': sin_rms,
               'flux_fraction_outside_0p1_rad': outside,
               'incident_peak_V_per_m': scale,
               'outgoing_evanescent_E_spectral_norm_fraction':
                   float(np.sum(abs(t*a)[abs(u)>=N2]**2)/np.sum(abs(t*a)**2))}
    return metrics, x, u, a, t, qt, transmitted


def independent_quadrature():
    """Continuous analytic spectrum and direct boundary admittances; no tmm/FFT."""
    def q2(u):
        return np.sqrt(N2*N2-u*u+0j).conjugate()
    def spectrum(u):
        return np.sqrt(np.pi)*W*np.exp(-(K0*W*u)**2/4)
    def transmission(u):
        y1 = np.sqrt(N1*N1-u*u)
        return 2*y1/(y1+q2(u))
    def integrate(f, lo=-CUT, hi=CUT):
        points = sorted({lo, hi, *[p for p in (-N2, 0., N2) if lo < p < hi]})
        return sum(quad(f, a, b, epsabs=1e-12, epsrel=1e-10, limit=150)[0]
                   for a, b in zip(points[:-1],points[1:]))
    # Dimensionless spectral weight removes SI scale from adaptive error control.
    def weight(u):
        return np.exp(-(K0*W*u)**2/2)
    wi = integrate(lambda u: np.sqrt(N1*N1-u*u)*weight(u))
    pin = wi*(np.pi*W*W)*K0/(2*np.pi*2*Z0)
    scale = 1/np.sqrt(pin)
    def pt(u):
        return float(q2(u).real * abs(transmission(u))**2 * weight(u))
    wt = integrate(pt, -N2, N2)
    angular = integrate(lambda u: pt(u)*(u/N2)**2, -N2, N2)
    cut = N2*np.sin(0.1)
    tail = integrate(pt,-N2,-cut)+integrate(pt,cut,N2)
    # Integrate relative field to incident peak so epsabs has a useful scale.
    fields = []
    for z in Z_PLANES:
        plane = []
        for x in (0.,1e-6,2e-6,4e-6):
            components = []
            for c in range(3):
                def f(u):
                    factor = (1.,-q2(u),u)[c]
                    return (K0/(2*np.pi)*spectrum(u)*transmission(u)*factor
                            *np.exp(-1j*K0*(u*x+q2(u)*z)))
                components.append(scale*(integrate(lambda u:f(u).real)
                                         +1j*integrate(lambda u:f(u).imag)))
            plane.append(components)
        fields.append(plane)
    return {'T':wt/wi, 'rms_sin_theta':float(np.sqrt(angular/wt)),
            'flux_fraction_outside_0p1_rad':tail/wt,
            'incident_peak_V_per_m':float(scale)}, np.array(fields)


def plane_wave_checks():
    results = []
    for angle in (0., 0.3, 1.0):
        u = N1*np.sin(angle)
        r,t,q2 = library_coefficients(u)
        q1 = N1*np.cos(angle)
        # Independent boundary E and H continuity, including complex TIR phase.
        boundary = max(abs(1+r-t), abs(q1*(1-r)-q2*t))
        T = q2.real*abs(t)**2/q1
        R = abs(r)**2
        results.append({'angle_rad':angle,'boundary_residual':float(boundary),
                        'R':float(R),'T':float(T),'balance_abs':float(abs(1-R-T)),
                        'q2_imag':float(q2.imag)})
    return results


def main():
    start=time.monotonic()
    checkout=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    data=[grid(n) for n in (512,1024)]
    a,b=data
    field_delta=[]
    for fa,fb in zip(a[-1],b[-1]):
        field_delta.append({'E_relative_L2':float(np.linalg.norm(fa[0]-fb[0,::2])/np.linalg.norm(fb[0,::2])),
                            'Z0H_relative_L2':float(np.linalg.norm(fa[1:]-fb[1:,::2])/np.linalg.norm(fb[1:,::2]))})
    relative={k:abs(a[0][k]-b[0][k])/abs(b[0][k]) for k in ('R','T','rms_sin_theta')}
    outside_delta=abs(a[0]['flux_fraction_outside_0p1_rad']-b[0]['flux_fraction_outside_0p1_rad'])
    qmetrics,qfields=independent_quadrature()
    # Spectral synthesis at the exact quadrature coordinates, no interpolation or fit.
    _,_,u,amp,t,qz,_=b
    sampled=np.array([[[np.sum(amp*t*np.exp(-1j*K0*qz*z)*factor
                                    *np.exp(-1j*K0*u*x))/L
                         for factor in (np.ones_like(u),-qz,u)]
                        for x in (0.,1e-6,2e-6,4e-6)] for z in Z_PLANES])
    qerr=float(np.max(abs(sampled-qfields))/qmetrics['incident_peak_V_per_m'])
    qrel={k:abs(b[0][k]-qmetrics[k])/abs(qmetrics[k]) for k in ('T','rms_sin_theta')}
    qoutside=abs(b[0]['flux_fraction_outside_0p1_rad']-qmetrics['flux_fraction_outside_0p1_rad'])
    pw=plane_wave_checks()
    removed=math.erfc(K0*W*CUT/np.sqrt(2))
    flux_error=max(max(abs(m['transmitted_flux_W_per_m'][j]-m['T']) for j in (0,1))
                   for m,*_ in data)
    flux_error=max(flux_error,*[abs(d[0]['reflected_flux_W_per_m']+d[0]['R']) for d in data],
                   *[abs(d[0]['incident_flux_W_per_m']-1) for d in data])
    gates={
        'sampling_field':max(v for d in field_delta for v in d.values())<1e-6,
        'sampling_flux_angular':max(relative.values())<1e-6 and outside_delta<1e-6,
        'power_balance':max(d[0]['balance_abs'] for d in data)<1e-10,
        'spatial_spectral_flux':flux_error<1e-10,
        'plane_wave_boundaries':max(d['boundary_residual'] for d in pw)<1e-10,
        'plane_wave_power':max(d['balance_abs'] for d in pw)<1e-10,
        'normal_incidence':abs(pw[0]['R']-0.04)<1e-10 and abs(pw[0]['T']-0.96)<1e-10,
        'tir':abs(pw[2]['T'])<1e-10 and pw[2]['q2_imag']<0,
        'continuous_field':qerr<1e-4,
        'continuous_flux_angular':max(qrel.values())<1e-4 and qoutside<0.02,
        'incident_spectral_cut':removed<1e-12,
    }
    report={'control_id':'M4C-TE-PLANAR-001','scope':'Synthetic 2D TE, invariant y; not actual WAFT/PIC',
            'wavelength_m':WAVELENGTH,'assumed_indices':[N1,N2],'assumed_w_m':W,
            'window_m':L,'z_planes_m':Z_PLANES,'samplings':[d[0] for d in data],
            'sampling_field_difference':field_delta,'sampling_relative_difference':relative,
            'sampling_outside_fraction_abs_difference':outside_delta,
            'spatial_spectral_flux_max_error':flux_error,'plane_waves':pw,
            'continuous_quadrature':qmetrics,'quadrature_max_field_relative_to_peak':qerr,
            'quadrature_relative_difference':qrel,'quadrature_outside_fraction_abs_difference':qoutside,
            'incident_removed_spectral_norm_bound':removed,'gates':gates,
            'status':'Pass' if all(gates.values()) else 'Fail',
            'actual_external_field':'Uncomputed','actual_overlap':None,'total_coupling':None,
            'full_package_feasibility':'Uncomputed'}
    out=ROOT/'results';out.mkdir(exist_ok=True)
    (out/'m4c_planar_control.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    for d in data:
        metrics,x,u,amp,t,qz,fields=d
        np.savez_compressed(out/f"m4c_fields_{metrics['N']}.npz",x_m=x,kx_per_m=u*K0,
                            incident_spectrum=amp,transmitted_spectrum=amp*t,
                            z_m=Z_PLANES,Ey_Z0Hx_Z0Hz=np.array(fields))
    elapsed=time.monotonic()-start
    paths=['scripts/m4c_planar_control.py','scripts/check_m4c_stop.py',
           'docs/M4C_REFERENCE_PLAN.md','docs/M4C_EXTERNAL_FIELD_REFERENCE.md',
           'references/m4c_external_field_request.json','requirements-m4c.txt',
           '.github/workflows/validate.yml']
    paths += sorted(str(p.relative_to(ROOT)) for p in (ROOT/'src').rglob('*.py'))
    provenance={'evaluated_checkout_sha':checkout,'checkout_dirty_before_run':dirty,
                'elapsed_s':elapsed,'peak_rss_bytes_linux':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                'python':platform.python_version(),
                'versions':{p:importlib.metadata.version(p) for p in ('numpy','scipy','tmm')},
                'sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
                'tmm_core_sha256':hashlib.sha256(Path(tmm.tmm_core.__file__).read_bytes()).hexdigest(),
                'result_sha256':hashlib.sha256((out/'m4c_planar_control.json').read_bytes()).hexdigest()}
    (out/'m4c_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'gates':gates,'elapsed_s':elapsed,
                      'fine_grid':b[0],'quadrature_field_error':qerr,'quadrature_relative':qrel},indent=2))
    return 0 if all(gates.values()) else 1


if __name__=='__main__':
    raise SystemExit(main())
