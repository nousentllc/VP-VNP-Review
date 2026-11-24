def ac_benchmark(root):
    import numpy as np, re, time
    from scipy.optimize import minimize
    text=(root/'pglib_opf_case3_lmbd.m').read_text()
    def matrix(name):
        body=re.search(r'mpc\.'+name+r'\s*=\s*\[(.*?)\];',text,re.S).group(1)
        return np.array([[float(v) for v in row.split()] for row in body.strip().split(';') if row.strip()])
    bus,gen,br,cost=[matrix(k) for k in ['bus','gen','branch','gencost']]
    assert len(bus)==3 and len(gen)==3 and np.all(br[:,8:10]==0) and np.all(br[:,10]==1)
    assert np.all(bus[:,4:6]==0) and np.all(gen[:,7]==1)
    Y=np.zeros((3,3),complex)
    for row in br:
        i,j=int(row[0])-1,int(row[1])-1; y=1/complex(row[2],row[3]); sh=1j*row[4]/2
        Y[i,i]+=y+sh; Y[j,j]+=y+sh; Y[i,j]-=y; Y[j,i]-=y
    def unpack(x):
        return x[:3]*np.exp(1j*np.r_[0,x[3:5]]),np.r_[x[5:7],0],x[7:10]
    def obj(x):
        _,p,_=unpack(x); return float(np.sum(cost[:,4]*p*p+cost[:,5]*p+cost[:,6]))/10000
    def eq(x):
        V,p,q=unpack(x); S=V*np.conj(Y@V)*100
        return np.r_[(p-bus[:,2]-S.real)/100,(q-bus[:,3]-S.imag)/100]
    def iq(x):
        V,_,_=unpack(x); values=[]
        for row in br:
            i,j=int(row[0])-1,int(row[1])-1; y=1/complex(row[2],row[3]); sh=1j*row[4]/2
            a=V[i]*np.conj((V[i]-V[j])*y+V[i]*sh)*100
            b=V[j]*np.conj((V[j]-V[i])*y+V[j]*sh)*100
            da=np.angle(V[i])-np.angle(V[j]); rate=row[5]
            values.extend([(rate**2-abs(a)**2)/10000,(rate**2-abs(b)**2)/10000,da-np.deg2rad(row[11]),np.deg2rad(row[12])-da])
        return np.array(values)
    bounds=list(zip(bus[:,12],bus[:,11]))+[(-np.pi,np.pi)]*2+list(zip(gen[:2,9],gen[:2,8]))+list(zip(gen[:,4],gen[:,3]))
    rows=[]; rng=np.random.default_rng(20261124)
    for run in range(10):
        x=np.r_[np.ones(3),np.zeros(2),[157.5,157.5],bus[:,3]]
        if run: x[:3]=rng.uniform(.94,1.06,3); x[3:5]=rng.uniform(-.15,.15,2)
        start=time.perf_counter(); sol=minimize(obj,x,method='SLSQP',bounds=bounds,constraints=[{'type':'eq','fun':eq},{'type':'ineq','fun':iq}],options={'ftol':1e-10,'maxiter':1000}); elapsed=time.perf_counter()-start
        V,p,q=unpack(sol.x)
        # Independent branch-wise reconstruction, rather than Ybus multiplication.
        flows=np.zeros(3,complex); thermal=0.; angle=0.; losses=0.
        for b in br:
            i,j=int(b[0])-1,int(b[1])-1; y=1/complex(b[2],b[3]); sh=1j*b[4]/2
            sf=100*V[i]*np.conj((V[i]-V[j])*y+V[i]*sh); st=100*V[j]*np.conj((V[j]-V[i])*y+V[j]*sh)
            flows[i]+=sf; flows[j]+=st; losses+=sf.real+st.real
            thermal=max(thermal,abs(sf)-b[5],abs(st)-b[5]); d=np.rad2deg(np.angle(V[i])-np.angle(V[j])); angle=max(angle,b[11]-d,d-b[12])
        residual=max(np.max(abs(p-bus[:,2]-flows.real)),np.max(abs(q-bus[:,3]-flows.imag)))
        bound_violation=max([max(lo-v,v-hi,0) for v,(lo,hi) in zip(sol.x,bounds)])
        valid=residual<1e-5 and thermal<1e-5 and angle<1e-5 and bound_violation<1e-7
        rows.append(dict(run=run,solver_success=bool(sol.success),validated=bool(valid),cost_dollars_per_hour=obj(sol.x)*10000,loss_MW=float(losses),balance_residual_MVA=float(residual),thermal_violation_MVA=float(max(0,thermal)),angle_violation_deg=float(max(0,angle)),bound_violation=float(bound_violation),seconds=elapsed,iterations=int(sol.nit),x=sol.x.tolist()))
    # Analytic lossless economic-dispatch lower bound: demand 315, nonnegative losses,
    # increasing convex costs, no shunts or negative-resistance branches.
    a,b=cost[:2,4],cost[:2,5]; D=sum(bus[:,2]); p1=(2*a[1]*D+b[1]-b[0])/(2*sum(a)); p2=D-p1
    assert 0<=p1<=gen[0,8] and 0<=p2<=gen[1,8] and np.all(br[:,2]>=0)
    lower=float(a[0]*p1*p1+b[0]*p1+a[1]*p2*p2+b[1]*p2)
    return dict(case='PGLib v23.07 case3_lmbd',commit='dc6be4b2f85ca0e776952ec22cbd4c22396ea5a3',seed=20261124,method='SLSQP, ten starts; no new algorithm',settings={'ftol':1e-10,'maxiter':1000},lower_bound_dollars_per_hour=lower,lower_bound_type='analytic lossless economic dispatch',runs=rows)

def bess_benchmark(root):
    import numpy as np, time, csv
    from scipy.optimize import linprog
    T=24; eta=.95; cap=100.; P=50.; Emax=200.; Emin=40.; E0=100.; ramp=20.
    profiles={'flat':[80.]*24,'four_hour_peak':[80.]*16+[140.]*4+[80.]*4,'eight_hour_peak':[80.]*12+[140.]*8+[80.]*4,'alternating':[80.]*12+[140.,80.]*4+[80.]*4}
    summary=[]; schedules=[]
    for name,load in profiles.items():
        d=np.array(load); n=4*T+T+1
        # x = grid[T], charge[T], discharge[T], unmet[T], energy[T+1].
        eq=[]; rhs=[]
        for t in range(T):
            r=np.zeros(n); r[t]=1; r[T+t]=-1; r[2*T+t]=1; r[3*T+t]=1; eq.append(r); rhs.append(d[t])
            r=np.zeros(n); r[4*T+t+1]=1; r[4*T+t]=-1; r[T+t]=-eta; r[2*T+t]=1/eta; eq.append(r); rhs.append(0.)
        ub=[]; ubr=[]
        for t in range(T):
            r=np.zeros(n); r[t]=1
            if t: r[t-1]=-1
            ub.extend([r,-r]); ubr.extend([ramp+(80 if t==0 else 0),ramp-(80 if t==0 else 0)])
        bounds=[(0,cap)]*T+[(0,P)]*(2*T)+[(0,float(v)) for v in d]+[(E0,E0)]+[(Emin,Emax)]*(T-1)+[(E0,Emax)]
        c=np.zeros(n); c[3*T:4*T]=1
        start=time.perf_counter(); first=linprog(c,A_ub=ub,b_ub=ubr,A_eq=eq,b_eq=rhs,bounds=bounds,method='highs')
        assert first.success
        # Lexicographic second stage fixes minimal unmet demand, then minimizes throughput.
        r=np.zeros(n); r[3*T:4*T]=1; eq2=eq+[r]; rhs2=rhs+[first.fun]
        c2=np.zeros(n); c2[T:3*T]=1
        sol=linprog(c2,A_ub=ub,b_ub=ubr,A_eq=eq2,b_eq=rhs2,bounds=bounds,method='highs'); seconds=time.perf_counter()-start
        assert sol.success
        x=sol.x
        candidate=[(x[t],x[T+t],x[2*T+t],x[3*T+t],x[4*T+t],x[4*T+t+1]) for t in range(T)]
        # Conventional threshold policy: recharge to 50% target, shave import above cap.
        greedy=[]; E=E0; prev=80.
        for t,L in enumerate(d):
            g=min(L,cap,prev+ramp); c0=0.; dis=min(max(L-g,0),P,max(0,(E-Emin)*eta)); unmet=max(0,L-g-dis)
            if L<cap and E<E0:
                c0=min(P,cap-L,prev+ramp-L,(E0-E)/eta); c0=max(0,c0); g=L+c0
            assert g>=prev-ramp-1e-8
            new=E+eta*c0-dis/eta; greedy.append((g,c0,dis,unmet,E,new)); E=new; prev=g
        # Stronger forecast-aware heuristic: fill before remaining peaks, then restore E0.
        foresight=[]; E=E0; prev=80.
        for t,L in enumerate(d):
            target=Emax if any(v>cap for v in d[t:]) else E0
            g=min(L,cap,prev+ramp); ch=0.; dis=min(max(L-g,0),P,max(0,(E-Emin)*eta)); u=max(0,L-g-dis)
            if L<cap and E<target:
                ch=max(0,min(P,cap-L,prev+ramp-L,(target-E)/eta)); g=L+ch
            new=E+eta*ch-dis/eta; foresight.append((g,ch,dis,u,E,new)); E=new; prev=g
        for method,rows in [('threshold',greedy),('forecast_threshold',foresight),('lookahead_LP',candidate)]:
            violations=[]; previous=80.
            for t,(g,ch,dis,u,e,en) in enumerate(rows):
                violations.extend([abs(g+dis-ch+u-d[t]),abs(en-e-eta*ch+dis/eta),max(0,g-cap,-g,ch-P,dis-P,-ch,-dis,Emin-en,en-Emax,abs(g-previous)-ramp,-u,u-d[t])])
                assert min(ch,dis)<1e-7
                previous=g
                schedules.append(dict(profile=name,method=method,hour=t,load_MW=d[t],grid_MW=g,charge_MW=ch,discharge_MW=dis,unserved_MW=u,energy_before_MWh=e,energy_after_MWh=en))
            terminal_shortfall=max(0,E0-rows[-1][-1]); maxviol=max(violations+[terminal_shortfall]); assert maxviol<1e-6
            summary.append(dict(profile=name,method=method,unserved_MWh=float(sum(r[3] for r in rows)),grid_MWh=float(sum(r[0] for r in rows)),throughput_MWh=float(sum(r[1]+r[2] for r in rows)),conversion_loss_MWh=float(sum((1-eta)*r[1]+(1/eta-1)*r[2] for r in rows)),terminal_MWh=float(rows[-1][-1]),max_violation=maxviol,solve_seconds=seconds if method=='lookahead_LP' else None))
    with (root/'bess_schedules.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=schedules[0]); w.writeheader(); w.writerows(schedules)
    (root/'bess_inputs.json').write_text(__import__('json').dumps(dict(profiles=profiles,eta_charge=eta,eta_discharge=eta,import_cap_MW=cap,power_MW=P,energy_MWh=Emax,reserve_MWh=Emin,initial_MWh=E0,terminal_min_MWh=E0,ramp_MW_per_hour=ramp,dt_hours=1),indent=2))
    return summary

def exact_certificate():
    from fractions import Fraction as F
    # min 20*x+50*y subject to x+y=100, 0<=x<=60, y>=0.
    def check(x,y,lam,mu):
        feasible=x+y==100 and 0<=x<=60 and y>=0
        dual=mu>=0 and lam-mu<=20 and lam<=50
        primal=20*x+50*y; lower=100*lam-60*mu
        return bool(feasible and dual and primal==lower)
    witness=tuple(map(F,[60,40,50,30])); valid=check(*witness)
    mutants=[(F(61),F(39),F(50),F(30)),(F(60),F(40),F(51),F(30)),(F(60),F(40),F(50),F(29)),(F(60),F(39),F(50),F(30))]
    rejected=sum(not check(*v) for v in mutants); assert valid and rejected==4
    return dict(primal=[60,40],dual=[50,30],primal_objective=3200,dual_objective=3200,accepted=valid,mutations_rejected=rejected,scope='exact rational arithmetic check, not Lean or a verified checker')

def main():
    import pathlib,json,platform,sys,hashlib
    import scipy,numpy
    root=pathlib.Path(__file__).resolve().parent
    results=dict(environment=dict(python=sys.version,scipy=scipy.__version__,numpy=numpy.__version__,platform=platform.platform(),processor=platform.processor()),ac_opf=ac_benchmark(root),bess=bess_benchmark(root),certificate=exact_certificate())
    (root/'results.json').write_text(json.dumps(results,indent=2))
    print(json.dumps({k:v for k,v in results.items() if k!='ac_opf'},indent=2))
    print(json.dumps({'ac_lower_bound':results['ac_opf']['lower_bound_dollars_per_hour'],'ac_runs':results['ac_opf']['runs']},indent=2))

if __name__=='__main__':
    main()
