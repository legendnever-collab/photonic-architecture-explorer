# M2-001 — frozen bounded diagnostic contract

2026-11-09, implementation前に固定。M1 Port/fixture/guardは変更しない。
実物Portデータは未提供: actual-SSC applicability=Uncomputed。
Synthetic external fieldはM1のposition/direction/ambient n=1、1310 nm、
waist radii 8/12 µm、waist phase。Guided effective indexをambientに代用しない。

目的: ideal relayの100% overlapを実機性能と解釈する前に、curvature sensitivityと
finite-footprint ray nonlinearity、placement時のchief-ray missを見えるようにする。

予算: curvatureは各mirror/各principal axisを個別に±1%、計8+nominal。
placementは各mirrorをglobal X/Y/Zに個別に±5 µm、計12+nominal、角度は固定。
各placementのSource chief rayを実際のquadratic patchesに交差させる。
Targetは動かさない。missはGeometry diagnosticとして報告、Gaussian overlapは
Uncomputed（off-vertex powered Gaussian handoff未検証のため）。

Finite-footprint diagnostic: M1直前Gaussian wavefront normal fan。
3x3 grid t/w_t,s/w_s in {-extent,0,+extent}。extent=0.5,1,2の3水準、
各9本、合計27本。Flat/Curvedを比較。Independent linear ray relayとの差を
target planeで測定し、max/RMS transverse residualとangle residualを記録。
Gaussian ray fanはwave fieldやWigner phase-space samplingではなく、power/yieldを
推定しない。Uniform RMSは9本のdiagnostic rayの統計のみ。Diffraction/OPDは未計算。

成功: M1 tests不変、exact rayの面方程式・反射則検証、Flat controlのlinear residual
<1e-10 m、Curved near-axis differentialがlinear referenceに収束、
placementでTargetを動かさずmissを検出、失敗時overlapを生成しない。
Curved finite fan residualに合格性能閾値は設けず、値を報告する。
新たな設計順位やtotal couplingは主張しない。

中断: 1e-9 m以下のsegment、back face、aperture miss、unintended hit、
nonfinite/invalid inputはFail。高NAはM1 guardでFail。実物データ不足はUncomputed。
上記予算を超える探索・新要素・Maxwell・UIは行わない。
