"""Collect nominal replay, probe comparisons and same-window convergence."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import subprocess

import numpy as np
import scipy
from scipy.interpolate import RectBivariateSpline

from scripts import m7r12_quadrature as q
from scripts import m7r12_window as window


def load(directory, name):
    return json.loads((directory / name).read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    folder = parser.parse_args().directory
    q.check_inputs()
    tags = ["q6-6-edge1", "q8-8-edge1", "q10-10-edge1", "q14-14-edge1",
            "q-512-14-edge1", "q14-14-edge2", "q14-14-edge4", "q-640--640-edge1"]
    rows = {tag: load(folder,tag+".json") for tag in tags}
    sources = ([f"filon-{i}" for i in (3,4,6,8,10,12)] +
               ["midpoint-324-probes"] + ["probes-"+tag for tag in tags])
    probe_errors = {}
    arrays = {}
    with np.load(folder/"filon-12.npz") as reference:
        arrays.update(xyz_m=reference["xyz_m"], normals=reference["normals"])
        for name in sources:
            with np.load(folder/(name+".npz")) as values:
                np.testing.assert_array_equal(values["xyz_m"],reference["xyz_m"])
                np.testing.assert_array_equal(values["normals"],reference["normals"])
                errors = {}
                for key in ("E","dE_dn"):
                    arrays[name+"_"+key] = values[key]
                    errors[key] = q.relative(values[key],reference[key])
                def current(z):
                    return np.imag(z["E"].conj()*z["dE_dn"])/q.r11.K
                errors["local_incident_current"] = q.relative(current(values),current(reference))
                probe_errors[name] = errors
    np.savez_compressed(folder/"common-M2-probes.npz",**arrays)

    fine = tags[3]
    midpoint = tags[-1]
    def eta(tag,pitch,half):
        return next(x["eta"] for x in rows[tag]["target"] if x["pitch_um"]==pitch
                    and x["half_window_um"]==half)
    with np.load(folder/f"M2-{fine}.npz") as a, np.load(folder/f"M2-{tags[4]}.npz") as b:
        for key in ("u_m","v_positive_m","area_m2"):
            np.testing.assert_array_equal(a[key],b[key])
        weighted = {k: q.relative(np.sqrt(a["area_m2"])*b[k],np.sqrt(a["area_m2"])*a[k])
                    for k in ("E","dE_dn")}
    with np.load(folder/f"target-{fine}-2um.npz") as a, np.load(folder/f"target-{midpoint}-2um.npz") as b:
        np.testing.assert_array_equal(a["ts_m"],b["ts_m"])
        target_difference = {k:q.relative(b[k],a[k]) for k in ("E","dE_dx")}
    # Resample *current*, not the fast complex field. This uses the published R11
    # receiver rule without a ninth relay or another M1 source integral.
    receiver = q.r11.mirror_surface(q.MIRRORS[1], 324, False, 1)
    u = receiver[3].reshape(324,324)[:,0]
    v = receiver[4].reshape(324,324)[0]
    area = receiver[2].reshape(324,324)
    receiver_checks = {}
    for tag in (fine,midpoint):
        with np.load(folder/f"M2-{tag}.npz") as z:
            positive = (z["E"].conj()*z["dE_dn"]).imag/q.r11.K
            current = np.column_stack((positive[:,::-1],positive))
            y = np.r_[-z["v_positive_m"][::-1],z["v_positive_m"]]
            receiver_checks[tag] = {}
            for degree in (3,5):
                spline = RectBivariateSpline(z["u_m"],y,current,kx=degree,ky=degree)
                power = np.sum(spline(u,v)*area)
                incident = rows[tag]["M1_over_launch"]*q.FROZEN["runs"][0]["launch_flux"]
                receiver_checks[tag][str(degree)] = float(power/incident)
    grazing = {tag:window.grazing(folder/f"M2-{tag}.npz",rows[tag]["orders"][1],rows[tag]["edge"])
               for tag in tags[3:]}
    checks = dict(
        refined_current_on_R11_M2_receiver=receiver_checks,
        M1_rule_change_same_M2_weighted_relative=weighted,
        M1_rule_change_same_M2_flux_ratio_delta=abs(rows[fine]["M2_over_M1"]-rows[tags[4]]["M2_over_M1"]),
        target_192um_cross_rule_field_relative=target_difference,
        target_192um_cross_rule_eta_delta=abs(eta(fine,2,192)-eta(midpoint,2,192)),
        interior_at_fixed_48um=[eta(tag,1,48) for tag in tags[:4]],
        edge_at_fixed_48um=[eta(tag,1,48) for tag in (fine,tags[5],tags[6])],
        pitch_at_fixed_48um=[eta(fine,p,48) for p in (2,1,.5)],
        window_at_fixed_2um=[eta(fine,2,w) for w in (24,48,96,192)],
    )
    archived = ["common-M2-probes.npz",f"M2-{fine}.npz",f"target-{fine}-2um.npz",
                f"target-{fine}-0.5um.npz"]
    data = dict(
        base_sha="e21c165d5dd06f2fe18402ae664bd58287d92e3f",
        inputs=q.FROZEN["inputs"], replay=load(folder,"replay.json"),
        filon=load(folder,"filon.json"), relative_to_filon12_at_probes=probe_errors,
        runs=rows, comparisons=checks, grazing_far_field=grazing,
        sha256={name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in archived},
        runtime=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
                     compiler=subprocess.check_output(["g++","--version"],text=True).splitlines()[0]),
        decision=dict(numerical_U=None, nominal_threshold="Uncomputed", finite_beam_clearance=None,
                      aperture_throughput=None, perturbed_mode_overlap=None, actual_total_coupling=None,
                      limiting_evidence="No supported bound on the outside-window squared-field norm or full numerical remainder.",
                      positive_mrad_mechanical_gap_um=49.289713, required_gap_um=50),
    )
    (folder/"summary.json").write_text(json.dumps(data,indent=2,allow_nan=False)+"\n")


if __name__ == "__main__":
    main()
