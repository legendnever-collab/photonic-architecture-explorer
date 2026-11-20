// Scalar outgoing Helmholtz single layer, exp(+i omega t). SoA input buffers.
#include <cmath>

extern "C" void reflected(int n, const double* src, const double* amplitude,
                          int m, const double* dst, const double* normals,
                          double k, double* result) {
    #pragma omp parallel for
    for (int j = 0; j < m; ++j) {
        double er=0, ei=0, gr=0, gi=0;
        #pragma omp simd reduction(+:er,ei,gr,gi)
        for (int i = 0; i < n; ++i) {
            double dx=dst[3*j]-src[i], dy=dst[3*j+1]-src[n+i], dz=dst[3*j+2]-src[2*n+i];
            double r=std::sqrt(dx*dx+dy*dy+dz*dz);
            double cs=std::cos(k*r), sn=std::sin(k*r);
            // amplitude already includes patch area, PO density and 1/(4*pi).
            double re=(amplitude[i]*cs+amplitude[n+i]*sn)/r;
            double im=(amplitude[n+i]*cs-amplitude[i]*sn)/r;
            double projection=(dx*normals[3*j]+dy*normals[3*j+1]+dz*normals[3*j+2])/r;
            er+=re;
            ei+=im;
            gr+=projection*(k*im-re/r);
            gi+=projection*(-k*re-im/r);
        }
        result[4*j]=er; result[4*j+1]=ei;
        result[4*j+2]=gr; result[4*j+3]=gi;
    }
}
