// Periodic Weyl sum at arbitrary points on the actual M1 sag.
#include <cmath>
#include <complex>
extern "C" void evaluate(int count, int modes, const double *xyz, const double *k,
                          const std::complex<double> *field, std::complex<double> *out) {
    #pragma omp parallel for
    for (int p = 0; p < count; ++p) {
        std::complex<double> sum[6]{};
        for (int j = 0; j < modes; ++j) {
            double phase = 0;
            for (int d = 0; d < 3; ++d) phase += xyz[3*p+d]*k[3*j+d];
            const std::complex<double> factor(std::cos(phase), std::sin(phase));
            for (int d = 0; d < 6; ++d) sum[d] += factor*field[6*j+d];
        }
        for (int d = 0; d < 6; ++d) out[6*p+d] = sum[d];
    }
}
