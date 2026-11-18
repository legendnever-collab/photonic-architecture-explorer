"""Entry point for the bundled Windows review runtime (no installation needed)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import webbrowser


def main():
    # Child workers inherit the bundled site-packages .pth and explicit UTF-8 mode.
    for key in ('PYTHONHOME', 'PYTHONPATH'):
        os.environ.pop(key, None)
    os.environ['PYTHONUTF8'] = '1'
    os.environ['PYTHONNOUSERSITE'] = '1'
    app = Path(__file__).resolve().parent
    os.chdir(app)
    from photonic_architecture_explorer.workspace import Workspace
    from photonic_architecture_explorer.inspector import make_server
    import photonic_architecture_explorer as module

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--port', type=int, default=0)
    args = parser.parse_args()
    if not Path(module.__file__).resolve().is_relative_to(app / 'src'):
        raise RuntimeError('Application was not imported from this review package')
    workspace = Workspace()
    if args.self_test:
        import numpy, scipy
        print(json.dumps({'status': 'Pass', 'python': sys.version,
                          'executable': sys.executable, 'application': module.__file__,
                          'numpy': numpy.__version__, 'scipy': scipy.__version__,
                          'utf8_mode': sys.flags.utf8_mode,
                          'templates': list(workspace.templates),
                          'proxy_sha256': hashlib.sha256(json.dumps(workspace.templates['smf-glass'],
                              sort_keys=True, allow_nan=False).encode()).hexdigest()}))
        return 0

    def stop(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    with make_server((), args.port, workspace=workspace) as server:
        address = f'http://127.0.0.1:{server.server_port}'
        print(f'Photonic Architecture Explorer: {address}', flush=True)
        print('Keep this window open. Press Ctrl+C to stop the app and workers.', flush=True)
        if not args.no_browser:
            webbrowser.open(address)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
