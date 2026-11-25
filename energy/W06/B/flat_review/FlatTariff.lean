import Mathlib.Data.Real.Archimedean
import Mathlib.Data.List.Forall2
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring
import Mathlib.Tactic.NormNum

namespace W06.Flat

def ramps (r prev : ℝ) : List ℝ → Prop
  | [] => True
  | a :: rest => a ≤ prev+r ∧ ramps r a rest

def internalRamps (r : ℝ) : List ℝ → Prop
  | [] => True
  | a :: rest => ramps r a rest

noncomputable def pass (r prev : ℝ) : List ℝ → List ℝ
  | [] => []
  | a :: rest => min a (prev+r) :: pass r (min a (prev+r)) rest

noncomputable def boundaryFree (r : ℝ) : List ℝ → List ℝ
  | [] => []
  | a :: rest => a :: pass r a rest

theorem propagate {r : ℝ} {grid cap : List ℝ} (h : List.Forall₂ (· ≤ ·) grid cap)
    (prev bound : ℝ) (hp : prev ≤ bound) (hg : ramps r prev grid) :
    List.Forall₂ (· ≤ ·) grid (pass r bound cap) := by
  induction h generalizing prev bound with
  | nil => exact .nil
  | cons h hd ih =>
    have hx := le_min h (le_trans hg.1 (show prev+r ≤ bound+r by linarith))
    exact .cons hx (ih _ _ hx hg.2)

theorem backwardPass {r : ℝ} {grid cap : List ℝ} (h : List.Forall₂ (· ≤ ·) grid cap)
    (hg : internalRamps r grid) : List.Forall₂ (· ≤ ·) grid (boundaryFree r cap) := by
  cases h with
  | nil => exact .nil
  | cons hx hd => exact .cons hx (propagate hd _ _ hx hg)

theorem rampEnvelope (r prev : ℝ) (grid cap : List ℝ)
    (box : List.Forall₂ (· ≤ ·) grid cap) (forward : ramps r prev grid)
    (backward : internalRamps r grid.reverse) :
    List.Forall₂ (· ≤ ·) grid ((boundaryFree r (pass r prev cap).reverse).reverse) := by
  have f := propagate box prev prev (le_refl _) forward
  have b := backwardPass (List.rel_reverse f) backward
  simpa using List.rel_reverse b

theorem initialCap (g y charge discharge power cap : ℝ)
    (balance : g = y+charge-discharge) (hc : charge ≤ power)
    (hd : 0 ≤ discharge) (hg : g ≤ cap) : g ≤ min cap (y+power) :=
  le_min hg (by linarith)

theorem forcedDischarge {I : Type*} [Fintype I] (g y charge discharge envelope : I → ℝ)
    (balance : ∀ i, g i = y i + charge i - discharge i)
    (hc : ∀ i, 0 ≤ charge i) (hd : ∀ i, 0 ≤ discharge i)
    (hg : ∀ i, g i ≤ envelope i) :
    (∑ i, max 0 (y i-envelope i)) ≤ ∑ i, discharge i := by
  apply Finset.sum_le_sum
  intro i _
  apply max_le (hd i)
  have := balance i
  have := hc i
  have := hg i
  linarith

/-- e is stored/charged MWh, b is drawn/delivered MWh, C,D are AC MWh. -/
theorem tariffIdentity (p w v e b Y C D S₀ S : ℝ) (he : e ≠ 0)
    (stock : S = S₀+e*C-b*D) :
    p*(Y+C-D)+w*(C+D)-v*S =
    p*Y-v*S₀+((p+w)/e-v)*(S-S₀)+((p+w)*b/e+w-p)*D := by
  rw [stock]
  field_simp
  ring

theorem tariffSigns (p w v e b : ℝ) (hp : 0 ≤ p) (hw : 0 ≤ w)
    (he : 0 < e) (eta : e ≤ 1) (draw : 1 ≤ b) (hv : v*e ≤ p+w) :
    0 ≤ (p+w)/e-v ∧ 0 ≤ (p+w)*b/e+w-p := by
  constructor
  · exact sub_nonneg.mpr ((le_div_iff₀ he).mpr hv)
  · have hbase : 0 ≤ p+w := by linarith
    have hle := mul_le_mul_of_nonneg_left (le_trans eta draw) hbase
    have hdiv : p+w ≤ (p+w)*b/e := (le_div_iff₀ he).mpr hle
    linarith

/-- An upper bound on improvement against a feasible chronological baseline.
    The common offset K contains total served consumption and the opening stock. -/
theorem flatCap (J₀ J K ks kd S₀ SB S D₀ DB D floor : ℝ)
    (base : J₀ = K+ks*(SB-S₀)+kd*DB) (alt : J = K+ks*(S-S₀)+kd*D)
    (hs : 0 ≤ ks) (hd : 0 ≤ kd) (stock : floor ≤ S) (dis : D₀ ≤ D) :
    J₀-J ≤ ks*(SB-floor)+kd*(DB-D₀) := by
  have m := mul_le_mul_of_nonneg_left stock hs
  have n := mul_le_mul_of_nonneg_left dis hd
  linarith

theorem fixedStockStop (J₀ J K ks kd S₀ S DB D : ℝ)
    (base : J₀ = K+ks*(S-S₀)+kd*DB) (alt : J = K+ks*(S-S₀)+kd*D)
    (hd : 0 ≤ kd) (dis : DB ≤ D) : J₀-J ≤ 0 := by
  have := mul_le_mul_of_nonneg_left dis hd
  linarith

theorem creditReversal : (50+10)/(1:ℝ)-100 < 0 := by norm_num

theorem negativePriceReversal : ((-100:ℝ)+10)*2/1+10-(-100) < 0 := by norm_num

/-- Same throughput and final inventory can cost different amounts when charge timing is priced. -/
theorem variablePriceCounterexample : (1:ℝ)*0+0*100 < 0*0+1*100 := by norm_num

end W06.Flat
