import Mathlib.Algebra.MvPolynomial.Funext
import Mathlib.Combinatorics.Nullstellensatz

/-! A list is a topologically sorted straight-line program, newest instruction first.
A reference is the distance to an older instruction; multiple uses address the same slot. -/
namespace SharedOBDD

inductive Ref where
  | zero | one | slot (offset : Nat)
  deriving Repr, DecidableEq

structure Node (n : Nat) where
  var : Fin n
  low : Ref
  high : Ref
  deriving Repr

def push (v : α) (s : Nat → α) : Nat → α
  | 0 => v
  | i+1 => s i

def Ref.read (z o : α) (s : Nat → α) : Ref → α
  | .zero => z
  | .one => o
  | .slot i => s i

def Ref.Valid (size : Nat) : Ref → Prop
  | .slot i => i < size
  | _ => True

def nodeStore (z o : α) (step : Fin n → α → α → α) : List (Node n) → Nat → α
  | [] => fun _ => z
  | q :: qs =>
    let s := nodeStore z o step qs
    push (step q.var (q.low.read z o s) (q.high.read z o s)) s

def level (qs : List (Node n)) (r : Ref) : Nat :=
  r.read n n (nodeStore n n (fun i _ _ => i.val) qs)

def Ordered : List (Node n) → Prop
  | [] => True
  | q :: qs => Ordered qs ∧ q.low.Valid qs.length ∧ q.high.Valid qs.length ∧
      q.var.val < level qs q.low ∧ q.var.val < level qs q.high

def decision (qs : List (Node n)) (root : Ref) (b : Fin n → Bool) : Bool :=
  root.read false true (nodeStore false true (fun i l h => if b i then h else l) qs)

inductive Wire (n : Nat) where
  | zero | one | input (i : Fin n) | gate (offset : Nat)
  deriving Repr, DecidableEq

inductive Op where | add | sub | mul deriving Repr, DecidableEq

structure Gate (n : Nat) where
  op : Op
  lhs : Wire n
  rhs : Wire n
  deriving Repr, DecidableEq

def Wire.read [Zero R] [One R] (x : Fin n → R) (s : Nat → R) : Wire n → R
  | .zero => 0
  | .one => 1
  | .input i => x i
  | .gate i => s i

def Op.run [Add R] [Sub R] [Mul R] : Op → R → R → R
  | .add => (· + ·)
  | .sub => (· - ·)
  | .mul => (· * ·)

def gateStore [Ring R] (x : Fin n → R) : List (Gate n) → Nat → R
  | [] => fun _ => 0
  | g :: gs =>
    let s := gateStore x gs
    push (g.op.run (g.lhs.read x s) (g.rhs.read x s)) s

/-- Each node's output occupies the newest of its three slots. -/
def wire (shift : Nat) : Ref → Wire n
  | .zero => .zero
  | .one => .one
  | .slot i => .gate (3*i + shift)

/-- Emit the difference, then the product, then the sum. The final sum can still
read the old low child two slots farther back. The emitted list is newest first. -/
def compile : List (Node n) → List (Gate n)
  | [] => []
  | q :: qs =>
    ⟨.add, wire 2 q.low, .gate 0⟩ ::
    ⟨.mul, .input q.var, .gate 0⟩ ::
    ⟨.sub, wire 0 q.high, wire 0 q.low⟩ :: compile qs

theorem gate_count (qs : List (Node n)) : (compile qs).length = 3 * qs.length := by
  induction qs with
  | nil => rfl
  | cons q qs ih => simp [compile, ih, Nat.mul_succ]

def Wire.Valid (size : Nat) : Wire n → Prop
  | .gate i => i < size
  | _ => True

def Wired : List (Gate n) → Prop
  | [] => True
  | g :: gs => g.lhs.Valid gs.length ∧ g.rhs.Valid gs.length ∧ Wired gs

theorem wire_valid {r : Ref} (h : r.Valid size) (k : Nat) :
    (wire (n := n) k r).Valid (3*size+k) := by
  cases r <;> simp_all [Ref.Valid, wire, Wire.Valid]

theorem compile_wired {qs : List (Node n)} (h : Ordered qs) : Wired (compile qs) := by
  induction qs with
  | nil => trivial
  | cons q qs ih =>
    obtain ⟨ho, hl, hh, _, _⟩ := h
    simp only [compile, Wired, List.length_cons, gate_count]
    refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ih ho⟩
    · exact wire_valid hl 2
    · change 0 < 3 * qs.length + 1 + 1
      omega
    · trivial
    · change 0 < 3 * qs.length + 1
      omega
    · exact wire_valid hh 0
    · exact wire_valid hl 0

def join [Ring R] (x l h : R) : R := l + x * (h-l)

private theorem read_slots [Ring R] (x : Fin n → R) (s t : Nat → R)
    (h : ∀ i, s (3*i) = t i) (r : Ref) :
    (wire 0 r).read x s = r.read 0 1 t := by
  cases r with
  | zero | one => rfl
  | slot i => exact h i

theorem compile_slots [Ring R] (x : Fin n → R) (qs : List (Node n)) (i : Nat) :
    gateStore x (compile qs) (3*i) =
      nodeStore 0 1 (fun j => join (x j)) qs i := by
  induction qs generalizing i with
  | nil => rfl
  | cons q qs ih =>
    cases i with
    | zero =>
      rcases q with ⟨j, l, h⟩
      cases l <;> cases h <;>
        simp [compile, gateStore, nodeStore, push, wire, Wire.read, Ref.read, Op.run, join, ih]
    | succ i => simpa [Nat.mul_succ, compile, gateStore, nodeStore, push] using ih i

open MvPolynomial

noncomputable def poly {F : Type*} [Field F] (qs : List (Node n)) (root : Ref) : MvPolynomial (Fin n) F :=
  (wire 0 root).read X (gateStore X (compile qs))

private noncomputable def ps {F : Type*} [Field F] (qs : List (Node n)) :=
  nodeStore (0 : MvPolynomial (Fin n) F) 1 (fun j => join (X j)) qs

theorem poly_read {F : Type*} [Field F] (qs : List (Node n)) (r : Ref) :
    poly (F := F) qs r = r.read 0 1 (ps qs) :=
  read_slots _ _ _ (compile_slots _ qs) r

def bit [Zero R] [One R] (b : Bool) : R := if b then 1 else 0

theorem cube_agreement {F : Type*} [Field F] (qs : List (Node n)) (root : Ref)
    (b : Fin n → Bool) :
    eval (fun i => bit (R := F) (b i)) (poly qs root) = bit (decision qs root b) := by
  rw [poly_read]
  induction qs generalizing root with
  | nil => cases root <;> simp [ps, nodeStore, Ref.read, decision, bit]
  | cons q qs ih =>
    cases root with
    | zero | one => simp [Ref.read, decision, bit]
    | slot i =>
      cases i with
      | succ i => exact ih (.slot i)
      | zero =>
        change eval _ (join (X q.var) (q.low.read 0 1 (ps qs)) (q.high.read 0 1 (ps qs))) =
          bit (if b q.var then decision qs q.high b else decision qs q.low b)
        simp only [join, map_add, map_mul, map_sub, eval_X, ih]
        cases b q.var <;> simp [bit]

/-- No earlier variable appears, and every variable has individual degree at most one. -/
theorem degree_bound {F : Type*} [Field F] {qs : List (Node n)} (ord : Ordered qs)
    (r : Ref) (j : Fin n) :
    degreeOf j (poly (F := F) qs r) ≤ (if j.val < level qs r then 0 else 1) := by
  rw [poly_read]
  induction qs generalizing r with
  | nil => cases r <;> simp [Ref.read, ps, nodeStore]
  | cons q qs ih =>
    obtain ⟨ord, _, _, hlow, hhigh⟩ := ord
    cases r with
    | zero | one => simp [Ref.read]
    | slot k =>
      cases k with
      | succ k => exact ih ord (.slot k)
      | zero =>
        change degreeOf j (join (X q.var) (q.low.read 0 1 (ps qs)) (q.high.read 0 1 (ps qs))) ≤
          (if j.val < q.var.val then 0 else 1)
        have hl := ih ord q.low
        have hh := ih ord q.high
        unfold join
        apply (degreeOf_add_le _ _ _).trans
        apply max_le
        · split <;> split at hl <;> omega
        · apply (degreeOf_mul_le _ _ _).trans
          have hd := degreeOf_sub_le j (q.high.read 0 1 (ps (F := F) qs)) (q.low.read 0 1 (ps qs))
          rw [degreeOf_X]
          by_cases eq : j = q.var
          · subst j
            simp [hlow, hhigh] at hh hl
            simp [hh, hl] at hd
            simp [hd]
          · simp only [if_neg eq, Nat.zero_add]
            apply hd.trans
            apply max_le
            · split <;> split at hh <;> omega
            · split <;> split at hl <;> omega

theorem unique_multilinear {F : Type*} [Field F] {qs : List (Node n)}
    (ord : Ordered qs) (root : Ref) (p : MvPolynomial (Fin n) F)
    (multilinear : ∀ i, degreeOf i p ≤ 1)
    (agrees : ∀ b : Fin n → Bool, eval (fun i => bit (R := F) (b i)) p = bit (decision qs root b)) :
    p = poly qs root := by
  classical
  apply sub_eq_zero.mp
  apply eq_zero_of_eval_zero_at_prod_finset _ (fun _ => {0, 1})
  · intro i
    rw [Finset.card_pair (zero_ne_one' F)]
    have hb := degree_bound (F := F) ord root i
    have hsub := degreeOf_sub_le i p (poly qs root)
    split at hb <;> have := multilinear i <;> omega
  · intro x hx
    let b : Fin n → Bool := fun i => decide (x i = 1)
    have he : (fun i => bit (R := F) (b i)) = x := by
      funext i
      have hi := hx i
      simp only [Finset.mem_insert, Finset.mem_singleton] at hi
      rcases hi with hz | ho <;> simp [bit, b, *]
    rw [map_sub, ← he, agrees, cube_agreement, sub_self]

/-- The returned wire, valid program, precise size and formal polynomial specification. -/
theorem compiler_spec {F : Type*} [Field F] {qs : List (Node n)} {root : Ref}
    (ord : Ordered qs) (validRoot : root.Valid qs.length) :
    Wired (compile qs) ∧
    (wire (n := n) 0 root).Valid (compile qs).length ∧
    (compile qs).length = 3 * qs.length ∧
    (∀ i, degreeOf i (poly (F := F) qs root) ≤ 1) ∧
    (∀ b, eval (fun i => bit (R := F) (b i)) (poly qs root) = bit (decision qs root b)) ∧
    (∀ p : MvPolynomial (Fin n) F, (∀ i, degreeOf i p ≤ 1) →
      (∀ b, eval (fun i => bit (R := F) (b i)) p = bit (decision qs root b)) →
      p = poly qs root) := by
  refine ⟨compile_wired ord, ?_, gate_count qs, ?_, cube_agreement qs root, ?_⟩
  · simpa [gate_count] using wire_valid (n := n) validRoot 0
  · intro i
    have h := degree_bound (F := F) ord root i
    split at h <;> omega
  · exact unique_multilinear ord root

end SharedOBDD

