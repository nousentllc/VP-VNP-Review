"""Shared paths, lossless JSON recording, and a small sparse linear-model builder."""
import json
import os
from pathlib import Path

import highspy as hs
import numpy as np
from scipy.sparse import coo_matrix

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('W03_RESULTS', str(ROOT / 'results'))).resolve()
OUT.mkdir(exist_ok=True, parents=True)
DESIGN = json.loads((ROOT / 'protocol/design.json').read_text())
INF = float('inf')


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    def convert(x):
        if isinstance(x, np.ndarray):
            return x.tolist()
        if isinstance(x, np.generic):
            return x.item()
        raise TypeError(type(x).__name__)
    path.write_text(json.dumps(data, default=convert, sort_keys=True, allow_nan=False,
                               separators=(',', ':')) + '\n')


class LinearModel:
    def __init__(self):
        self.lo, self.hi, self.cost, self.integer = [], [], [], []
        self.row, self.col, self.val, self.lhs, self.rhs = [], [], [], [], []

    def vars(self, shape, lo=0, hi=1, cost=0, integer=False):
        first = len(self.lo)
        for array, value in [(self.lo, lo), (self.hi, hi), (self.cost, cost), (self.integer, integer)]:
            array.extend(np.broadcast_to(value, shape).ravel().tolist())
        return np.arange(first, len(self.lo)).reshape(shape)

    def constraint(self, terms, lo=-INF, hi=INF):
        row = len(self.lhs)
        for index, coef in terms:
            if coef:
                self.row.append(row)
                self.col.append(int(index))
                self.val.append(float(coef))
        self.lhs.append(lo)
        self.rhs.append(hi)

    def solver(self, presolve, gap):
        n, m = len(self.cost), len(self.lhs)
        self.A = coo_matrix((self.val, (self.row, self.col)), shape=(m,n)).tocsc()
        lp = hs.HighsLp()
        lp.num_col_, lp.num_row_ = n, m
        lp.col_cost_, lp.col_lower_, lp.col_upper_ = self.cost, self.lo, self.hi
        lp.row_lower_, lp.row_upper_ = self.lhs, self.rhs
        a = lp.a_matrix_
        a.format_ = hs.MatrixFormat.kColwise
        a.start_, a.index_, a.value_ = self.A.indptr, self.A.indices, self.A.data
        lp.a_matrix_ = a
        if any(self.integer):
            lp.integrality_ = [hs.HighsVarType.kInteger if i else hs.HighsVarType.kContinuous
                               for i in self.integer]
        h = hs.Highs()
        settings = {'output_flag': False, 'threads': 1, 'random_seed': 17,
                    'presolve': presolve, 'mip_rel_gap': gap, 'mip_feasibility_tolerance': 1e-7}
        for name, val in settings.items():
            if h.setOptionValue(name, val) != hs.HighsStatus.kOk:
                raise ValueError(name)
        if h.passModel(lp) != hs.HighsStatus.kOk:
            raise ValueError('HiGHS rejected the model')
        return h


def finite_bound(x):
    return float(x) if np.isfinite(x) and abs(x) < 1e25 else None
