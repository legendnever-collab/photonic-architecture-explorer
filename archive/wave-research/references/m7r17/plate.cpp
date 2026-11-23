// exp(+iwt), length in wavelengths. Full monochromatic finite PEC PO integral.
// Symmetry about the incidence plane leaves six nonzero field components.
#include <cmath>
#include <complex>
using Complex = std::complex<double>;

extern "C" void plate(int density, double width, double length, double sine,
                      double observer_x, double observer_z, Complex *out) {
    const double k = 2*std::acos(-1.), cosine = std::sqrt(1-sine*sine);
    const int nx = std::ceil(width*density), ny = std::ceil(length*density/2);
    const double dx = width/nx, dy = length/(2*ny);
    Complex total[6]{};
    #pragma omp parallel
    {
        Complex partial[6]{};
        #pragma omp for
        for (int i=0; i<nx; ++i) {
            const double x = (i+0.5)*dx, delta = observer_x-x;
            for (int j=0; j<ny; ++j) {
                const double y = (j+0.5)*dy;
                const double r = std::sqrt(delta*delta + y*y + observer_z*observer_z);
                const double ux=delta/r, uy=-y/r, uz=observer_z/r;
                const double phase = -k*(r+sine*x);
                const Complex g(std::cos(phase)/r, std::sin(phase)/r);
                const Complex curvature = Complex(1, -1/(k*r))/r;
                const Complex transverse(0,-k);
                const Complex radial = -transverse + 3.*curvature;
                const Complex curl(-1/r, -k);
                // E = G [(transverse-curvature) I + radial uu] J
                // H = G curl (u x J). TE has Jy=2 cos(theta), TM has Jx=-2.
                partial[0] += g*(transverse-curvature+radial*uy*uy)*(2*cosine);
                partial[1] += g*curl*(-uz*2*cosine);
                partial[2] += g*curl*(ux*2*cosine);
                partial[3] += g*(transverse-curvature+radial*ux*ux)*(-2.);
                partial[4] += g*radial*ux*uz*(-2.);
                partial[5] += g*curl*uz*(-2.);
            }
        }
        #pragma omp critical
        for (int d=0; d<6; ++d) total[d] += partial[d];
    }
    for (int d=0; d<6; ++d) out[d]=total[d]*(2*dx*dy/(2*k));
}
