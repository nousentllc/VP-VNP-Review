import Anchor

namespace W05.Terminal
/-- At an already feasible inequality, only directional consumption of positive
    slack can cap a nonnegative slot adjustment. -/
theorem row_headroom {u s q : ℝ} (hs : 0 ≤ s) (hq : 0 ≤ q) :
    u*q ≤ s ↔ (0 < u → q ≤ s/u) := by
  by_cases hp : 0 < u
  · rw [imp_iff_right hp,le_div_iff₀ hp,mul_comm q u]
  · have hx := mul_nonpos_of_nonpos_of_nonneg (le_of_not_gt hp) hq
    exact ⟨fun _ h => (hp h).elim,fun _ => hx.trans hs⟩

/-- Measured terminal energy deficit and positive gain p, e.g. η_c Δt for
    increasing charge or Δt/η_d for decreasing discharge. All original rows
    other than the target are residualized in s; row slopes may have any sign. -/
theorem single_slot_iff {I : Type*} (s u : I → ℝ) (hs : ∀ i, 0 ≤ s i)
    (e target p : ℝ) (hp : 0 < p) (he : e ≤ target) :
    (∃ q : ℝ, 0 ≤ q ∧ e+p*q=target ∧ ∀ i, u i*q ≤ s i) ↔
      ∀ i, 0 < u i → (target-e)/p ≤ s i / u i := by
  have hq : 0 ≤ (target-e)/p := div_nonneg (sub_nonneg.mpr he) hp.le
  have hid : e+p*((target-e)/p)=target := by field_simp; ring
  constructor
  · rintro ⟨q,h0,hend,hrow⟩
    have eq : q=(target-e)/p := (eq_div_iff (ne_of_gt hp)).2 (by nlinarith)
    intro i hi
    rw [← eq]
    exact (row_headroom (hs i) h0).1 (hrow i) hi
  · intro h
    exact ⟨_,hq,hid,fun i => (row_headroom (hs i) hq).2 (h i)⟩

/-- A signed target residual permits either increased or decreased power.
    The residual is tested in its directed coordinate before using row_headroom. -/
theorem signed_slot_iff {I : Type*} (s u : I → ℝ) (hs : ∀ i, 0 ≤ s i)
    (e target p : ℝ) (hp : p ≠ 0) (direction : 0 ≤ (target-e)/p) :
    (∃ q : ℝ, 0 ≤ q ∧ e+p*q=target ∧ ∀ i, u i*q ≤ s i) ↔
      ∀ i, 0 < u i → (target-e)/p ≤ s i / u i := by
  have hid : e+p*((target-e)/p)=target := by field_simp; ring
  constructor
  · rintro ⟨q,h0,hend,hrow⟩
    have eq : q=(target-e)/p := (eq_div_iff hp).2 (by nlinarith)
    intro i hi
    rw [← eq]
    exact (row_headroom (hs i) h0).1 (hrow i) hi
  · intro h
    exact ⟨_,direction,hid,fun i => (row_headroom (hs i) direction).2 (h i)⟩

/-- After changing one state increment, every later SOC balance changes
    by the same amount. Times denote the number of elapsed intervals. -/
theorem suffix_shift (initial delta : ℝ) (increment : ℕ → ℝ) (slot t : ℕ) :
    initial + ∑ k ∈ Finset.range t, (increment k + if k=slot then delta else 0) =
      (initial + ∑ k ∈ Finset.range t, increment k) + if slot<t then delta else 0 := by
  simp [Finset.sum_add_distrib,add_assoc]

/-- Adjacent import ramps have opposite effects from one changed power slot. -/
theorem adjacent_ramps (before current after pulse : ℝ) :
    (current+pulse)-before=(current-before)+pulse ∧
    after-(current+pulse)=(after-current)-pulse := by constructor <;> ring

/-- With charging efficiency η and discharging efficiency ρ, a pulse has the
    indicated exact energy gain on the fixed charge/discharge mode trajectory. -/
theorem soc_increment (e eta rho c d dc dd hours : ℝ) :
    (e+hours*(eta*(c+dc)-(d+dd)/rho))-(e+hours*(eta*c-d/rho)) =
    hours*(eta*dc-dd/rho) := by ring

theorem charge_cost (price wear q len : ℝ) :
    price*(q*len) + wear*(q*len) = (price+wear)*len*q := by ring

theorem no_single_slot_can_be_insufficient :
    (¬ ∃ q : ℝ, 0 ≤ q ∧ q ≤ 1 ∧ q = 2) ∧
    ∃ q r : ℝ, 0 ≤ q ∧ q ≤ 1 ∧ 0 ≤ r ∧ r ≤ 1 ∧ q+r=2 := by
  constructor
  · rintro ⟨_,_,h,rfl⟩; norm_num at h
  · exact ⟨1,1,by norm_num,le_rfl,by norm_num,le_rfl,by norm_num⟩

end W05.Terminal
