# Frozen M1 scope

Purpose: 두 고정 Port 사이에서 두 curved reflector의 기하학적 가능성과
paraxial Mode Matching 효과를 작은 재현 가능한 tool로 구분합니다.

Implemented: immutable Ports, elliptical Gaussian q, exactly two supplied
reflectors, specular closure and local frames, coplanar oblique astigmatic powers,
principal curvature parameters, Gaussian overlap, Flat/Curved/spherical-control
comparison, input/domain/chief-ray obstruction guards, classified JSON reports.

Not implemented: architecture search, full freeform prescription/inverse design,
FDTD/FEM/Maxwell, CAD, 3D/UI, novelty scoring, company data, actual SSC adapter,
manufacturing optimization. Dataclasses and pure functions leave room for future
architectures without adding an architecture registry or plug-in framework now.

Status semantics:

- Pass: 해당 명시된 검사/계산을 통과. 모델 외 실제 성능을 의미하지 않음.
- Fail: geometry 또는 supported-domain guard에 실패. 원인과 실패 범주 명시.
- Uncomputed: 선행 검사 실패 또는 M1 미구현 항목. 0으로 대체하지 않음.

Malformed primitive inputs (NaN/Inf/nonpositive radius/invalid q) raise DomainError
at construction. Constructible designs return classified reports via evaluate().
Physical-loss and fabrication fields remain Uncomputed for every case.
