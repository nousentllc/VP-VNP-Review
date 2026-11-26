# Edition 12 reconciliation of the hosted log and the flat-branch margin

Two questions about Edition 11 concern the provenance of the 9,032-job build and the size of the numerical improvement in E.10. The hosted evidence supports the job count. The strict denominator 12 is a modest improvement to an auxiliary inequality. It leaves the final exponent coefficient $1/1600^2$ unchanged.

## Which build produced each count?

The hosted ZIP contains two logs with different scopes. The review workflow first builds four Lake targets. The publisher's driver then starts Comparator, which performs builds for the reference and solution exports. The standalone log is a copy of the *inner* Comparator transcript. Its last line precedes the publisher shell driver's final two messages. [Workflow as executed](https://github.com/nousentllc/VP-VNP-Review/blob/3524ec471d5e2dee4cd70bd3c60f1dcc94dc43cc/.github/workflows/pass14-comparator.yml) · [Publisher driver, lines 125–139](../primary/.github/scripts/comparator-check.sh#L125)

| Event | Evidence inside the original hosted ZIP | Timestamped Actions job line |
|---|---|---:|
| Four-target build, 9,032 jobs | `pass14-build.log` line 808 | 1165 |
| Build before reference export, 8,708 jobs | `pass14-comparator/comparator.log` line 8, followed by the Challenge export on line 9 | 1222 |
| Build before solution export, 9,027 jobs | Same member, line 516, followed by the Solution export on line 517 | 1730 |
| Nanoda and Lean default kernel accept | Same member, lines 519 and 521 | 1733 and 1735 |
| Final Comparator acceptance | Same member, line 522 | 1736 |
| Driver prints `PASS comparator.json` and accepts the one configuration | Outside both members, after Comparator exits | 1737 and 1738 |

The ZIP is 9,514 bytes with SHA-256 `51c556d89448e6574e57dc4cceca799fd187d786fb7807516d65bc5629772307`. The 35,543-byte build-log member hashes to `484e0e0411afc88bdcd72dff064f2fbc5f108ec45517f6f9afa14f33d14e3002`. Both the 24,357-byte inner log and its standalone copy hash to `afb8c386d39bd7b3c2e40e3d60df3bfaa6c6aa479580a8ca7ecb6c0ba87c1e38`. The original reader checks the 9,032-job completion against the build member. The earlier receipt also lists four tool revision messages and two final driver messages drawn from the outer job. We re-read job 139478246305 and matched all 14 entries in the receipt's evidence list against the timestamped job messages, in order. The accompanying excerpt records the source line for each. These checks establish the provenance of the recorded run without executing another hosted build. [Original ZIP](../checks/pass14_linux_artifact.zip) · [Original reader](../checks/pass14_reader_check.py#L213) · [Job excerpts](edition12-hosted-log-excerpts.json) · [GitHub Actions job](https://github.com/nousentllc/VP-VNP-Review/actions/runs/45691617731/job/139478246305)

## How close is denominator 12 to the scalar limit?

Let $z=\log_2 L,\ N=k(k-1)/2,\ \Delta=1/(1000k)$. At fixed $\Delta$, the four wire, outer, middle, and label inequalities and the paying-cut inequality imply

$$
 z \ge
 \frac{\ell(4k/81-3N\Delta)-k(\sqrt{k}+\Delta)}
      {4/(9\sqrt{k})+\Delta}.
$$

Multiplying the cut inequality by the nonnegative common scale $c$ and eliminating the four terms gives this directly. For the scalar problem the lower bound is attainable: use $c=1$, put each of the four measured prices at its specified bound, and take equality in the cut. Independent scalar prices are a relaxation of the circuit construction. Edition 11's proof rounds the losses independently, obtaining $az\ge b\ell k\sqrt{k}$ with $a=4009/9000,\ b=7651/202500$. The sharp real denominator for that **rounded final comparison** is $a/b=180405/15302=11.78963534\ldots$. Consequently $z>\ell k\sqrt{k}/12$ follows immediately. The publisher had already obtained denominator 14. The review's sharpened circuit corollary has a native Lean receipt separate from the publisher comparison. [Scalar hypotheses and proof](../checks/pass14a_margin.lean#L7) · [Circuit corollary](../checks/pass14a_circuit.lean) · [Publisher comparison](../primary/vp-vnp/Paper/Rate.lean#L123)

To optimize the **unrounded fixed-tolerance inequalities**, put $x=1/\sqrt{k}$ and divide through by $\ell k\sqrt{k}$. For fixed $k$, the resulting lower bound increases with $\ell$ because the subtracted term $(\sqrt{k}+\Delta)/\ell$ decreases. For real $\ell\ge 100\sqrt{k}$ its minimum is at equality, giving

$$
 F(x)=\frac{A+h x^2-f x^3}{d+gx},\qquad
 A=\frac4{81}-\frac3{2000}-\frac1{100},\
 h=\frac3{2000},\ f=\frac1{100000},\ d=\frac49,\ g=\frac1{1000}.
$$

The positive $h x^2$ retains the $k-1$ in the number of wires. The negative $f x^3$ pays for the end-label tolerance. With a positive denominator, the derivative has the sign of

$$
 P(x)=-gA+2hdx+(hg-3fd)x^2-2fgx^3.
$$

On $0\le x\le1$, $P'(x)\ge2hd-2|hg-3fd|-6fg>0$. Its unique root lies between $0.0284192052859$ and $0.0284192052861$, hence $k\approx1238.15821$. Both the real scalar hypothesis $k\ge1$ and the circuit restriction $k\ge2$ contain this point. The sharp reciprocal $1/\min F$ lies between **11.7324917284 and 11.7324917285**. Strict inequalities require a denominator strictly larger than this sharp threshold if equality is admitted among the scalar inputs.

### Integer parameters

Requiring integer $k$ but allowing real $\ell$ leaves two candidate integers bracketing the unique minimum. Exact interval comparison selects $k=1238$. With the manuscript's integer tensor power one must instead use $\ell=\lceil100\sqrt{k}\rceil$. The minimum occurs at $k=1225,\ \ell=3500$ and equals

$$
 \frac{13156618919}{154359922500},
 \qquad D_{\rm integer}=\frac{154359922500}{13156618919}
     =11.73249171769\ldots .
$$

The certificate excludes both infinite tails by monotonicity of the real-$\ell$ lower bound. At $k=1200$ and $1300$ that lower bound already exceeds the displayed minimum by $10^{-10}$. For the 101 integers between the endpoints it computes the ceiling by integer square root, bounds $\sqrt{k}$ outward by rational intervals, and checks the same gap for every other $k$. At $1225$, increasing $\ell$ by one also costs more than that gap. This is global over the stated parameter domain.

Here $z$ is a real scalar. Requiring $L$ itself to be a positive integer rounds the extremal value $z_*=16116858175775/1260081$ up to $\log_2\lceil2^{z_*}\rceil$. The increase is bounded by $2\cdot 2^{-z_*}$, from $\log_2(1+t)\le t/\ln 2<2t$. It cannot cross the certified gap to any other parameter pair. The exact reciprocal in that scalar-plus-integer-size model is $3500\cdot1225\cdot35/\log_2\lceil2^{z_*}\rceil$. These computations say nothing about realization of the extremal prices by an actual circuit.

There is a further choice outside $\texttt{margin12}$'s hypotheses. The cube theorem permits a fresh common witness at *any* positive tolerance. For fixed $k,\ell,L$, the identity above holds as an inequality for every positive $\Delta$, with the same numerical bounds and with a possibly different witness and paying cut on each use. Letting $\Delta$ decrease to zero yields $z/(\ell k\sqrt{k})\ge(4/81-1/100)/(4/9)=319/3600$. This is an independent observation about reusing the approximation theorem. No new Lean or circuit-optimality claim is attached to it. The paper's all-field conclusion already follows with the published constants. [Tolerance quantifier](../primary/vp-vnp/Paper/Convex.lean#L318) · [Fixed choice in the publisher's numerical proof](../primary/vp-vnp/Paper/Rate.lean#L184)

Run `python3 reconciliation/check_edition12_comparator_margin.py` from the review root for the provenance comparison, rational root brackets, integer optimization certificate, and summary output.
