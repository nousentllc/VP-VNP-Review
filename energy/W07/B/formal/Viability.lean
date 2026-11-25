import Mathlib.Data.Nat.Basic

namespace W07.Game

/-- n is the number of periods left after the current step. State is observed before
the nominal action and must contain the history needed by the contract. -/
structure Contract (X A R U D : Type) where
  terminal : Nat → X → Prop
  nominal : Nat → X → A → Prop
  call : Nat → X → Nat → A → R → Prop
  reply : Nat → X → A → R → U → Prop
  disturb : Nat → X → A → R → U → D → Prop
  legal : Nat → X → A → R → U → D → Prop
  next : Nat → X → A → R → U → D → X
  budget : Nat → Nat → R → Nat

variable {X A R U D : Type}

def Kernel (g : Contract X A R U D) : Nat → Nat → X → Prop
  | 0,b,x => g.terminal b x
  | n+1,b,x => ∃ a, g.nominal n x a ∧
      ∀ r, g.call n x b a r → ∃ u, g.reply n x a r u ∧
        ∀ d, g.disturb n x a r u d → g.legal n x a r u d ∧
          Kernel g n (g.budget n b r) (g.next n x a r u d)

/-- Each controller commits one nominal value, observes the call, commits a reply,
then selects a continuation using the public call and the observed successor state.
Two disturbances with an identical observed successor cannot select different continuations. -/
def Plan (X A R U : Type) : Nat → Type _
  | 0 => Unit
  | n+1 => A × (R → U) × (R → X → Plan X A R U n)

def Safe (g : Contract X A R U D) : (n : Nat) → Nat → X → Plan X A R U n → Prop
  | 0,b,x,_ => g.terminal b x
  | n+1,b,x,p => g.nominal n x p.1 ∧ ∀ r, g.call n x b p.1 r →
    g.reply n x p.1 r (p.2.1 r) ∧ ∀ d, g.disturb n x p.1 r (p.2.1 r) d →
    g.legal n x p.1 r (p.2.1 r) d ∧
    Safe g n (g.budget n b r) (g.next n x p.1 r (p.2.1 r) d)
      (p.2.2 r (g.next n x p.1 r (p.2.1 r) d))

def defaultPlan [Inhabited A] [Inhabited U] : (n : Nat) → Plan X A R U n
  | 0 => ()
  | n+1 => (default, fun _ => default, fun _ _ => defaultPlan n)

theorem strategy_to_kernel (g : Contract X A R U D) (n b : Nat) (x : X)
    (p : Plan X A R U n) (h : Safe g n b x p) : Kernel g n b x := by
  induction n generalizing b x with
  | zero => exact h
  | succ n ih =>
    refine ⟨p.1,h.1,?_⟩
    intro r hr
    obtain ⟨hu,hd⟩ := h.2 r hr
    exact ⟨p.2.1 r,hu,fun d how => ⟨(hd d how).1,ih _ _ _ (hd d how).2⟩⟩

theorem kernel_to_strategy [Inhabited A] [Inhabited U] (g : Contract X A R U D)
    (n b : Nat) (x : X) (h : Kernel g n b x) : ∃ p, Safe g n b x p := by
  classical
  induction n generalizing b x with
  | zero => exact ⟨(),h⟩
  | succ n ih =>
    obtain ⟨a,ha,hr⟩ := h
    let u := fun r => if hh : g.call n x b a r then (hr r hh).choose else default
    have hu (r) (hh : g.call n x b a r) : g.reply n x a r (u r) ∧
        ∀ d, g.disturb n x a r (u r) d → g.legal n x a r (u r) d ∧
          Kernel g n (g.budget n b r) (g.next n x a r (u r) d) := by
      simpa [u,hh] using (hr r hh).choose_spec
    let child := fun r y =>
      if hq : ∃ q, Safe g n (g.budget n b r) y q then hq.choose
      else defaultPlan (X := X) (A := A) (R := R) (U := U) n
    refine ⟨(a,u,child),ha,?_⟩
    intro r hh
    refine ⟨(hu r hh).1,?_⟩
    intro d hd
    obtain ⟨safe,viable⟩ := (hu r hh).2 d hd
    refine ⟨safe,?_⟩
    have existsChild := ih _ _ viable
    simpa [child,existsChild] using existsChild.choose_spec

theorem causal_equivalence [Inhabited A] [Inhabited U] (g : Contract X A R U D)
    (n b : Nat) (x : X) : Kernel g n b x ↔ ∃ p, Safe g n b x p :=
  ⟨kernel_to_strategy g n b x, fun ⟨p,h⟩ => strategy_to_kernel g n b x p h⟩

/-- Terminal sets may themselves shrink. Common response, disturbance, transition
and legality fields are enforced by the type, and ordered successor budgets by stepMono. -/
theorem budget_shrink (g : Contract X A R U D)
    (endMono : ∀ lo hi x, lo ≤ hi → g.terminal hi x → g.terminal lo x)
    (calls : ∀ n x lo hi a r, lo ≤ hi → g.call n x lo a r → g.call n x hi a r)
    (stepMono : ∀ n lo hi r, lo ≤ hi → g.budget n lo r ≤ g.budget n hi r)
    (n lo hi : Nat) (x : X) (order : lo ≤ hi) (h : Kernel g n hi x) :
    Kernel g n lo x := by
  induction n generalizing lo hi x with
  | zero => exact endMono _ _ _ order h
  | succ n ih =>
    obtain ⟨a,ha,hr⟩ := h
    refine ⟨a,ha,?_⟩
    intro r hh
    obtain ⟨u,hu,hd⟩ := hr r (calls _ _ _ _ _ _ order hh)
    refine ⟨u,hu,?_⟩
    intro d how
    obtain ⟨legal,next⟩ := hd d how
    exact ⟨legal,ih _ _ _ (stepMono _ _ _ _ order) next⟩

theorem decrement_order (lo hi cost : Nat) (h : lo ≤ hi) : lo-cost ≤ hi-cost :=
  Nat.sub_le_sub_right h cost

end W07.Game
