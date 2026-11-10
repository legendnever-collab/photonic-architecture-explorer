"""Legacy checker retained; use run_m4c_stop.py for fresh execution certification."""
import argparse
import json
from pathlib import Path
from m4c_evidence import ROOT, check_legacy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('exit_code', type=int)
    parser.add_argument('--output-dir', type=Path, default=ROOT/'results')
    parser.add_argument('--run-id')
    args = parser.parse_args()
    p = check_legacy(args.output_dir, args.exit_code, args.run_id)
    (args.output_dir/'m4c_execution.json').write_text(json.dumps({
        'evidence_check':'Pass' if args.run_id else 'Historical integrity only',
        'control_acceptance':'Fail', 'control_exit_code':1,
        'fresh_execution_verified': args.run_id is not None,
        'run_id': args.run_id,
        'stop_reason':'angular-bin tail fraction exceeds frozen 0.02 absolute error budget',
        'evaluated_checkout_sha':p['evaluated_checkout_sha'],
        'actual_device_performance':'Uncomputed'}, indent=2)+'\n')
    print('Fresh evidence verified: Control FAIL / stopped; actual performance Uncomputed.'
          if args.run_id else
          'Historical integrity only; fresh execution UNVERIFIED. Use run_m4c_stop.py.')


if __name__ == '__main__':
    main()
