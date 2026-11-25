import COA

namespace W06.Closing

/-- Under a constant inventory credit, intermediate valuations cancel on a continuous path. -/
theorem telescope (stock : ℕ → ℝ) (v : ℝ) (n : ℕ) :
    (∑ t ∈ Finset.range n, v*(stock (t+1)-stock t)) = v*(stock n-stock 0) := by
  induction n with
  | zero => simp
  | succ n ih => rw [Finset.sum_range_succ, ih]; ring

/-- With a common opening position and both closing positions in one box, only
    the terminal valuation component obeys this bound without a repair hypothesis. -/
theorem creditDifference (s₀ sT qT lo hi v days : ℝ)
    (hs : sT ≤ hi) (hq : lo ≤ qT) (hv : 0 ≤ v) (hd : 0 < days) :
    (v*(sT-s₀) - v*(qT-s₀))/days ≤ v*(hi-lo)/days := by
  apply div_le_div_of_nonneg_right _ hd.le
  have := mul_le_mul_of_nonneg_left (sub_le_sub hs hq) hv
  linarith

/-- If every weaker-contract schedule has a stronger-contract repair at additional
    same-horizon cost ≤ K, the difference of infima is ≤ K, even without minimizers. -/
theorem terminalPremium {P : Type*} (weak strong : Set P) (J : P → ℝ)
    (base : P) (hb : base ∈ strong) (included : strong ⊆ weak)
    (K l : ℝ) (lower : ∀ p ∈ weak, l ≤ J p)
    (repair : ∀ p ∈ weak, ∃ q ∈ strong, J q ≤ J p + K) :
    0 ≤ sInf (values strong J) - sInf (values weak J) ∧
      sInf (values strong J) - sInf (values weak J) ≤ K := by
  have a : J base ∈ values strong J := ⟨base,hb,rfl⟩
  have m : values strong J ⊆ values weak J := Set.image_mono included
  have bw : BddBelow (values weak J) := ⟨l, by rintro _ ⟨p,hp,rfl⟩; exact lower p hp⟩
  have bs := bw.mono m
  have small := csInf_le_csInf bw (show (values strong J).Nonempty from ⟨_,a⟩) m
  have large : sInf (values strong J) - K ≤ sInf (values weak J) := by
    apply le_csInf ⟨_,m a⟩
    rintro _ ⟨p,hp,rfl⟩
    obtain ⟨q,hq,cost⟩ := repair p hp
    have := csInf_le bs (show J q ∈ values strong J from ⟨q,hq,rfl⟩)
    linarith
  exact ⟨by linarith, by linarith⟩

/-- One extra required terminal unit may have arbitrarily high replacement price. -/
theorem noCapacityOnlyMoneyBound (claimed : ℝ) :
    ∃ price : ℝ, 0 ≤ price ∧ claimed < price * (1-0) := by
  refine ⟨max claimed 0 + 1, by positivity, ?_⟩
  have := le_max_left claimed (0:ℝ)
  linarith

end W06.Closing
