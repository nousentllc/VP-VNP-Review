"""Check the Edition 11 evidence provenance and the fixed-tolerance margin using rational bounds."""
from fractions import Fraction as F
from hashlib import sha256
from math import isqrt
from pathlib import Path
from zipfile import ZipFile
import json


ROOT = Path(__file__).resolve().parents[1]
A = F(4, 81) - F(3, 2000) - F(1, 100)
d, g, h, f = F(4, 9), F(1, 1000), F(3, 2000), F(1, 100000)


def inverse_sqrt_interval(k):
    root = isqrt(k)
    if root**2 == k:
        return F(1, root), F(1, root)
    scale = 10**24
    digit = isqrt(scale**2 // k)
    return F(digit, scale), F(digit + (digit**2 * k != scale**2), scale)


def bound_at(k, ell=None):
    """Outward rational bounds for z/(ell*k*sqrt(k)). None takes ell=100*sqrt(k)."""
    lo, hi = inverse_sqrt_interval(k)
    if ell is None:
        lower = A + h*lo**2 - f*hi**3
        upper = A + h*hi**2 - f*lo**3
    else:
        lower = A + F(1, 100) + h*lo**2 - 1/(lo*ell) - g*hi**2/ell
        upper = A + F(1, 100) + h*hi**2 - 1/(hi*ell) - g*lo**2/ell
    assert lower > 0
    return lower / (d + g*hi), upper / (d + g*lo)


def derivative_numerator(x):
    return -g*A + 2*h*d*x + (h*g - 3*f*d)*x**2 - 2*f*g*x**3


def margin_check():
    # The derivative's numerator increases on [0,1], with a unique sign change.
    assert 2*h*d - 2*abs(h*g - 3*f*d) - 6*f*g > 0
    slo, shi = F(284192052859, 10**13), F(284192052861, 10**13)
    assert derivative_numerator(slo) < 0 < derivative_numerator(shi)
    den_lo = (d+g*slo)/(A+h*shi**2-f*slo**3)
    den_hi = (d+g*shi)/(A+h*slo**2-f*shi**3)
    assert F(117324917284, 10**10) < den_lo < den_hi < F(117324917285, 10**10)
    assert 1238 < 1/shi**2 < 1/slo**2 < 1239
    assert bound_at(1238)[1] < bound_at(1239)[0]

    # Outside this window the real-ell bounds increase away from the unique minimum.
    best = F(13156618919, 154359922500)
    gap = F(1, 10**10)
    assert bound_at(1200)[0] > best + gap and bound_at(1300)[0] > best + gap
    for k in range(1200, 1301):
        ell = isqrt(10000*k - 1) + 1
        assert (ell-1)**2 < 10000*k <= ell**2
        lo, hi = bound_at(k, ell)
        if k == 1225:
            assert ell == 3500 and lo == hi == best
            assert bound_at(k, ell + 1)[0] > best + gap
        else:
            assert lo > best + gap
    z = best * 3500 * 1225 * 35
    assert z > 128 and F(2, 2**128) < gap
    return {"coarse_denominator":str(F(180405, 15302)), "real_denominator_interval":["11.7324917284","11.7324917285"],
            "integer_k_real_ell_worst_k":1238, "integer_k_and_ell_worst":[1225,3500],
            "integer_k_and_ell_denominator":str(1/best), "real_logL_at_integer_optimum":str(z),
            "zero_tolerance_limiting_denominator":str(d/(F(4,81)-F(1,100)))}


def comparator_check():
    checks = ROOT / "checks"
    receipt = json.loads((checks / "pass14_comparator.json").read_bytes())
    provenance = receipt["evidence_lines_provenance"]
    excerpts = json.loads((ROOT / provenance["timestamped_job_excerpts"]).read_bytes())
    assert all(receipt[key] == excerpts[key] for key in ("run_id", "job_id", "job_url"))
    job = {entry["line"]:entry["text"].split("Z ", 1)[1] for entry in excerpts["lines"]}
    archived = checks / "pass14_linux_artifact.zip"
    assert "sha256:"+sha256(archived.read_bytes()).hexdigest() == receipt["artifact"]["digest"]
    with ZipFile(archived) as z:
        content = {name:z.read(name) for name in z.namelist()}
    assert {name:sha256(data).hexdigest() for name,data in content.items()} == receipt["artifact"]["members"]
    inner = receipt["comparator_log"]["archive_member"]
    assert content[inner] == (checks / "pass14_comparator.log").read_bytes()
    build = content["pass14-build.log"].decode().splitlines()
    comparator = content[inner].decode().splitlines()
    assert build[807] == job[1165] == "Build completed successfully (9032 jobs)."
    assert comparator[7] == job[1222] == "Build completed successfully (8708 jobs)."
    assert comparator[515] == job[1730] == "Build completed successfully (9027 jobs)."
    assert comparator[521] == job[1736] == "Your solution is okay!"
    assert job[1737] == "PASS comparator.json" and job[1738] == "All 1 comparator configuration(s) accepted."
    # Match every historical receipt quote, including the previously unarchived driver lines.
    indices = provenance["evidence_lines_in_job_order"]
    assert indices == [n for n in job if n not in (1222,1730)]
    assert list(receipt["evidence_lines"]) == [job[n] for n in indices]
    assert [r["jobs"] for r in provenance["build_completions"]] == [9032, 8708, 9027]
    for row in provenance["build_completions"]:
        message = content[row["archive_member"]].decode().splitlines()[row["member_line"]-1]
        assert message == job[row["job_line"]] == f"Build completed successfully ({row['jobs']} jobs)."
    return {"outer_build":[808,9032], "verifier_builds":[[8,8708],[516,9027]],
            "verifier_accepted_line":522, "matched_evidence_lines":len(receipt["evidence_lines"])}


if __name__ == "__main__":
    print(json.dumps({"comparator":comparator_check(), "margin":margin_check()}, indent=2))
