def main():
    import pathlib,json,csv,re,math
    from fractions import Fraction
    root=pathlib.Path(__file__).resolve().parent
    data=json.loads((root/'results.json').read_text())
    case=(root/'pglib_opf_case3_lmbd.m').read_text()
    def matrix(name):
        body=re.search(r'mpc\.'+name+r'\s*=\s*\[(.*?)\];',case,re.S).group(1)
        return [[float(v) for v in row.split()] for row in body.strip().split(';') if row.strip()]
    bus,gen,br,cost=[matrix(k) for k in ['bus','gen','branch','gencost']]
    assert len(bus)==len(gen)==3
    assert all(row[8]==row[9]==0 and row[10]==1 for row in br)
    assert all(row[4]==row[5]==0 for row in bus)
    ac=[]
    for run in data['ac_opf']['runs']:
        x=run['x']; v=x[:3];theta=[0,x[3],x[4]];p=[x[5],x[6],0];q=x[7:10]
        pflow=[0.]*3;qflow=[0.]*3;thermal=0.;angle=0.
        for b in br:
            i,j=int(b[0])-1,int(b[1])-1
            G=b[2]/(b[2]**2+b[3]**2);B=-b[3]/(b[2]**2+b[3]**2)
            for a,z in [(i,j),(j,i)]:
                d=theta[a]-theta[z]
                pf=G*v[a]**2-v[a]*v[z]*(G*math.cos(d)+B*math.sin(d))
                qf=-(B+b[4]/2)*v[a]**2-v[a]*v[z]*(G*math.sin(d)-B*math.cos(d))
                pflow[a]+=pf*100;qflow[a]+=qf*100
                thermal=max(thermal,math.hypot(pf,qf)*100-b[5])
            deg=math.degrees(theta[i]-theta[j]);angle=max(angle,b[11]-deg,deg-b[12])
        residual=max([abs(p[i]-bus[i][2]-pflow[i]) for i in range(3)]+[abs(q[i]-bus[i][3]-qflow[i]) for i in range(3)])
        assert residual<1e-5 and thermal<1e-5 and angle<1e-5
        assert all(bus[i][12]-1e-7<=v[i]<=bus[i][11]+1e-7 for i in range(3))
        assert all(gen[i][9]-1e-7<=p[i]<=gen[i][8]+1e-7 and gen[i][4]-1e-7<=q[i]<=gen[i][3]+1e-7 for i in range(3))
        objective=sum(cost[i][4]*p[i]**2+cost[i][5]*p[i]+cost[i][6] for i in range(3))
        assert abs(objective-run['cost_dollars_per_hour'])<1e-7
        assert abs(sum(p)-sum(b[2] for b in bus)-run['loss_MW'])<1e-7
        ac.append({'run':run['run'],'scalar_balance_residual':residual,'thermal_violation_MVA':max(0,thermal)})
    inputs=json.loads((root/'bess_inputs.json').read_text())
    rows=list(csv.DictReader((root/'bess_schedules.csv').open()));bess=[]
    for profile in inputs['profiles']:
        for method in ['threshold','forecast_threshold','lookahead_LP']:
            group=[r for r in rows if r['profile']==profile and r['method']==method]
            assert len(group)==24
            prevE=100.;prevG=80.;grid=0.;served=0.;loss=0.;maxres=0.;unserved=0.
            for t,row in enumerate(group):
                r={k:float(v) for k,v in row.items() if k not in ['profile','method']}
                g,c,d,u,e,en=[r[k] for k in ['grid_MW','charge_MW','discharge_MW','unserved_MW','energy_before_MWh','energy_after_MWh']]
                load=inputs['profiles'][profile][t]
                assert r['hour']==t and r['load_MW']==load
                maxres=max(maxres,abs(e-prevE),abs(g+d-c+u-load),abs(en-e-.95*c+d/.95))
                assert -1e-8<=g<=100+1e-8 and abs(g-prevG)<=20+1e-8
                assert 40-1e-8<=en<=200+1e-8 and -1e-8<=c<=50+1e-8 and -1e-8<=d<=50+1e-8
                assert min(c,d)<1e-7 and -1e-8<=u<=load+1e-8
                grid+=g;served+=load-u;unserved+=u;loss+=.05*c+(1/.95-1)*d
                prevE=en;prevG=g
            error=abs(grid-served-loss-(prevE-100))
            assert maxres<1e-7 and error<1e-6 and prevE>=100-1e-8
            record=next(r for r in data['bess'] if r['profile']==profile and r['method']==method)
            assert abs(unserved-record['unserved_MWh'])<1e-7 and abs(loss-record['conversion_loss_MWh'])<1e-7
            bess.append({'profile':profile,'method':method,'balance_residual':maxres,'conservation_error_MWh':error})
    F=Fraction;x,y=map(F,data['certificate']['primal']);lam,mu=map(F,data['certificate']['dual'])
    assert x+y==100 and 0<=x<=60 and y>=0 and mu>=0 and lam-mu<=20 and lam<=50
    assert 20*x+50*y==100*lam-60*mu==3200
    result={'status':'passed','AC_scalar_trigonometric_checks':ac,'BESS_checks':bess,'toy_exact_witness':'accepted',
       'scope':'Independent numerical reconstruction within same model; not a formally verified checker or field validation'}
    (root/'independent_checks.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({'status':'passed','AC_cases':len(ac),'BESS_schedules':len(bess)},indent=2))

if __name__=='__main__':
    main()

