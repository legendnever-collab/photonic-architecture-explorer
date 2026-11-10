"""Isolate legacy outputs before launch; runtime failure is never an accepted STOP."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import uuid
from m4c_evidence import ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    run_id = uuid.uuid4().hex
    out = (args.output_dir or ROOT/'results/runtime'/('m4c-'+run_id)).resolve()
    out.mkdir(parents=True, exist_ok=False)  # Refuse stale directories, including empty ones.
    env = {**os.environ, 'M4C_OUTPUT_DIR': str(out), 'M4C_RUN_ID': run_id}
    with (out/'process.log').open('w') as log:
        child = subprocess.run([sys.executable, str(ROOT/'scripts/m4c_planar_control.py')],
                               cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=120)
    subprocess.run([sys.executable, str(ROOT/'scripts/check_m4c_stop.py'), str(child.returncode),
                    '--output-dir', str(out), '--run-id', run_id], cwd=ROOT, check=True)
    print(out)


if __name__ == '__main__':
    main()
