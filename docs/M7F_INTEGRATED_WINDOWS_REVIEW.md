# M7-F — Integrated Windows Review

M7-D/E의 Background Near-Match·Windows Runtime과 M7-R1/R2의 Mode Library·Reference
탭을 하나의 Two-Port Workspace에서 검토한다. Windows Actions의 `m7f-windows-review-package`
Artifact에서 `Photonic-Architecture-Explorer-M7F-Windows-x64.zip`을 내려받고 전체 압축을
해제한 뒤 `Start-Photonic-Architecture-Explorer.cmd`를 실행한다. 압축 해제 위치에 공백과
한글이 들어간 경우도 CI에서 검사한다.

| 검토 경로 | 합격 조건 |
|---|---|
| Synthetic Example → Design | Frozen 세 사례와 exact 결과 일치. 유효 exact 후보가 있으면 Worker 미실행. |
| SMF–Glass Mode Reference → 1550 nm 개념 Proxy → Design | 문헌 비교는 읽기 전용. Proxy를 명시적으로 열고 Design을 누르면 exact-q 이후 Background Near-Match 수행. |
| Proxy 결과와 Export | 36개 배치의 기존 집계와 독립 검사 재현. Fixed Ports 및 HTML·JSON·A4의 Input SHA와 Candidate ID 일치. |
| 1310 nm Readiness → 검증한 Port 데이터로 새 입력 열기 | Glass Mode 정보가 없으면 Uncomputed. Mode Width와 Curvature가 누락된 1310 nm 입력에서 Worker·후보·Overlap 미표시. |
| 취소·편집·늦은 응답·재시도 | 취소 및 오래된 결과 게시 차단. 동일 Proxy 재시도에서 Input SHA 일치, 새 Job ID. |
| ZIP 무결성 | 추출 Runtime·앱 사용, Source HEAD/Tree와 배포 파일 Inventory 대조. Offline Mode Report 원본과 일치. |

`scripts/check_m7d.cjs`는 Windows ZIP에서 추출한 Python으로 통합 Browser 검사를 실행한다.
같은 검사는 Linux CI에서도 실행한다. 1550 nm Proxy의 Normalized Mode Overlap은 Gaussian
Concept 결과다. 실제 Complex Field 적용성, Assembly Tolerance, Package Yield, Total Coupling은
Uncomputed로 표시한다. 1310 nm 검사의 수치는 입력 차단을 재현하기 위한 Synthetic 값이다.

실제 1310 nm 사례의 검토는 [Port Readiness 지시문](NEXT_TASK.md)을 따른다.
