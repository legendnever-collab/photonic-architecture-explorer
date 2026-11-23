# M7-R14 사전 계산 계약

기준 #44 d7385b00131b5288b040a10dc61f562aee557508. 1310 nm, R6의 고정 SMF·Glass Port, R8 확장 처방, 5.023725 mm Envelope 및 Guard를 사용한다. 첫 수치 계산 전에 아래 규약과 중단 조건을 정했다.

- 분모 P_L은 SMF 공기 쪽 +5 µm 외부 Source 평면 (0,0,0)에서 +X로 발사하는 입사 성분의 시간평균 Power다. Source 내부의 guided launch를 분모로 삼으면 다른 지표가 된다. 분자는 Glass 내부 균일 단면에서 선택한 x-polarized fundamental guided mode로 향하는 Power다. 두 공기 평면에서 t=−Z, s=+Y, n=t×s=+X다. Target 중심은 (2,0,2) mm, Facet 바깥 5 µm다. peak phasor exp(+iωt)와 forward carrier exp(−ikd)를 사용한다.
- P=½ Re ∫(E×H*)·n dA. 순방향 입사장 i와 별도의 Glass 역방출 해 r을 같은 Target 공기 평면에 놓는다. P_r>0은 r을 여기한 **내부 guided incident** power의 크기다. 수동 reciprocal Facet, 고립된 lossless guided port, 일관된 모드 위상·단위 및 충분한 적분면을 전제한다. B=∫(E_r×H_i−E_i×H_r)·n dA, P_guided/P_L=|B|²/(16 P_r P_L). r은 켤레하지 않은 역방출장이며 H도 세계 좌표계로 회전한다. 시간 역전된 forward test field를 만드는 경우에만 (E*,−H*)를 쓴다. 단위는 V/m, A/m, m², W 또는 동일 비율을 보존하는 명시적 공통 단위다.
- 양성 대조는 1310 nm 공기 PEC 직사각형 도파관의 단일 TE10 진행파다. 폭 1 µm (s), 높이 0.4 µm (t). 적분과 독립인 해석적 guided power로 정규화해 비율 1을 검사한다. 순방향 동일 진행 방향을 reverse 자리에 넣으면 B=0이다. 별도 air/glass 평면파 경계에서 4n/(1+n)²를 재현해 Facet 투과가 1 미만인 경우의 분모를 검사한다. 복소 진폭·위상, 16/32점 횡격자에서 각 비율의 절대오차 허용치 1e−12.
- 저장 R5 최종 Fourier 장은 좌표 반전과 벡터 회전 후 공기면의 signed flux를 독립 Parseval 적분과 비교한다. 상대 차이 1e−12 이내, 역방출 flux는 음수. 이 대조는 저장된 상대 단위의 Supercell 진단이다.
- 명목 정량값의 제안 수치 예산은 전달 비율 절대오차 1e−3 (연구용 정밀도)다. Target 격자/창/좌표 적분, 역방출·Facet 및 내부 모드 정규화, 입사 Vector relay/Source flux, 독립 guided-port monitor 대조 및 잔여항에 각각 2.5e−4를 배정한다. 합산은 각 항목의 보수적 상한이 있을 때만 유효하다. 실제 성능 합격 기준은 미지정이다.
- 계산 범위는 대조 2종과 저장 파일 점검이다. 필수 벡터 성분, power scale 또는 독립 검증이 부족하면 명목 비율과 U를 Uncomputed로 기록한다. R10 목표는 해당 전체면 지표에만 적용한다. 회전 상태는 명목 검증 후 다룬다.
