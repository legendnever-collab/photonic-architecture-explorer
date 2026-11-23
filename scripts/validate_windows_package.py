"""Verify an extracted Windows package: inventory, isolated runtime, .cmd launcher, HTTP API and browser.

    python scripts/validate_windows_package.py <package dir> --output-dir <dir> [--browser-channel msedge]
"""
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

from build_windows_package import ROOT, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--browser-channel', action='append', default=[],
                        help='Run the browser check against the packaged server with this Playwright channel (e.g. msedge, chrome)')
    args = parser.parse_args()
    package = args.package.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    manifest = verify(package)
    git = lambda *a: subprocess.check_output(['git', *a], cwd=ROOT, text=True).strip()  # noqa: E731
    if manifest['source_head'] != git('rev-parse', 'HEAD') or manifest['source_tree'] != git('rev-parse', 'HEAD^{tree}') or manifest['source_dirty']:
        raise RuntimeError('Package must match the clean verification HEAD')
    executable = package / 'runtime/python.exe'
    launcher = package / 'app/launcher.py'
    poisoned = dict(os.environ, PYTHONHOME=str(package / 'wrong-home'), PYTHONPATH=str(package / 'wrong-path'), PYTHONUTF8='0')
    smoke = subprocess.run([str(executable), '-I', '-X', 'utf8', str(launcher), '--self-test'],
                           cwd=args.output_dir, env=poisoned, capture_output=True, text=True, encoding='utf-8', check=True)
    runtime = json.loads(smoke.stdout)
    assert runtime['status'] == 'Pass', runtime
    assert Path(runtime['executable']).resolve() == executable
    assert Path(runtime['application']).resolve().is_relative_to(package / 'app/src')
    assert runtime['S1_document_sha256'] == manifest['self_test_S1_document_sha256']

    # The checkout engine and the packaged engine must agree on every scenario.
    sys.path.insert(0, str(ROOT / 'src'))
    from photonic_architecture_explorer import api
    from photonic_architecture_explorer.app import scenario_document, scenario_index

    cmd = package / 'Start-Photonic-Architecture-Explorer.cmd'
    launched = subprocess.run(f'"{cmd}" --self-test', shell=True, cwd=args.output_dir, env=poisoned,
                              capture_output=True, text=True, encoding='utf-8', timeout=60)
    if launched.returncode:
        raise RuntimeError('CMD self-test failed: ' + launched.stdout + '\n' + launched.stderr)
    assert json.loads(launched.stdout)['status'] == 'Pass'

    process = subprocess.Popen([str(executable), '-I', '-X', 'utf8', str(launcher), '--no-browser', '--port', '0'],
                               cwd=args.output_dir, env=poisoned, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, encoding='utf-8')
    lines = queue.Queue()
    threading.Thread(target=lambda: [lines.put(line) for line in process.stdout], daemon=True).start()
    evidence = {'status': 'Pass', 'source_head': manifest['source_head'], 'runtime': runtime,
                'file_inventory_verified': True, 'poisoned_environment_ignored': True, 'cmd_launcher': True}
    try:
        address = None
        for _ in range(10):
            match = re.search(r'http://127\.0\.0\.1:\d+/', lines.get(timeout=20))
            if match:
                address = match[0]
                break
        assert address, 'Launcher did not print a loopback URL'
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(address, timeout=10) as response:
            assert 'assets/app.js' in response.read().decode('utf-8')
        packaged = {}
        for entry in scenario_index()['scenarios']:
            if not entry['file']:
                continue
            document = scenario_document(entry['id'])
            request = urllib.request.Request(address + 'api/design', data=json.dumps(document).encode('utf-8'),
                                             headers={'Content-Type': 'application/json'})
            with opener.open(request, timeout=120) as response:
                remote = json.loads(response.read())
            local = api.design(document)
            assert remote['status'] == local['status'] == entry['expect']['status'], entry['id']
            assert [c['id'] for c in remote['candidates']] == [c['id'] for c in local['candidates']], entry['id']
            assert remote['engine_report'] == json.loads(json.dumps(local['engine_report'])), entry['id']
            packaged[entry['id']] = remote['status']
        evidence['packaged_http_scenarios'] = packaged
        for channel in args.browser_channel:
            out = args.output_dir / f'browser-{channel}'
            check = subprocess.run([sys.executable, str(ROOT / 'scripts/check_app.py'), '--url', address,
                                    '--channel', channel, '--output-dir', str(out)], capture_output=True, text=True, encoding='utf-8')
            (args.output_dir / f'browser-{channel}.log').write_text(check.stdout + check.stderr, encoding='utf-8')
            if check.returncode:
                raise RuntimeError(f'Browser check with {channel} failed:\n{check.stdout}\n{check.stderr}')
            evidence[f'browser_{channel}'] = 'Pass'
    finally:
        process.terminate()
        process.wait(timeout=10)
    verify(package)
    (args.output_dir / 'acceptance.json').write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(evidence, ensure_ascii=False))


if __name__ == '__main__':
    main()
