# M7-R16 사전 계산 계약

#46 c4876ab2927a0eee0b9159add7cb965e6a3785ef. R6 Fixed Port, R8 확장 두 quadratic patch, R7 기구 조건과 R15 최종 SMF Fourier E/H 및 같은 run의 P_launch=1.7426507346302212e−11 m²를 사용한다. 공기 n=1, λ=1310 nm, exp(+iωt), forward exp(−ik·r), H는 Z₀H/E_ref다. 실제 코팅 데이터가 없어 명목 Reference의 경계를 두 개의 유한하고 얇은 Ideal PEC screen으로 가정한다. 동일 반사면의 무한 접평면은 편광 및 파일 전달을 시험하는 해석 대조다.

1. 공기 중 각 Fourier order를 Maxwell 평면파로 전파한다. 음의 공간 carrier와 저장 Fourier 양의 지수 사이의 부호 및 셀 중심을 적용한다. 전진 propagating orders만 있는 동결 장에서 H=k̂×E, k̂·E=0, 전후 셀 Flux의 R15 일치를 상대 1e−10 이내로 요구한다. 별도 비축 coherent TE/TM 평면파 합의 해석값과 양수 거리 전파의 E/H를 상대 1e−10 이내에서 비교한다.
2. 평면 PEC는 경계에서 total tangential E=0. 0°, 30°, 60°에서 TE/TM와 복소 혼합 편광의 반사 E/H를 독립 성분 해와 대조한다. 편광 상대오차·법선 Flux 상쇄 상대오차 한계는 각각 1e−10이다. 실패하면 export 중단.
3. 최대 두 접평면을 거친 control 해를 고정 Target에서 읽고 complex128 E_t,E_s,H_t,H_s, 축·중심·법선·격자·면적 가중치·Source power·case 표기를 저장/재로딩한다. 계산 예산은 CPU 1분, control 창 40 µm, 64×64. 이 파일은 주기장·무한평면 대조에 한해 유효하다.
4. 유한 곡면의 nominal route는 편광을 보존하는 surface current 전파 및 독립 reference가 필요하다. R14의 절대 예산 1e−3 중 relay/source 항 2.5e−4를 사용한다. Source 단일 셀→고립장 변환, 유한 PEC current/edge, 전파 수치오차와 잔여항의 제안된 분배는 각각 5e−5, 1e−4, 1e−4다. Target quadrature, Glass 역방출 정규화, 독립 내부 monitor·나머지에 각 2.5e−4. 각 항의 상한이 확보되기 전에는 전달 비율·U·회전 응답은 Uncomputed다.
