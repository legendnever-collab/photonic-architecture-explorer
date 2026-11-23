"""Entry point of the offline Windows package: starts the Workspace and opens the browser."""
import argparse
import json
import os
from pathlib import Path
import signal
import sys
import webbrowser


def main():
    for key in ('PYTHONHOME', 'PYTHONPATH'):
        os.environ.pop(key, None)
    os.environ['PYTHONUTF8'] = '1'
    os.environ['PYTHONNOUSERSITE'] = '1'
    app = Path(__file__).resolve().parent
    os.chdir(app)
    import photonic_architecture_explorer as module
    from photonic_architecture_explorer import api
    from photonic_architecture_explorer.app import VERSION, make_server, scenario_document

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--port', type=int, default=8770, help='0 picks a free port')
    args = parser.parse_args()
    if not Path(module.__file__).resolve().is_relative_to((app / 'src').resolve()):
        raise RuntimeError('Application was not imported from this package')
    if args.self_test:
        import numpy
        import scipy
        s1 = api.design(scenario_document('S1'))
        web = Path(module.__file__).resolve().parent / 'web' / 'index.html'
        print(json.dumps({'status': 'Pass' if s1['status'] == 'Computed' and web.is_file() else 'Fail',
                          'version': VERSION, 'python': sys.version, 'executable': sys.executable,
                          'application': module.__file__, 'numpy': numpy.__version__, 'scipy': scipy.__version__,
                          'utf8_mode': sys.flags.utf8_mode, 'S1': s1['status'], 'S1_document_sha256': s1['document_sha256'],
                          'web_index': web.is_file()}))
        return 0

    def stop(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    try:
        server = make_server(args.port)
    except OSError:
        server = make_server(0)  # the default port is busy; take any free one
    address = f'http://127.0.0.1:{server.server_address[1]}/'
    print(f'Photonic Architecture Explorer {VERSION}: {address}', flush=True)
    print('이 창을 열어 두세요. 종료하려면 Ctrl+C를 누르세요.', flush=True)
    if not args.no_browser:
        webbrowser.open(address)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
