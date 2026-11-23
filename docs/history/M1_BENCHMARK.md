# M1-001 frozen synthetic benchmark

Frozen before implementation, 2026-11-09. All lengths are metres, angles radians,
wavelength is vacuum wavelength. Synthetic external fields, not measured PIC or
Glass Waveguide modes. No customer/company inputs.

- Right-handed global (X,Y,Z); fold plane XZ; common sagittal axis +Y.
- Vacuum wavelength 1.310e-6; homogeneous ambient index 1.0 throughout.
- Source: (0,0,0), propagation +X, tangential axis -Z, sagittal +Y.
- M1 vertex: (0.001,0,0); illuminated normal (-1,0,1)/sqrt(2).
- M2 vertex: (0.001,0,0.002); illuminated normal (1,0,-1)/sqrt(2).
- Target: (0.002,0,0.002), accepted propagation +X, tangential -Z, sagittal +Y.
- Both Port waist radii: tangential 8e-6, sagittal 12e-6 (1/e^2 intensity
  radii, MFD 16 and 24 micrometres); flat phase, normalized scalar power 1.
- Segment lengths: f, 2f, f with f=0.001. Incidence angles 45 degrees.
- Both reflector tangent-plane rectangular half-apertures: 0.0007 tangential,
  0.0005 sagittal. Local surface h=(kappa_t*u^2+kappa_s*v^2)/2 along the
  illuminated normal. Aperture bounds refer to local u,v coordinates.
- Flat control: both principal curvatures zero.
- Curved relay: both reflectors kappa_t=cos(pi/4)/(2f),
  kappa_s=1/(2f*cos(pi/4)); hence P_t=P_s=1/f. These are local biconic/
  toroidal-equivalent principal curvatures, NOT spherical mirrors or a
  manufactured freeform prescription. Exact local paraboloid patches serve
  only chief-ray obstruction and differential-ray reference tests.
- Additional astigmatism control: spherical vertex curvatures kappa_t=kappa_s
  =500 m^-1. This is an intentionally unmatched comparison, not optimization.

Analytical predictions fixed before implementation:

1. Specular path +X -> +Z -> +X closes exactly at the fixed Target.
2. Flat q_out=q_in+0.004 for each axis.
3. Curved first-order relay matrix is -I, thus q_out=q_in and ideal normalized
   Mode Overlap is 1 (within 1e-10). Geometric transverse parity from two folds
   is identity; -I also inverts the image in the unfolded paraxial relay.
4. Flat centered equal-waist overlap is product over axes of
   [1+(L/(2*z_R))^2]^(-1/2), z_R=pi*n*w0^2/lambda0.
5. Curved overlap must exceed Flat by at least 0.5 absolute and output radii
   must differ by at least 20%; this verifies curvature effects, not product gain.

Acceptance limits (engineering guards, not rigorous aberration error bounds):
direction closure 1e-10; minimum segment 1e-9 m; coplanarity/alignment 1e-10;
incidence <=70 degrees; each segment's asymptotic waist divergence <=0.1 rad;
3w projected footprint times absolute principal curvature <=0.15;
sum of Gaussian tangent-plane rectangular aperture-tail estimates <=1e-6.
No tuning these thresholds to turn a failing test green.

Independent validation: analytic propagation/overlap limits; discrete Fresnel
propagation with sampled quadratic phase masks; exact local-surface ray
reflection differentiated at the vertex; independent complex-field quadrature;
rigid world-frame transformations; adversarial invalid inputs.

Required negative cases: wrong endpoint direction, incorrect normal, zero
segment, unequal medium/wavelength, noncoplanar path, rolled elliptical axes,
high NA, grazing incidence, excessive curvature/footprint, tiny aperture,
nonfinite values and invalid q. Failure withholds Mode Overlap.

Physical coating loss, Fresnel loss at actual devices, polarization, roughness,
finite-aperture diffraction, finite-beam aberration, packaging bodies,
fabrication and assembly feasibility, total coupling: Uncomputed.
