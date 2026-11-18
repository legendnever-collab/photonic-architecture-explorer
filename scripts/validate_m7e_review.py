"""Verify an extracted review package, isolated launcher and Frozen exact cases."""
import argparse
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import urllib.request

from build_m7e_review import ROOT, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    package = args.package.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    manifest = verify(package)
    head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if manifest['source_head'] != head or manifest['source_dirty']:
        raise RuntimeError('Package must match the clean verification HEAD')
    executable = package / 'runtime/python.exe'
    launcher = package / 'app/review_launcher.py'
    poisoned = dict(os.environ, PYTHONHOME=str(package/'wrong-home'),
                    PYTHONPATH=str(package/'wrong-path'), PYTHONUTF8='0')
    smoke = subprocess.run([str(executable),'-I','-X','utf8',str(launcher),'--self-test'],
                           cwd=args.output_dir,env=poisoned,capture_output=True,text=True,encoding='utf-8',check=True)
    runtime = json.loads(smoke.stdout)
    assert Path(runtime['executable']).resolve() == executable
    assert Path(runtime['application']).resolve().is_relative_to(package / 'app/src')
    assert runtime['utf8_mode'] == 1
    assert runtime['proxy_sha256'] == manifest['input_proxy_sha256']
    environment = dict(os.environ, PYTHONUTF8='1', PYTHONNOUSERSITE='1')
    environment.pop('PYTHONHOME',None);environment.pop('PYTHONPATH',None)
    program = '''
import json
from pathlib import Path
from photonic_architecture_explorer.design import design_two_ports
from photonic_architecture_explorer.inspector import ROOT
names=['m5a_two_ports.json','m5f_different_q.json','m5f_high_divergence.json']
print(json.dumps({name:design_two_ports(json.loads((ROOT/'examples'/name).read_text())) for name in names}))
'''
    computed = subprocess.run([str(executable),'-I','-X','utf8','-c',program],cwd=args.output_dir,
                              env=environment,capture_output=True,text=True,encoding='utf-8',check=True)
    results = json.loads(computed.stdout)
    sys.path.insert(0,str(ROOT/'src'))
    from photonic_architecture_explorer.design import design_two_ports
    for name, result in results.items():
        expected = design_two_ports(json.loads((ROOT/'examples'/name).read_text(encoding='utf-8')))
        assert result == expected, name
    (args.output_dir/'frozen.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    # Verify the .cmd dispatch too; the tested folder contains both spaces and Unicode.
    cmd = package/'Start-Photonic-Architecture-Explorer.cmd'
    # Popen supplies cmd.exe's outer /c quoting. A list containing manually nested
    # quotes is escaped again by list2cmdline and breaks a path containing spaces.
    command = f'"{cmd}" --self-test'
    launched = subprocess.run(command,shell=True,cwd=args.output_dir,env=poisoned,
                             capture_output=True,text=True,encoding='utf-8',timeout=30)
    if launched.returncode:
        (args.output_dir/'cmd-error.txt').write_text(launched.stdout+'\n'+launched.stderr,encoding='utf-8')
        raise RuntimeError('CMD self-test failed: '+launched.stdout+'\n'+launched.stderr)
    assert json.loads(launched.stdout)['proxy_sha256'] == manifest['input_proxy_sha256']
    process = subprocess.Popen([str(executable),'-I','-X','utf8',str(launcher),'--no-browser'],
        cwd=args.output_dir,env=poisoned,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8')
    lines = queue.Queue()
    def read():
        for line in process.stdout:
            lines.put(line)
    reader = threading.Thread(target=read,daemon=True);reader.start()
    try:
        address = None
        for _ in range(5):
            line = lines.get(timeout=10)
            match = re.search(r'http://127\.0\.0\.1:\d+',line)
            if match:
                address=match[0];break
        assert address, 'Launcher did not print a loopback URL'
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(address,timeout=5) as response:
            html = response.read().decode('utf-8')
        assert 'SMF–Glass Proxy' in html and 'Design' in html
    finally:
        process.terminate();process.wait(timeout=10)
        reader.join(timeout=2)
        process.stdout.close()
    verify(package)
    evidence = {'status':'Pass','source_head':head,'package':str(package),
                'runtime':runtime,'file_inventory_verified':True,'poisoned_environment_ignored':True,
                'frozen_results_equal':True,'cmd_launcher':True,'actual_launcher_http':True,
                'packaged_application_import':True}
    (args.output_dir/'acceptance.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(evidence))


if __name__ == '__main__':
    main()
