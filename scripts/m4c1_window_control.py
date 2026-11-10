"""M4C1-TE-WINDOW-001: fixed window study reusing the frozen planar reference."""
import argparse
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import resource
import subprocess
import time
import uuid

import numpy as np
from scipy.integrate import quad
import tmm
import m4c_planar_control as ref
from m4c_evidence import ROOT, head, seal, sha, verify

WINDOWS = (80e-6, 160e-6, 320e-6, 640e-6, 1280e-6)


def exact_points(data, length):
    _, _, u, amp, t, qz, _ = data
    return np.array([[[np.sum(amp*t*np.exp(-1j*ref.K0*qz*z)*factor
                             *np.exp(-1j*ref.K0*u*x))/length
                       for factor in (np.ones_like(u), -qz, u)]
                      for x in (0., 1e-6, 2e-6, 4e-6)] for z in ref.Z_PLANES])


def reflected_quadrature():
    """Direct TE admittance reflection, analytic Gaussian; no library/FFT reuse."""
    def weight(u):
        return np.exp(-(ref.K0*ref.W*u)**2/2)
    def integrate(f):
        return sum(quad(f, a, b, epsabs=1e-12, epsrel=1e-10, limit=150)[0]
                   for a,b in zip((-ref.CUT,-ref.N2,0.,ref.N2),
                                  (-ref.N2,0.,ref.N2,ref.CUT)))
    def incident(u):
        return np.sqrt(ref.N1**2-u*u)*weight(u)
    def reflected(u):
        qi = np.sqrt(ref.N1**2-u*u)
        qt = np.sqrt(ref.N2**2-u*u+0j).conjugate()
        return incident(u)*abs((qi-qt)/(qi+qt))**2
    return integrate(reflected)/integrate(incident)


def audit_external():
    request = json.loads((ROOT/'references/m4c_external_field_request.json').read_text())
    def missing(value, prefix=''):
        if isinstance(value, dict):
            return [p for k,v in value.items() for p in missing(v, prefix+'.'+k if prefix else k)]
        return [prefix] if value is None else []
    gaps = missing(request)
    return {'request_case_id': request['case_id'], 'request_provenance': request['provenance'],
            'missing_fields': gaps,
            'status': 'Unprovided' if gaps else 'Requires external data review',
            'scope': 'Repository request and files supplied with this task; no external field files supplied',
            'not_an_automatic_field_validator': True,
            'resume_condition': 'Non-confidential complex E/H export with reference plane, medium, units, phase, power and convergence metadata; or a reproducible local facet model. Reciprocal Target required separately.'}


def calculate(out):
    qmetrics, qfields = ref.independent_quadrature()
    qr = reflected_quadrature()
    rows, outputs = [], []
    for length in WINDOWS:
        coarse_n = round(length/(ref.L/512))
        data = [ref.grid(n, window_m=length) for n in (coarse_n, 2*coarse_n)]
        a,b = data
        deltas = [{'E_relative_L2': float(np.linalg.norm(fa[0]-fb[0,::2])/np.linalg.norm(fb[0,::2])),
                   'Z0H_relative_L2': float(np.linalg.norm(fa[1:]-fb[1:,::2])/np.linalg.norm(fb[1:,::2]))}
                  for fa,fb in zip(a[-1],b[-1])]
        relative = {k:abs(a[0][k]-b[0][k])/abs(b[0][k]) for k in ('R','T','rms_sin_theta')}
        tail_delta = abs(a[0]['flux_fraction_outside_0p1_rad']-b[0]['flux_fraction_outside_0p1_rad'])
        point_fields = [exact_points(d,length) for d in data]
        field_errors = [float(np.max(abs(v-qfields))/qmetrics['incident_peak_V_per_m']) for v in point_fields]
        smooth_errors = [{k:abs(d[0][k]-qmetrics[k])/abs(qmetrics[k]) for k in ('T','rms_sin_theta')} for d in data]
        tail_errors = [abs(d[0]['flux_fraction_outside_0p1_rad']-qmetrics['flux_fraction_outside_0p1_rad']) for d in data]
        reflected_errors = [abs(d[0]['R']-qr)/qr for d in data]
        flux_error = max(abs(m['incident_flux_W_per_m']-1) for m,*_ in data)
        for m,*_ in data:
            flux_error = max(flux_error, abs(m['reflected_flux_W_per_m']+m['R']),
                             *[abs(v-m['T']) for v in m['transmitted_flux_W_per_m']])
        gates = {
            'sampling_field':max(v for d in deltas for v in d.values())<1e-6,
            'sampling_flux_angular':max(relative.values())<1e-6 and tail_delta<1e-6,
            'power_balance':max(d[0]['balance_abs'] for d in data)<1e-10,
            'spatial_spectral_flux':flux_error<1e-10,
            'continuous_field':max(field_errors)<1e-4,
            'continuous_smooth_flux_angular':max(v for d in smooth_errors for v in d.values())<1e-4,
            'continuous_reflected_flux':max(reflected_errors)<1e-4,
            'continuous_tail':max(tail_errors)<0.02}
        du = ref.WAVELENGTH/length
        rows.append({'window_m':length, 'delta_u':du,
                     'cutoff_bin_coordinate':float(ref.N2*np.sin(0.1)/du),
                     'samplings':[d[0] for d in data], 'sampling_field_difference':deltas,
                     'sampling_relative_difference':relative, 'sampling_tail_abs_difference':tail_delta,
                     'continuous_field_errors':field_errors, 'continuous_smooth_relative_errors':smooth_errors,
                     'continuous_tail_abs_errors':tail_errors, 'continuous_R_relative_errors':reflected_errors,
                     'spatial_spectral_flux_max_error':flux_error, 'gates':gates})
        for d,points in zip(data,point_fields):
            m,x,u,amp,t,qz,fields = d
            name = f"m4c1_fields_L{round(length*1e6)}_N{m['N']}.npz"
            np.savez_compressed(out/name, x_m=x, kx_per_m=u*ref.K0,
                                incident_spectrum=amp, transmitted_spectrum=amp*t,
                                z_m=ref.Z_PLANES, Ey_Z0Hx_Z0Hz=np.array(fields),
                                exact_point_fields=points, independent_point_fields=qfields)
            outputs.append(name)
    pw = ref.plane_wave_checks()
    removed = math.erfc(ref.K0*ref.W*ref.CUT/np.sqrt(2))
    last_change = abs(rows[-1]['samplings'][1]['flux_fraction_outside_0p1_rad']-
                      rows[-2]['samplings'][1]['flux_fraction_outside_0p1_rad'])
    gates = {
        'all_windows_non_tail':all(v for r in rows for k,v in r['gates'].items() if k!='continuous_tail'),
        'final_two_windows_all_criteria':all(all(r['gates'].values()) for r in rows[-2:]),
        'final_two_tail_difference':last_change<0.02,
        'legacy_failure_reproduced':all(abs(v-0.027777663568040678)<1e-12 for v in rows[0]['continuous_tail_abs_errors']),
        'continuous_power_balance':abs(1-qr-qmetrics['T'])<1e-10,
        'plane_wave_boundaries':max(d['boundary_residual'] for d in pw)<1e-10,
        'plane_wave_power':max(d['balance_abs'] for d in pw)<1e-10,
        'normal_incidence':abs(pw[0]['R']-0.04)<1e-10 and abs(pw[0]['T']-0.96)<1e-10,
        'tir':abs(pw[2]['T'])<1e-10 and pw[2]['q2_imag']<0,
        'incident_spectral_cut':removed<1e-12}
    report = {'control_id':'M4C1-TE-WINDOW-001', 'scope':'Synthetic 2D TE planar only; not actual WAFT/PIC',
              'status':'Pass' if all(gates.values()) else 'Fail', 'gates':gates, 'windows':rows,
              'continuous_quadrature':dict(qmetrics, R=qr, balance_abs=abs(1-qr-qmetrics['T'])),
              'final_two_tail_abs_difference':last_change, 'plane_waves':pw,
              'incident_removed_spectral_norm_bound':removed, 'external_input_audit':audit_external(),
              'actual_external_field':'Uncomputed', 'actual_overlap':None, 'total_coupling':None,
              'full_package_feasibility':'Uncomputed'}
    name = 'm4c1_window_control.json'
    (out/name).write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return report, outputs+[name]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir',type=Path)
    args = parser.parse_args()
    run_id = uuid.uuid4().hex
    out = (args.output_dir or ROOT/'results/runtime'/('m4c1-'+run_id)).resolve()
    out.mkdir(parents=True,exist_ok=False)
    os.environ['M4C_RUN_ID'] = run_id
    start = time.monotonic()
    checkout = head()
    dirty = bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    report, outputs = calculate(out)
    paths = ['scripts/m4c_planar_control.py','scripts/m4c1_window_control.py',
             'scripts/check_m4c_stop.py','docs/M4C1_VERIFICATION_PLAN.md','docs/M4C_REFERENCE_PLAN.md',
             'references/m4c_external_field_request.json','requirements-m4c.txt','.github/workflows/validate.yml']
    paths += sorted(str(p.relative_to(ROOT)) for folder in ('src','tests','examples')
                    for p in (ROOT/folder).rglob('*') if p.suffix in ('.py','.json'))
    provenance = {'evaluated_checkout_sha':checkout, 'checkout_dirty_before_run':dirty,
                  'elapsed_s':time.monotonic()-start,
                  'peak_rss_bytes_linux':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                  'python':platform.python_version(),
                  'versions':{p:importlib.metadata.version(p) for p in ('numpy','scipy','tmm')},
                  'sha256':{p:sha(ROOT/p) for p in paths},
                  'tmm_core_sha256':sha(Path(tmm.tmm_core.__file__))}
    seal(out,provenance,outputs)
    (out/'m4c1_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    verify(out,provenance,run_id,checkout)
    print(json.dumps({'status':report['status'],'gates':report['gates'],
                      'tail_errors':[r['continuous_tail_abs_errors'][1] for r in report['windows']],
                      'elapsed_s':provenance['elapsed_s'],'output_dir':str(out)},indent=2))
    return 0 if report['status']=='Pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
