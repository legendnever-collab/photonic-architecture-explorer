"""Fresh, bounded M5-A artifacts. Refuse an existing run directory; fail closed."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from photonic_architecture_explorer.design import design_two_ports
from photonic_architecture_explorer.design_report import render_design_report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=False)
    start=time.monotonic()
    provenance={'status':'Running','evaluated_checkout_sha':subprocess.check_output(
        ['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'checkout_dirty_before_run':bool(subprocess.check_output(
            ['git','status','--porcelain'],cwd=ROOT,text=True).strip()),
        'python':platform.python_version(),'github_run_id':os.environ.get('GITHUB_RUN_ID'),
        'budget_seconds':30,'artifact_sha256':{}}
    manifest=args.output_dir/'provenance.json'
    manifest.write_text(json.dumps(provenance,indent=2)+'\n')
    try:
        document=json.loads((ROOT/'examples/m5a_two_ports.json').read_text())
        cases={'design':document}
        missing=copy.deepcopy(document);del missing['source']['wavefront_curvature_ts_per_m']
        cases['missing-phase']=missing
        high=copy.deepcopy(document);high['source']['mfd_ts_m']['value']=[2e-6,2e-6]
        cases['domain-fail']=high
        statuses={};counts={}
        for name,inputs in cases.items():
            result=design_two_ports(inputs)
            assert result==design_two_ports(inputs), 'nondeterministic result'
            expected={'design':'Computed','missing-phase':'Uncomputed','domain-fail':'Fail'}[name]
            assert result['status']==expected,(name,result['reason'])
            if name=='design':
                assert len(result['candidates'])==3
                counts={k:result['search'][k] for k in ('geometry_count','accepted_count','rejection_counts')}
            else:
                assert not result['candidates']
            statuses[name]=result['status']
            (args.output_dir/(name+'.json')).write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
            (args.output_dir/(name+'.html')).write_text(render_design_report(result),encoding='utf-8')
        paths=sorted(p for folder in ('src','tests','scripts','examples') for p in (ROOT/folder).rglob('*')
                     if p.suffix in ('.py','.cjs','.json'))
        paths += [ROOT/'pyproject.toml',ROOT/'.github/workflows/validate.yml',ROOT/'docs/M5A_DESIGN_CONTRACT.md',ROOT/'docs/PRODUCT_CHARTER.md']
        provenance['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        provenance['artifact_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(args.output_dir.iterdir()) if p!=manifest}
        provenance.update(case_statuses=statuses,search=counts,elapsed_seconds=time.monotonic()-start)
        assert provenance['elapsed_seconds']<30,'bounded execution budget exceeded'
        provenance['status']='Pass'
    except Exception as exc:
        provenance.update(status='Fail',error=repr(exc))
        raise
    finally:
        manifest.write_text(json.dumps(provenance,indent=2)+'\n')
    print(json.dumps({k:provenance[k] for k in ('status','evaluated_checkout_sha','case_statuses','elapsed_seconds')}))


if __name__=='__main__':
    main()
