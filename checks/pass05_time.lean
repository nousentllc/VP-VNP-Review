import Mathlib.Tactic.Ring

/- An independent arithmetic check for Proposition I.1. The expression below
   is tU in Nc/Uni/LenU.lean:177. This file checks its universal majorant and
   the cost of reading both sides of a tape, the input, and one extra letter. -/
namespace Pass05Time

def tapeContents (b T L : Nat) : Nat :=
  5 * ((T + 1) * (L + 1)) + (T + 1) + (T + 1) * (L + 1) +
  T * (L + 1) + T * (L + 4) +
  ((L + 2) * ((2 * T + 1) * (L + 4) + 1) +
    ((L + 1) * ((2 * T + 1) * (L + 4)) + b * (L + 1)) +
    2 * ((2 * T + 1) * (L + 3)))

def slack (b T L : Nat) : Nat :=
  L^2*T*b + 46*L^2*T + L^2*b + 48*L^2 +
  2*L*T*b + 66*L*T + L*b + 80*L + T*b + 2*T + 23

theorem contents_bound (b T L : Nat) :
    tapeContents b T L ≤ (50 + b) * (T + 1) * (L + 1)^2 := by
  calc
    tapeContents b T L ≤ tapeContents b T L + slack b T L := Nat.le_add_right _ _
    _ = (50 + b) * (T + 1) * (L + 1)^2 := by unfold tapeContents slack; ring

theorem final_length_bound {t₀ s budget C : Nat}
    (hc : t₀ ≤ C * budget) (hs : s ≤ budget) (hpos : 1 ≤ budget) :
    2 * t₀ + s + 1 ≤ (2 * C + 2) * budget := by
  calc
    2 * t₀ + s + 1 ≤ 2 * (C * budget) + budget + budget :=
      Nat.add_le_add (Nat.add_le_add (Nat.mul_le_mul_left 2 hc) hs) hpos
    _ = (2 * C + 2) * budget := by ring

#print axioms contents_bound
#print axioms final_length_bound

end Pass05Time
