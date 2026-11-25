"""Bounded post-hoc branch tree. All leaves, including unsolved ones, cover original commitments."""
import sys,time
from fractions import Fraction as F
from pathlib import Path
from linear import read,write
from commitment import build,HERE


def fixed(lp,branch):
    for j,v in branch:
        assert lp.integer[j] and 0<=v<=1
        lp.box[j]=(F(v),F(v))


def run(path,T,primary,out):
    start=time.perf_counter();lp=build(path,T);boxes=lp.box.copy()
    r=read(primary/'summary.json');U=F(r['U']);base=F(r['L'])
    nodes=[];leaves=set()
    def node(branch,parent):
        lp.box=boxes.copy();fixed(lp,branch);s,x,y=lp.optimize()
        L=base if parent is None else nodes[parent]['L']
        if y is not None:L=max(L,lp.dual(y))
        candidates=[]
        if x:
            candidates=[j for j,v in enumerate(x) if lp.integer[j] and lp.box[j][0]<lp.box[j][1] and 1e-7<v<1-1e-7]
        split=min(candidates,key=lambda j:(not lp.names[j].startswith('ug['),abs(x[j]-.5),j)) if candidates else None
        i=len(nodes);leaves.add(i)
        nodes.append(dict(parent=parent,branch=branch,dual=y,L=L,split=split,native=s))
        return i
    node([],None);history=[]
    while len(nodes)<15:
        global_lb=min(nodes[i]['L'] for i in leaves);history.append(global_lb)
        if global_lb>F(99,100)*U:break
        cand=[i for i in leaves if nodes[i]['split'] is not None and nodes[i]['L']<=F(99,100)*U]
        if not cand:break
        i=min(cand,key=lambda k:(nodes[k]['L'],k));rnode=nodes[i];leaves.remove(i)
        for v in (0,1):node([*rnode['branch'],[rnode['split'],v]],i)
    L=max(F(r['strongest_L']),min(nodes[i]['L'] for i in leaves))
    write(out/'tree.json.gz',nodes)
    write(out/'summary.json',dict(nodes=len(nodes),leaves=len(leaves),U=U,L=L,relative_pct=float(100*(U-L)/U),
         excluded=L>F(99,100)*U,wall_s=time.perf_counter()-start,global_lower_history=history))
    print(path.name,T,len(nodes),float(100*(U-L)/U),flush=True)


def audit(path,T,primary,out):
    lp=build(path,T);boxes=lp.box.copy();r=read(primary/'summary.json');nodes=read(out/'tree.json.gz')
    assert nodes[0]['parent'] is None and nodes[0]['branch']==[]
    children={i:[] for i in range(len(nodes))}
    for i,n in enumerate(nodes):
        L=F(r['L']) if i==0 else F(nodes[n['parent']]['L'])
        if i:assert 0<=n['parent']<i;children[n['parent']].append(i)
        lp.box=boxes.copy();fixed(lp,n['branch'])
        if n['dual'] is not None:L=max(L,lp.dual(list(map(F,n['dual']))))
        assert L==F(n['L'])
    for i,kids in children.items():
        if kids:
            j=nodes[i]['split'];assert lp.integer[j] and boxes[j]==(0,1) and j not in [v[0] for v in nodes[i]['branch']]
            assert [nodes[k]['branch'] for k in kids]==[[*nodes[i]['branch'],[j,v]] for v in (0,1)]
    L=max(F(r['strongest_L']),min(F(nodes[i]['L']) for i,k in children.items() if not k))
    assert L==F(read(out/'summary.json')['L'])


if __name__=='__main__':
    act,primary,out=sys.argv[1],Path(sys.argv[2]),Path(sys.argv[3])
    for p in sorted(primary.glob('*/summary.json')):
        r=read(p)
        if r['U'] is not None and not r['excluded']:
            path=HERE/'inputs'/r['case'];target=out/p.parent.name
            if act=='run':
                if (target/'summary.json').exists():raise FileExistsError(target)
                run(path,r['horizon'],p.parent,target)
            else:audit(path,r['horizon'],p.parent,target)
