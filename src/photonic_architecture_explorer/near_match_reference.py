"""Independent NumPy ABCD/complex-field reference; no production Gaussian kernels."""
import math
import numpy as np


def independent_check(candidate, ports):
    """ABCD transport and direct complex quadrature independent of Gaussian kernels."""
    prescription, evaluation = candidate["prescription"], candidate["evaluation"]
    mirrors = prescription["design"]["reflectors"]
    points = np.array([ports.source.position,
                       *[m["vertex_m"]["value"] for m in mirrors], ports.target.position])
    segments = np.diff(points, axis=0)
    lengths = np.linalg.norm(segments, axis=1)
    directions = segments / lengths[:, None]
    np.testing.assert_allclose(directions[0], ports.source.direction, atol=1e-12, rtol=0)
    np.testing.assert_allclose(directions[-1], ports.target.direction, atol=1e-12, rtol=0)
    powers = []
    for index, mirror in enumerate(mirrors):
        normal = np.array(mirror["illuminated_normal"]["value"])
        np.testing.assert_allclose(directions[index] - 2 * np.dot(directions[index], normal) * normal,
                                   directions[index + 1], atol=1e-12, rtol=0)
        cosine = -np.dot(directions[index], normal)
        kt, ks = mirror["principal_curvature_ts_per_m"]["value"]
        powers.append((2 * kt / cosine, 2 * ks * cosine))
    translation = lambda length: np.array([[1., length], [0., 1.]])
    power = lambda value: np.array([[1., 0.], [-value, 1.]])
    q_output = []
    for axis, source_q in enumerate(ports.source.mode.q):
        matrix = (translation(lengths[2]) @ power(powers[1][axis])
                  @ translation(lengths[1]) @ power(powers[0][axis])
                  @ translation(lengths[0]))
        q = (matrix[0, 0] * source_q + matrix[0, 1]) / (matrix[1, 0] * source_q + matrix[1, 1])
        output = evaluation["gaussian_mode_matching"]["output_axes"][axis]
        actual_q = complex(-output["waist_distance_m"], output["rayleigh_range_m"])
        if not (abs(q - actual_q) / abs(q) <= 1e-10):
            raise AssertionError("Independent near-match numerical check failed")
        q_output.append(q)
    # Independently inspect the intermediate q at every powered surface.
    intermediate = np.array(ports.source.mode.q, dtype=complex)
    guard_checks = []
    for mirror_index in range(2):
        intermediate += lengths[mirror_index]
        radii = np.sqrt(-ports.source.mode.wavelength /
                        (math.pi * ports.source.mode.index * np.imag(1 / intermediate)))
        cosine = evaluation["geometry"]["cosines"][mirror_index]
        footprint = radii / np.array([cosine, 1.])
        curvatures = np.array(mirrors[mirror_index]["principal_curvature_ts_per_m"]["value"])
        slope = float(np.max(3 * footprint * abs(curvatures)))
        before = evaluation["samples"][1 + 2 * mirror_index]
        np.testing.assert_allclose(footprint, before["surface_radii_m"], rtol=1e-10, atol=1e-15)
        if not (abs(slope - before["footprint_slope_3w"]) <= 1e-10):
            raise AssertionError("Independent near-match numerical check failed")
        if not (slope <= .15):
            raise AssertionError("Independent near-match numerical check failed")
        intermediate = 1 / (1 / intermediate - np.array(powers[mirror_index]))
        divergence = np.sqrt(ports.source.mode.wavelength /
                             (math.pi * ports.source.mode.index * intermediate.imag))
        if not (max(divergence) <= .1):
            raise AssertionError("Independent near-match numerical check failed")
        after = evaluation["samples"][2 + 2 * mirror_index]["axes"]
        np.testing.assert_allclose(divergence, [v["divergence_rad"] for v in after],
                                   rtol=1e-10, atol=1e-15)
        guard_checks.append({"footprint_m": footprint.tolist(), "max_3w_curvature": slope,
                             "outgoing_divergence_rad": divergence.tolist()})
    wavelength, index = ports.source.mode.wavelength, ports.source.mode.index
    wave_number = 2 * math.pi * index / wavelength
    overlaps = []
    for count, window in ((16385, 8), (32769, 10)):
        overlap = 1.
        for incoming, target in zip(q_output, ports.target.mode.q):
            wi = math.sqrt(-wavelength / (math.pi * index * (1 / incoming).imag))
            wt = math.sqrt(-wavelength / (math.pi * index * (1 / target).imag))
            x = np.linspace(-window * max(wi, wt), window * max(wi, wt), count)
            incident = np.exp(-x*x/(wi*wi) - .5j*wave_number*(1/incoming).real*x*x)
            desired = np.exp(-x*x/(wt*wt) - .5j*wave_number*(1/target).real*x*x)
            overlap *= float(abs(np.trapezoid(desired.conj()*incident, x))**2
                             / (np.trapezoid(abs(incident)**2, x) * np.trapezoid(abs(desired)**2, x)))
        if not (abs(overlap - candidate["overlap"]) <= 1e-8):
            raise AssertionError("Independent near-match numerical check failed")
        overlaps.append(overlap)
    if not (abs(overlaps[0] - overlaps[1]) <= 1e-8):
        raise AssertionError("Independent near-match numerical check failed")
    return {"status": "Pass", "quadrature_overlap": overlaps,
            "q_output_m": [[q.real, q.imag] for q in q_output], "surface_checks": guard_checks}
