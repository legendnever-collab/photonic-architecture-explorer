# M7-R15 사전 검증 범위

Main 5af007336e001740dfb630231c9e74c1a2f1d1cd에서 R5 Glass와 R6 SMF의 case·편광·1310 nm·공기 쪽 +5 µm를 고정한다. 기존 base/grid/basis/window 네 단계씩 재현한다. FMMAX 1.7.1·JAX/JAXLIB 0.12.1 CPU float64를 사용한다.

- 내부 incident/reflected 분리 모드의 +z flux와 공기면 outgoing +z flux를 저장한다. Vacuum plane wave에서 FMMAX의 상대 E/H 임피던스 1을 검사한다. Export와 일치하는 power는 모니터의 면적 평균에 셀 면적을 곱하고 중심 Ex 복소계수의 제곱 크기로 나눈 값이다.
- 증거 파일의 SHA를 검증한다. 저장 Fourier 장의 독립 격자 적분과 Solver monitor는 상대차 1e−8 이내를 요구한다. 각 run의 Fourier order와 6성분을 재현해 상대 L² 1e−8 이내를 요구한다. |T+R−1|에는 원래 1e−3 Gate를 적용하고, 내부 단독 모드 합의 전체 monitor 대비 잔차도 보고한다.
- R14의 2.5e−4 할당과 비교할 진단으로, 각 Grid/Basis/Window 쌍에서 T와 R의 절대 변화 및 각 정규화 Power의 상대 변화를 기록한다. 변화와 balance를 보수적으로 더한 screening 값이 할당 이내인지 판정한다. 이 비교는 유한 주기 이상화 모델에서의 관찰치다. Relay 전체 U는 후속 독립 대조를 필요로 한다.
