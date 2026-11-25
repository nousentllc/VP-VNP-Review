import AIPC
import Storage

/-! A concrete instance of the two cost maps. Everything below reuses the
W03 storage model, including label-compatible endpoints and aggregate-only
external constraints. Each reconstructed point carries its feasibility proof. -/
namespace W04.StorageContract
open Finset
variable {N T C R A B : ℕ} {ext : (ℕ → ℕ) → Prop}
abbrev Full (N T C R A B : ℕ) (ext : (ℕ → ℕ) → Prop) :=
  {x // W03.fullOK N T C R A B ext x}
abbrev Reduced (N T C R A B : ℕ) (ext : (ℕ → ℕ) → Prop) :=
  {s // W03.aggOK N T C R A B ext s}

def project (hn : 0 < N) (x : Full N T C R A B ext) : Reduced N T C R A B ext :=
  ⟨W03.total N x.val, W03.projection hn x.property⟩

def recover (hn : 0 < N) (s : Reduced N T C R A B ext) : Full N T C R A B ext :=
  ⟨fun t => W03.lift N (s.val t), W03.reconstruction hn s.property⟩

noncomputable def fullCost (fee : (ℕ → ℕ) → ℝ) (k : ℝ) (x : Full N T C R A B ext) :=
  fee (W03.total N x.val) + k * ((∑ t ∈ range T, W03.movement N (x.val t) (x.val (t+1)) : ℤ) : ℝ)

noncomputable def reducedCost (fee : (ℕ → ℕ) → ℝ) (k : ℝ) (s : Reduced N T C R A B ext) :=
  fee s.val + k * ((∑ t ∈ range T, |(s.val (t+1):ℤ) - s.val t| : ℤ) : ℝ)

theorem projection_bound (hn : 0 < N) (fee : (ℕ → ℕ) → ℝ) (k : ℝ) (hk : 0 ≤ k)
    (x : Full N T C R A B ext) : reducedCost fee k (project hn x) ≤ fullCost fee k x := by
  have ht := sum_le_sum (s := range T) (fun t _ => W03.projected_movement N x.val t)
  exact add_le_add_right (mul_le_mul_of_nonneg_left (by exact_mod_cast ht) hk) _

theorem recovery_cost (hn : 0 < N) (fee : (ℕ → ℕ) → ℝ) (k : ℝ)
    (s : Reduced N T C R A B ext) : fullCost fee k (recover hn s) = reducedCost fee k s := by
  simp only [fullCost,recover,reducedCost,W03.lift_movement hn,W03.total_lift N hn s.val]

theorem threshold_from_contract (hn : 0 < N) (fee : (ℕ → ℕ) → ℝ) (k : ℝ) (hk : 0 ≤ k)
    (b : ℝ) : AtMost (fullCost (N:=N) (T:=T) (C:=C) (R:=R) (A:=A) (B:=B) (ext:=ext) fee k) b ↔
      AtMost (reducedCost (N:=N) (T:=T) (C:=C) (R:=R) (A:=A) (B:=B) (ext:=ext) fee k) b :=
  threshold_iff (project hn) (recover hn) (projection_bound hn fee k hk)
    (fun s => (recovery_cost hn fee k s).le) b
end W04.StorageContract
