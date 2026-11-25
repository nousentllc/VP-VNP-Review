"""Finite-box rational LP and independently evaluable primal/dual certificates."""
from fractions import Fraction as F
import json
import gzip
import math
import time
from pathlib import Path
import numpy as np
import highspy as hs
from scipy.sparse import csr_matrix


class Linear:
    def __init__(self):
        self.names, self.box, self.cost, self.rows, self.integer = [], [], [], [], []
        self.offset = F(0)

    def var(self, name, lower, upper, cost=0, integer=False):
        assert lower <= upper
        self.names.append(name)
        self.box.append((F(lower), F(upper)))
        self.cost.append(F(cost))
        self.integer.append(integer)
        return len(self.names) - 1

    def row(self, name, co, lo=None, hi=None):
        co = {j:F(v) for j,v in co.items() if v}
        self.rows.append((name, co, None if lo is None else F(lo), None if hi is None else F(hi)))

    def dual(self, multipliers):
        assert len(self.rows) == len(multipliers)
        reduced = self.cost.copy()
        total = self.offset
        for (name,co,lower,upper),y in zip(self.rows,multipliers):
            if not y: continue
            end = lower if y>0 else upper
            if end is None: raise ValueError('Invalid multiplier endpoint '+name)
            total += y*end
            for j,a in co.items(): reduced[j] -= y*a
        return total + sum(c*(box[0] if c>=0 else box[1]) for c,box in zip(reduced,self.box))

    def feasible(self, x, integrality=True):
        assert len(x)==len(self.box)
        for name,b,inte,v in zip(self.names,self.box,self.integer,x):
            if not b[0]<=v<=b[1] or (integrality and inte and v.denominator!=1): raise ValueError(name)
        for name,co,lo,hi in self.rows:
            z=sum(a*x[j] for j,a in co.items())
            if (lo is not None and lo>z) or (hi is not None and hi<z): raise ValueError(name)
        return self.offset+sum(c*v for c,v in zip(self.cost,x))

    def optimize(self,mixed=False,seconds=30):
        start=time.perf_counter()
        h=hs.Highs()
        for k,v in dict(output_flag=False,threads=1,random_seed=61,time_limit=float(seconds),mip_rel_gap=.001).items():
            assert h.setOptionValue(k,v)==hs.HighsStatus.kOk
        nr,nc=len(self.rows),len(self.names)
        h.addVars(nc,np.array([float(v[0]) for v in self.box]),np.array([float(v[1]) for v in self.box]))
        idx=np.arange(nc,dtype=np.int32)
        h.changeColsCost(nc,idx,np.array(self.cost,dtype=float));h.changeObjectiveOffset(float(self.offset))
        if mixed:
            inds=idx[self.integer]; h.changeColsIntegrality(len(inds),inds,np.ones(len(inds),dtype=np.uint8))
        starts,indices,data,lo,hi=[0],[],[],[],[]
        for _,co,l,u in self.rows:
            indices.extend(co.keys());data.extend(map(float,co.values()));starts.append(len(data))
            lo.append(-math.inf if l is None else float(l));hi.append(math.inf if u is None else float(u))
        assert h.addRows(nr,np.array(lo),np.array(hi),len(data),np.array(starts,dtype=np.int32),np.array(indices,dtype=np.int32),np.array(data))==hs.HighsStatus.kOk
        loaded=time.perf_counter();h.run(); end=time.perf_counter(); sol=h.getSolution(); info=h.getInfo()
        valid=sol.value_valid and info.primal_solution_status==hs.kSolutionStatusFeasible
        r=dict(status=h.modelStatusToString(h.getModelStatus()),native_objective=h.getObjectiveValue() if valid else None,
               native_dual_bound=info.mip_dual_bound if mixed and math.isfinite(info.mip_dual_bound) else None,
               model_load_s=loaded-start,solve_s=end-loaded)
        x=sol.col_value if valid else None
        y=None
        if not mixed and sol.dual_valid:
            y=[F(round(F.from_float(float(v)) * 10**9), 10**9) for v in sol.row_dual]
            # Projection onto the proper signed halfline preserves dual admissibility.
            y=[0 if (l is None and v>0) or (u is None and v<0) else v for v,(_,_,l,u) in zip(y,self.rows)]
        return r,x,y


def write(path, data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    encoded=(json.dumps(data,default=str,sort_keys=True,allow_nan=False,indent=None)+'\n').encode()
    path.write_bytes(gzip.compress(encoded,mtime=0) if path.suffix=='.gz' else encoded)


def read(path):
    path=Path(path)
    raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)
