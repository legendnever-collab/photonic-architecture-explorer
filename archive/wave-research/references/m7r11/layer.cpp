// Scalar Helmholtz layer and receiver normal derivative; all coordinates in metres.
// Each input amplitude includes its quadrature area. Normals are unit vectors.
#include <cmath>
#include <complex>
using Complex = std::complex<double>;

extern "C" void layer(int count, const double* p, const double* normal,
                      const Complex* amplitude, int receivers, const double* dest,
                      const double* direction, double k, bool launch,
                      Complex* field, Complex* derivative) {
    constexpr double inv4pi = 0.0795774715459476679;
    #pragma omp parallel for schedule(static)
    for (int j = 0; j < receivers; ++j) {
        Complex sum{}, grad{};
        for (int i = 0; i < count; ++i) {
            double d[3], distance2 = 0, arrival = 0;
            for (int l = 0; l < 3; ++l) {
                d[l] = dest[3*j+l] - p[3*i+l];
                distance2 += d[l]*d[l];
                arrival += d[l]*direction[3*j+l];
            }
            double r = std::sqrt(distance2), inv = 1/r;
            arrival *= inv;
            Complex g = amplitude[i] * (inv4pi * inv)
                      * Complex(std::cos(k*r), -std::sin(k*r));
            Complex a(inv,k);
            if (launch) {
                double departure = 0, axes = 0;
                for (int l = 0; l < 3; ++l) {
                    departure += d[l]*normal[3*i+l]*inv;
                    axes += normal[3*i+l]*direction[3*j+l];
                }
                Complex value = 2.0*g*a*departure;
                sum += value;
                grad += -a*arrival*value + 2.0*g*inv*
                        (a*(axes-departure*arrival)-departure*arrival*inv);
            } else {
                sum += g;
                grad -= a*arrival*g;
            }
        }
        field[j] = sum;
        derivative[j] = grad;
    }
}
