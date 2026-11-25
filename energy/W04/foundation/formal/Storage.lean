import Mathlib

/-! Integer storage with ideal unit dynamics. The first r labeled batteries receive
one extra unit. Reversing all labels gives the manuscript's floor convention. -/
namespace W03
open Finset
def lift (N S i : ℕ) : ℕ := S / N + if i < S % N then 1 else 0

theorem lift_total (N S : ℕ) (hn : 0 < N) :
    ∑ i ∈ range N, lift N S i = S := by
  have hf : (range N).filter (fun i => i < S % N) = range (S % N) := by
    ext i
    simp only [mem_filter, mem_range]
    exact ⟨And.right, fun h => ⟨lt_trans h (Nat.mod_lt _ hn), h⟩⟩
  simp only [lift, sum_add_distrib, sum_const, card_range, Nat.nsmul_eq_mul,
    Finset.sum_boole, hf]
  exact (Nat.add_comm _ _).trans (Nat.mod_add_div S N)

theorem lift_mono {N S U : ℕ} (h : S ≤ U) (i : ℕ) : lift N S i ≤ lift N U i := by
  have hq := Nat.div_le_div_right (c := N) h
  by_cases eq : S / N = U / N
  · have hs := Nat.mod_add_div S N
    rw [eq] at hs
    have hu := Nat.mod_add_div U N
    simp only [lift, eq]
    split_ifs <;> omega
  · unfold lift
    split_ifs <;> omega

theorem lift_translate (N S R i : ℕ) (hn : 0 < N) :
    lift N (S + N * R) i = lift N S i + R := by
  simp [lift, Nat.add_mul_div_left _ _ hn, Nat.add_mul_mod_self_left, Nat.add_right_comm]

theorem lift_rate {N S U R : ℕ} (hn : 0 < N) (h : U ≤ S + N * R) (i : ℕ) :
    lift N U i ≤ lift N S i + R := by
  simpa only [lift_translate N S R i hn] using lift_mono (N := N) h i

theorem lift_capacity {N S C : ℕ} (hn : 0 < N) (h : S ≤ N*C) (i : ℕ) :
    lift N S i ≤ C := by
  have h' := lift_rate (S:=0) (U:=S) (R:=C) hn (by simpa using h) i
  simpa [lift] using h'

def movement (N : ℕ) (x y : ℕ → ℕ) : ℤ :=
  ∑ i ∈ range N, |(y i : ℤ) - (x i : ℤ)|

theorem lift_movement {N : ℕ} (hn : 0 < N) (S U : ℕ) :
    movement N (lift N S) (lift N U) = |(U:ℤ) - S| := by
  have ordered : ∀ a b : ℕ, a ≤ b →
      movement N (lift N a) (lift N b) = (b:ℤ) - a := by
    intro a b hab
    unfold movement
    have hp (i : ℕ) : (0:ℤ) ≤ (lift N b i : ℤ) - lift N a i := by
      exact sub_nonneg.mpr (by exact_mod_cast lift_mono hab i)
    simp_rw [abs_of_nonneg (hp _)]
    rw [sum_sub_distrib]
    exact_mod_cast (show (∑ i ∈ range N, (lift N b i : ℤ)) - (∑ i ∈ range N, (lift N a i : ℤ)) =
      (b:ℤ) - a by rw [← Nat.cast_sum, ← Nat.cast_sum, lift_total N b hn, lift_total N a hn])
  rcases le_total S U with h | h
  · rw [ordered S U h, abs_of_nonneg (sub_nonneg.mpr (by exact_mod_cast h))]
  · have rev : movement N (lift N S) (lift N U) = movement N (lift N U) (lift N S) := by
      unfold movement
      apply sum_congr rfl
      intro i _
      exact abs_sub_comm _ _
    rw [rev, ordered U S h, abs_sub_comm, abs_of_nonneg (sub_nonneg.mpr (by exact_mod_cast h))]

/- A hardware or price coupling may be supplied as a predicate on the aggregate
trajectory (and fixed external conditions). All endpoints use one labeling. -/
def total (N : ℕ) (x : ℕ → ℕ → ℕ) (t : ℕ) : ℕ := ∑ i ∈ range N, x t i

theorem total_lift (N : ℕ) (hn : 0 < N) (s : ℕ → ℕ) :
    total N (fun t => lift N (s t)) = s := funext (fun t => lift_total N (s t) hn)

def fullOK (N T C R A B : ℕ) (external : (ℕ → ℕ) → Prop) (x : ℕ → ℕ → ℕ) : Prop :=
  (∀ i < N, x 0 i = lift N A i ∧ x T i = lift N B i) ∧
  (∀ t ≤ T, ∀ i < N, x t i ≤ C) ∧
  (∀ t < T, ∀ i < N, x (t+1) i ≤ x t i + R ∧ x t i ≤ x (t+1) i + R) ∧
  external (total N x)

def aggOK (N T C R A B : ℕ) (external : (ℕ → ℕ) → Prop) (s : ℕ → ℕ) : Prop :=
  (s 0 = A ∧ s T = B) ∧ (∀ t ≤ T, s t ≤ N*C) ∧
  (∀ t < T, s (t+1) ≤ s t + N*R ∧ s t ≤ s (t+1) + N*R) ∧ external s

theorem projection {N T C R A B : ℕ} (hn : 0 < N) {ext x}
    (h : fullOK N T C R A B ext x) : aggOK N T C R A B ext (total N x) := by
  obtain ⟨ep,cap,rate,couple⟩ := h
  have sr (u v : ℕ) (step : ∀ i < N, x v i ≤ x u i + R) :
      total N x v ≤ total N x u + N*R := by
    unfold total
    calc
      _ ≤ ∑ i ∈ range N, (x u i + R) := sum_le_sum (fun i hi => step i (mem_range.mp hi))
      _ = _ := by simp [sum_add_distrib]
  refine ⟨⟨?_,?_⟩,?_,?_,couple⟩
  · rw [← lift_total N A hn]
    exact sum_congr rfl (fun i hi => (ep i (mem_range.mp hi)).1)
  · rw [← lift_total N B hn]
    exact sum_congr rfl (fun i hi => (ep i (mem_range.mp hi)).2)
  · intro t ht
    calc
      total N x t ≤ ∑ _i ∈ range N, C := sum_le_sum (fun i hi => cap t ht i (mem_range.mp hi))
      _ = _ := by simp
  · intro t ht
    exact ⟨sr t (t+1) (fun i hi => (rate t ht i hi).1),
      sr (t+1) t (fun i hi => (rate t ht i hi).2)⟩

theorem reconstruction {N T C R A B : ℕ} (hn : 0 < N) {ext s}
    (h : aggOK N T C R A B ext s) : fullOK N T C R A B ext (fun t => lift N (s t)) := by
  obtain ⟨ep,cap,rate,couple⟩ := h
  refine ⟨fun i _ => ⟨by simp [ep.1], by simp [ep.2]⟩,
    fun t ht i _ => lift_capacity hn (cap t ht) i,
    fun t ht i _ => ⟨lift_rate hn (rate t ht).1 i, lift_rate hn (rate t ht).2 i⟩, ?_⟩
  simpa only [total_lift N hn s] using couple

theorem projected_movement (N : ℕ) (x : ℕ → ℕ → ℕ) (t : ℕ) :
    |(total N x (t+1):ℤ) - (total N x t:ℤ)| ≤ movement N (x t) (x (t+1)) := by
  unfold total movement
  push_cast
  rw [← sum_sub_distrib]
  exact Finset.abs_sum_le_sum_abs _ _

/- Equality of all cost sublevel attainability statements also covers infeasibility.
The external cost may depend on the complete aggregate path. -/
theorem same_threshold {N T C R A B : ℕ} (hn : 0 < N) (ext : (ℕ → ℕ) → Prop)
    (fee : (ℕ → ℕ) → ℤ) (k b : ℤ) (hk : 0 ≤ k) :
    (∃ x, fullOK N T C R A B ext x ∧ fee (total N x) +
       k * (∑ t ∈ range T, movement N (x t) (x (t+1))) ≤ b) ↔
    (∃ s, aggOK N T C R A B ext s ∧ fee s +
       k * (∑ t ∈ range T, |(s (t+1):ℤ) - s t|) ≤ b) := by
  constructor
  · rintro ⟨x,h,hb⟩
    exact ⟨total N x, projection hn h, le_trans (add_le_add_right
      (mul_le_mul_of_nonneg_left (sum_le_sum (fun t _ => projected_movement N x t)) hk) _) hb⟩
  · rintro ⟨s,h,hb⟩
    refine ⟨fun t => lift N (s t), reconstruction hn h, ?_⟩
    simpa only [total_lift N hn s,lift_movement hn] using hb

theorem same_threshold_real {N T C R A B : ℕ} (hn : 0 < N) (ext : (ℕ → ℕ) → Prop)
    (fee : (ℕ → ℕ) → ℝ) (k b : ℝ) (hk : 0 ≤ k) :
    (∃ x, fullOK N T C R A B ext x ∧ fee (total N x) +
       k * ((∑ t ∈ range T, movement N (x t) (x (t+1)) : ℤ) : ℝ) ≤ b) ↔
    (∃ s, aggOK N T C R A B ext s ∧ fee s +
       k * ((∑ t ∈ range T, |(s (t+1):ℤ) - s t| : ℤ) : ℝ) ≤ b) := by
  constructor
  · rintro ⟨x,h,hb⟩
    have ht := sum_le_sum (s := range T) (fun t _ => projected_movement N x t)
    exact ⟨total N x, projection hn h, le_trans (add_le_add_right
      (mul_le_mul_of_nonneg_left (by exact_mod_cast ht) hk) _) hb⟩
  · rintro ⟨s,h,hb⟩
    refine ⟨fun t => lift N (s t), reconstruction hn h, ?_⟩
    simpa only [total_lift N hn s,lift_movement hn] using hb

theorem cyclic_zero (ri rj c d : ℝ) (diff : ri ≠ rj)
    (hi : ri*c = d) (hj : rj*c = d) : c = 0 ∧ d = 0 := by
  have h : (ri-rj)*c=0 := by linear_combination hi - hj
  have hc := (mul_eq_zero.mp h).resolve_left (sub_ne_zero.mpr diff)
  exact ⟨hc, by simpa [hc] using hi.symm⟩

theorem terminal_bound (ri rj c d ei ej : ℝ) (hc : 0 ≤ c)
    (hi : |ri*c-d| ≤ ei) (hj : |rj*c-d| ≤ ej) : |ri-rj| * c ≤ ei+ej := by
  calc
    |ri-rj| * c = |(ri*c-d)-(rj*c-d)| := by rw [show (ri*c-d)-(rj*c-d) = (ri-rj)*c by ring, abs_mul, abs_of_nonneg hc]
    _ ≤ |ri*c-d| + |rj*c-d| := abs_sub _ _
    _ ≤ ei+ej := add_le_add hi hj
/-- One-hour AC-side proportional dynamics, using a positive discharge efficiency
to clear the denominator and a positive asset weight to recover class totals. -/
theorem storage_residual (T : ℕ) (soc c d : ℕ → ℝ) (ec ed w : ℝ)
    (hw : 0 < w)
    (dyn : ∀ t < T, ed * (soc (t+1) - soc t) = w*(ec*ed*c t-d t)) :
    ec*ed*(∑ t ∈ range T, c t) - (∑ t ∈ range T, d t) =
      ed*(soc T - soc 0)/w := by
  apply (eq_div_iff (ne_of_gt hw)).mpr
  have hs := sum_congr (s₁ := range T) (s₂ := range T) rfl
    (fun t ht => dyn t (mem_range.mp ht))
  rw [← mul_sum, ← mul_sum, sum_range_sub, sum_sub_distrib, ← mul_sum] at hs
  linear_combination -hs

theorem cyclic_totals (T : ℕ) (s c d : ℕ → ℝ) (ec ed w : ℝ)
    (hw : 0 < w) (ends : s T = s 0)
    (dyn : ∀ t < T, ed*(s (t+1)-s t) = w*(ec*ed*c t-d t)) :
    ec*ed*(∑ t ∈ range T, c t) = ∑ t ∈ range T, d t := by
  have h := storage_residual T s c d ec ed w hw dyn
  rw [ends] at h
  simpa using sub_eq_zero.mp (by simpa using h : ec*ed*(∑ t ∈ range T, c t) - (∑ t ∈ range T, d t) = 0)

theorem terminal_residual (T : ℕ) (s c d : ℕ → ℝ) (ec ed w δ : ℝ)
    (hw : 0 < w) (he : 0 < ed) (ends : |s T-s 0| ≤ δ)
    (dyn : ∀ t < T, ed*(s (t+1)-s t) = w*(ec*ed*c t-d t)) :
    |ec*ed*(∑ t ∈ range T, c t)-(∑ t ∈ range T, d t)| ≤ ed*δ/w := by
  rw [storage_residual T s c d ec ed w hw dyn, abs_div, abs_mul, abs_of_pos hw, abs_of_pos he]
  exact div_le_div_of_nonneg_right (mul_le_mul_of_nonneg_left ends he.le) hw.le

theorem each_zero {T : ℕ} (c : ℕ → ℝ) (nonneg : ∀ t < T, 0 ≤ c t)
    (totalZero : ∑ t ∈ range T, c t = 0) : ∀ t < T, c t = 0 := by
  intro t ht
  exact (Finset.sum_eq_zero_iff_of_nonneg (fun i hi => nonneg i (mem_range.mp hi))).mp
    totalZero t (mem_range.mpr ht)
theorem no_common_cycles (T : ℕ) (s₁ s₂ c d : ℕ → ℝ) (a b e f w v : ℝ)
    (hw : 0<w) (hv : 0<v) (diff : a*b ≠ e*f)
    (ep₁ : s₁ T = s₁ 0) (ep₂ : s₂ T = s₂ 0)
    (d₁ : ∀ t<T, b*(s₁ (t+1)-s₁ t) = w*(a*b*c t-d t))
    (d₂ : ∀ t<T, f*(s₂ (t+1)-s₂ t) = v*(e*f*c t-d t))
    (hc : ∀ t<T, 0 ≤ c t) (hd : ∀ t<T, 0 ≤ d t) :
    ∀ t<T, c t = 0 ∧ d t = 0 := by
  have h := cyclic_zero _ _ _ _ diff (cyclic_totals T s₁ c d a b w hw ep₁ d₁)
    (cyclic_totals T s₂ c d e f v hv ep₂ d₂)
  exact fun t ht => ⟨each_zero c hc h.1 t ht, each_zero d hd h.2 t ht⟩

theorem two_device_bound (T : ℕ) (s₁ s₂ c d : ℕ → ℝ) (a b e f w v δ γ : ℝ)
    (hw : 0<w) (hv : 0<v) (hb : 0<b) (hf : 0<f) (hc : ∀ t<T, 0 ≤ c t)
    (ep₁ : |s₁ T-s₁ 0| ≤ δ) (ep₂ : |s₂ T-s₂ 0| ≤ γ)
    (d₁ : ∀ t<T, b*(s₁ (t+1)-s₁ t) = w*(a*b*c t-d t))
    (d₂ : ∀ t<T, f*(s₂ (t+1)-s₂ t) = v*(e*f*c t-d t)) :
    |a*b-e*f| * (∑ t ∈ range T, c t) ≤ b*δ/w + f*γ/v := by
  exact terminal_bound _ _ _ _ _ _ (sum_nonneg (fun t ht => hc t (mem_range.mp ht)))
    (terminal_residual T s₁ c d a b w δ hw hb ep₁ d₁)
    (terminal_residual T s₂ c d e f v γ hv hf ep₂ d₂)

def certificate (x y price rent : ℚ) : Bool := decide
  (0 ≤ x ∧ x ≤ 60 ∧ 0 ≤ y ∧ x+y=100 ∧ 0 ≤ rent ∧ price-rent ≤ 20 ∧ price ≤ 50 ∧
   20*x+50*y=100*price-60*rent)
example : certificate 60 40 50 30 = true := by norm_num [certificate]
example : certificate 61 39 50 30 = false := by norm_num [certificate]
example : certificate 60 40 51 30 = false := by norm_num [certificate]
example : certificate 60 40 50 29 = false := by norm_num [certificate]
example : certificate 60 39 50 30 = false := by norm_num [certificate]
end W03
#print axioms W03.lift_total
#print axioms W03.lift_rate
#print axioms W03.lift_capacity
#print axioms W03.lift_movement
#print axioms W03.projection
#print axioms W03.reconstruction
#print axioms W03.same_threshold
#print axioms W03.cyclic_zero
#print axioms W03.terminal_bound

#print axioms W03.storage_residual
#print axioms W03.cyclic_totals
#print axioms W03.terminal_residual
#print axioms W03.each_zero

#print axioms W03.no_common_cycles
#print axioms W03.two_device_bound

#print axioms W03.same_threshold_real
