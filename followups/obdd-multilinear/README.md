# A verified compiler from ordered decision diagrams to multilinear circuits

For every field F and every ordered binary decision diagram with s stored decision nodes, the compiler emits exactly 3s binary arithmetic instructions and a valid output wire. The output represents the unique formal multilinear polynomial over F that agrees with the diagram on every Boolean input. The Lean theorem is `SharedOBDD.compiler_spec` in [SharedOBDD.lean](SharedOBDD.lean).

## Construction and cost

Topologically number the diagram's nodes so children are available before their parents. Use the diagram's chosen variable order to number the variables. At a test of xᵢ, let L and H denote the existing output wires for the low and high branches. The compiler emits these three instructions in execution order.

1. Compute D = H − L.
2. Compute M = xᵢ D.
3. Compute A = L + M and use its wire for this node.

A shared child has one output slot. Every parent references that slot. Subtraction, multiplication and addition each count as one gate. Input variables, the constants zero and one, and wire fan-out are free. The compiler processes every supplied decision node, including redundant or unreachable nodes. It performs no optimizations. Thus 3s is its actual output length and an upper bound on the size needed. A constant diagram with zero nodes emits zero gates.

## What Lean checks

- `gate_count` computes the length of the emitted circuit. `compile_wired` and the root-wire clause of `compiler_spec` establish that all gate references are in range.
- `compile_slots` relates the interpreter for actual arithmetic instructions to the node computation for every register. The source list stores newest nodes first. Its node at distance i has its output at distance 3i in the compiled list.
- `cube_agreement` proves agreement at every bit assignment. `degree_bound` proves that earlier variables are absent and that every variable has degree at most one. In particular the children's polynomials are independent of the variable tested by their parent. Multiplication by that variable therefore preserves multilinearity.
- `unique_multilinear` works with Mathlib's formal multivariate polynomials. The difference between any two candidates vanishes on the grid {0,1}ⁿ and has degree at most one in each variable. The grid-vanishing theorem makes that difference the zero polynomial, including over finite fields and in characteristic two. [Pinned Mathlib lemma](https://github.com/leanprover-community/mathlib4/blob/0df444a360eaa60ab8c11dca51a86af692955474/Mathlib/Combinatorics/Nullstellensatz.lean#L67)

## Controls

[Controls.lean](Controls.lean) uses a three-node diagram in which the root and another decision node share a child. Lean checks all eight bit assignments and the nine-gate count. At the integer input (2,3,5), the emitted circuit evaluates to −19. The file also checks terminal-only input and rejection of an out-of-range source reference.

A diagram that tests the same variable twice can select x². It agrees with x on both bits and gives 4 at the integer input 2. Lean rejects that diagram's ordering predicate. A separate mutation test changes the compiler's multiplication opcode to addition, preserving instruction count and wiring. The replay requires the semantic proof to reject that change.

## Reproduce

Use Lean 4.33.1, Mathlib revision `0df444a360eaa60ab8c11dca51a86af692955474`, Bash and Python 3. With elan and Lake available, run from the extracted project directory:

```sh
lake update
lake exe cache get
bash replay.sh
```

The first two commands prepare the pinned dependency and its cache and need network access on a cold machine. With an existing built Mathlib checkout, the alternate offline invocation is `MATHLIB_DIR=/path/to/mathlib LEAN_BIN=/absolute/path/to/lean bash replay.sh`. The script compiles both source files into a fresh temporary directory with warnings treated as errors, prints the theorem's axioms, then exercises the compiler mutation.

The recorded local run used the existing Apple arm64 Lean and compiled Mathlib cache. The cache's retained Git object pack contains the pinned Mathlib commit. The math library was reused rather than rebuilt in this run. The full output is in [replay.txt](replay.txt). The result is a proof about circuits supplied as ordered decision diagrams. It gives no bound on the size of a decision diagram for a function supplied as an unrestricted Boolean circuit.
