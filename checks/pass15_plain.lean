/-
Portions adapted from NS1/Accel.lean and Paper/Postpone.lean in the pinned
publisher release. Copyright (c) 2026 Anthropic, PBC. Apache-2.0,
see primary/vp-vnp/LICENSE and primary/vp-vnp/NOTICE.
-/
import Paper.NoAcc

namespace Review.Pass15

open NS1 Paper

variable {A R : Type} [CommRing A] [CommRing R] [Algebra A R]
variable {θ : List Bool → A}

theorem bill_lt_cost {F : Fm} {x : Tree} {l : List (Run A)} (h : Ev θ F x l) : ∀ r ∈ l, r.bill.length < r.cost := by
  induction h with
  | quote c x => simp [Run.det]
  | id x => simp [Run.det]
  | hd _ ih =>
    simp only [List.mem_map, forall_exists_index, and_imp, forall_apply_eq_imp_iff₂, Run.tick]
    exact fun r hr => (ih r hr).trans (Nat.lt_succ_self _)
  | tl _ ih =>
    simp only [List.mem_map, forall_exists_index, and_imp, forall_apply_eq_imp_iff₂, Run.tick]
    exact fun r hr => (ih r hr).trans (Nat.lt_succ_self _)
  | cons _ _ iha ihb =>
    intro r hr
    simp only [List.mem_flatMap, List.mem_map] at hr
    obtain ⟨r1, h1, r2, h2, rfl⟩ := hr
    have := iha r1 h1
    have := ihb r2 h2
    simp only [Run.tick, Run.seq, List.length_append]
    omega
  | ite _ _ _ iha ihb ihc =>
    intro r hr
    simp only [List.mem_flatMap, List.mem_map] at hr
    obtain ⟨r1, h1, r2, h2, rfl⟩ := hr
    have := iha r1 h1
    have : r2.bill.length < r2.cost := by
      by_cases h : r1.out = .nil
      · exact ihc r1 h1 h r2 h2
      · exact ihb r1 h1 h r2 h2
    simp only [Run.tick, Run.seq, List.length_append]
    omega
  | run _ _ _ iha ihb ih =>
    intro r hr
    simp only [List.mem_flatMap, List.mem_map] at hr
    obtain ⟨r1, h1, r2, h2, r3, h3, rfl⟩ := hr
    have := iha r1 h1
    have := ihb r2 h2
    have := ih r1 h1 r2 h2 r3 h3
    simp only [Run.tick, Run.seq, List.length_append]
    omega
  | guess x => simp [Run.det]
  | fail x => simp
  | theta _ ih =>
    simp only [List.mem_map, forall_exists_index, and_imp, forall_apply_eq_imp_iff₂]
    exact fun r hr => (ih r hr).trans (Nat.lt_succ_self _)
  | mul _ ih =>
    simp only [List.mem_map, forall_exists_index, and_imp, forall_apply_eq_imp_iff₂, List.length_append,
      List.length_singleton]
    exact fun r hr => Nat.succ_lt_succ (ih r hr)

/- Same four conclusions as K.4, at the closed time endpoint. -/
theorem postpone_endpoint (p z : Tree) {T J : ℕ} (hJ : T ≤ 2 ^ J) (hh : Hl θ (Fm.ofTree p) z)
    (hc : ∀ r ∈ evl θ (Fm.ofTree p) z, r.cost ≤ T) (L : KT R) (κ : List Bool → R)
    (hκ : ∀ r ∈ evl θ (Fm.ofTree p) z, ∀ n ∈ r.bill, κ n = L.lookup n) :
    val κ (evl θ (Fm.ofTree p) z) = ((L.budg J).map fun e => e.2 * algebraMap A R (pv θ (postponed p z e.1))).sum ∧
      ∀ e ∈ L.budg J,
        Plain θ ((1000 + 100 * (L.ht + J + 1)) * T + 40 * (L.nds * (J + 1)) + 40) (postponed p z e.1) ∧
        (postponed p z e.1).size ≤ WF.code.size + p.size + z.size + 4 * (L.nds * (J + 1)) + 3 ∧
        pv θ (postponed p z e.1) = ((evl θ (Fm.ofTree p) z).map fun r => if ok e.1 r.bill = true then r.th else 0).sum ∧
        (evl θ (Fm.ofTree (postponed p z e.1).hd) (postponed p z e.1).tl).map Run.th =
          ((evl θ (Fm.ofTree p) z).filter fun r => ok e.1 r.bill).map Run.th := by
  have hp : ∀ e ∈ L.budg J, Plain θ ((1000 + 100 * (L.ht + J + 1)) * T + 40 * (L.nds * (J + 1)) + 40) (zq p z e.1) ∧
      pv θ (zq p z e.1) = ((evl θ (Fm.ofTree p) z).map fun r => if ok e.1 r.bill = true then r.th else 0).sum ∧
      (evl θ (Fm.ofTree (zq p z e.1).hd) (zq p z e.1).tl).map Run.th =
        ((evl θ (Fm.ofTree p) z).filter fun r => ok e.1 r.bill).map Run.th :=
    fun e he => zq_plain hh.ev hc (KT.ht_budg he) (by
      have := Nat.mul_le_mul_left 40 (KT.nds_budg he)
      unfold MM
      omega)
  refine ⟨?_, fun e he => ⟨(hp e he).1, ?_, (hp e he).2⟩⟩
  · rw [val_eq_sum_budg (J := J) (K := L) (fun r hr => ((bill_lt_cost hh.ev r hr).trans_le (hc r hr)).trans_le hJ) hκ]
    refine congrArg List.sum (List.map_congr_left fun e he => ?_)
    rw [← (hp e he).2.1]
    rfl
  · have h1 := Bt.size_enc e.1
    have h2 := KT.nds_budg he
    simp only [postponed, zq, Tree.size]
    omega

/- Independent interface lemma. A structural size bound and a time allowance
   permit a hypothetical accelerator to evaluate every postponed component.
   The evaluator's value contract is invoked only on the plain instance
   delivered by K.4. There is no accelerator hypothesis on the original input. -/
theorem postponed_accelerator_sum (p z : Tree) {T J H v t B : ℕ}
    (L K : KT R) (κ : List Bool → R) (D : Tree)
    (room : T < 2 ^ J) (halt : Hl θ (Fm.ofTree p) z)
    (cost : ∀ r ∈ evl θ (Fm.ofTree p) z, r.cost ≤ T)
    (names : ∀ r ∈ evl θ (Fm.ofTree p) z, ∀ n ∈ r.bill, κ n = L.lookup n)
    (timeRoom : (1000 + 100 * (L.ht + J + 1)) * T + 40 * (L.nds * (J + 1)) + 40 ≤ v ^ H)
    (sizeRoom : WF.code.size + p.size + z.size + 4 * (L.nds * (J + 1)) + 3 ≤ v ^ (H - 32))
    (acc : IsAccT θ H v t K B D) :
    val κ (evl θ (Fm.ofTree p) z) =
      ((L.budg J).map fun e => e.2 * val K.lk (evl θ (Fm.ofTree D) (postponed p z e.1))).sum := by
  obtain ⟨expand, parts⟩ := lem_postpone p z room halt cost L κ names
  rw [expand]
  apply congrArg List.sum
  apply List.map_congr_left
  intro e he
  obtain ⟨plain, size, _⟩ := parts e he
  rw [acc.val _ (size.trans sizeRoom) (Plain.of_le plain timeRoom)]

/-- One accepting computation halts in two steps and records the empty word
    as a name. A singleton bill containing the empty word is not the empty bill. -/
theorem fast_named_input (θ : List Bool → A) :
    ∃ z : Tree, Hl θ (Fm.ofTree z.hd) z.tl ∧
      (∀ r ∈ evl θ (Fm.ofTree z.hd) z.tl, r.cost ≤ 2) ∧ ∀ t, ¬ Plain θ t z := by
  let F := Fm.mul (.quote .nil)
  let r : Run A := ⟨2, 1, [[]], .nil⟩
  have ev : Ev θ F .nil [r] := Ev.mul (Ev.quote .nil .nil)
  refine ⟨.cons F.code .nil, ?_⟩
  simp only [Tree.hd, Tree.tl, Fm.ofTree_code]
  refine ⟨ev.hl, ?_, ?_⟩
  · rw [ev.evl]
    simp [r]
  · intro t plain
    have member : r ∈ evl θ (Fm.ofTree (Tree.cons F.code .nil).hd) (Tree.cons F.code .nil).tl := by
      simp [Tree.hd, Tree.tl, Fm.ofTree_code, ev.evl]
    have impossible : ([[]] : List (List Bool)) = [] := (plain.2 r member).1
    cases impossible

/-- Nested name instructions request the same empty word on every step
    after the initial quote. This family attains the one-step overhead. -/
def requestEmpty : ℕ → Fm
  | 0 => .quote .nil
  | n + 1 => .mul (requestEmpty n)

theorem requestEmpty_ev (θ : List Bool → A) (n : ℕ) :
    Ev θ (requestEmpty n) .nil [⟨n + 1, 1, List.replicate n [], .nil⟩] := by
  induction n with
  | zero => exact Ev.quote .nil .nil
  | succ n ih =>
    have step := Ev.mul ih
    simpa only [requestEmpty, List.map_cons, List.map_nil, Tree.path, List.replicate_succ',
      Nat.succ_eq_add_one] using step

end Review.Pass15

#check @Paper.lem_postpone
#check @Paper.prop_next_round
#check @Paper.prop_next
#check @Paper.thm_noacc_finite_field
#check @Paper.thm_noacc_periodic
#check @Paper.thm_noacc_all_scales
#check @Paper.thm_noacc_diagonal
#check @Paper.thm_noacc
#check @Review.Pass15.postponed_accelerator_sum
#print axioms Paper.lem_postpone
#print axioms Paper.prop_next_round
#print axioms Paper.prop_next
#print axioms Paper.thm_noacc_finite_field
#print axioms Paper.thm_noacc_periodic
#print axioms Paper.thm_noacc_all_scales
#print axioms Paper.thm_noacc_diagonal
#print axioms Paper.thm_noacc
#print axioms Review.Pass15.postponed_accelerator_sum
#check @Review.Pass15.fast_named_input
#print axioms Review.Pass15.fast_named_input
#check @Review.Pass15.bill_lt_cost
#print axioms Review.Pass15.bill_lt_cost
#check @Review.Pass15.postpone_endpoint
#print axioms Review.Pass15.postpone_endpoint
#check @Review.Pass15.requestEmpty_ev
#print axioms Review.Pass15.requestEmpty_ev
