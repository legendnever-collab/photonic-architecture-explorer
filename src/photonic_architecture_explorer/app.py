"""Local Workspace server: JSON API + static frontend, loopback only, standard library only.

    pae-app [--port 8770] [--open]

Endpoints
    GET  /api/health                 version and schema identifiers
    GET  /api/presets                Port presets with provenance
    GET  /api/scenarios              User Decision Benchmark index
    GET  /api/scenarios/<id>         one scenario Design Document
    POST /api/preview                Design Document -> Port geometry and per-Port guards
    POST /api/design                 Design Document -> pae.result/1
"""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
import mimetypes
from pathlib import PurePosixPath
from urllib.parse import urlparse
import webbrowser

from . import api
from .design_document import SCHEMA
from .presets import load_presets

VERSION = '0.2.0-p0'
MAX_BODY = 2 * 1024 * 1024
PACKAGE = resources.files(__package__)


def scenario_index():
    return json.loads(PACKAGE.joinpath('scenarios', 'index.json').read_text(encoding='utf-8'))


def scenario_document(identifier):
    for entry in scenario_index()['scenarios']:
        if entry['id'] == identifier and entry['file']:
            return json.loads(PACKAGE.joinpath('scenarios', entry['file']).read_text(encoding='utf-8'))
    return None


def static_file(path):
    """Resolve a request path inside the packaged `web/` directory, or None."""
    parts = PurePosixPath(path).parts[1:] or ('index.html',)
    if any(part in ('..', '') or part.startswith('.') for part in parts):
        return None
    node = PACKAGE.joinpath('web', *parts)
    if node.is_dir():
        node = node.joinpath('index.html')
    return node if node.is_file() else None


class Handler(BaseHTTPRequestHandler):
    server_version = f'PAE/{VERSION}'

    def log_message(self, fmt, *args):  # keep the console quiet for users
        pass

    def _send(self, status, body, content_type='application/json; charset=utf-8'):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False, allow_nan=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/api/health':
            return self._send(200, {'status': 'ok', 'version': VERSION, 'design_schema': SCHEMA,
                                    'result_schema': api.RESULT_SCHEMA})
        if path == '/api/presets':
            return self._send(200, {'presets': load_presets()})
        if path == '/api/scenarios':
            return self._send(200, scenario_index())
        if path.startswith('/api/scenarios/'):
            document = scenario_document(path.rsplit('/', 1)[-1])
            return self._send(200, document) if document else self._send(404, {'error': 'unknown scenario'})
        if path.startswith('/api/'):
            return self._send(404, {'error': 'unknown endpoint'})
        node = static_file(path)
        if node is None:
            return self._send(404, b'Not found', 'text/plain; charset=utf-8')
        kind = mimetypes.guess_type(node.name)[0] or 'application/octet-stream'
        if kind.startswith('text/') or kind in ('application/javascript', 'application/json'):
            kind += '; charset=utf-8'
        return self._send(200, node.read_bytes(), kind)

    def do_POST(self):
        path = urlparse(self.path).path
        handlers = {'/api/preview': api.preview, '/api/design': api.design}
        if path not in handlers:
            return self._send(404, {'error': 'unknown endpoint'})
        length = int(self.headers.get('Content-Length') or 0)
        if length <= 0 or length > MAX_BODY:
            return self._send(413 if length > MAX_BODY else 400, {'error': 'JSON body of at most 2 MB required'})
        try:
            document = json.loads(self.rfile.read(length).decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return self._send(400, {'error': f'invalid JSON: {exc}'})
        return self._send(200, handlers[path](document))


def make_server(port=8770):
    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Photonic Architecture Explorer local Workspace')
    parser.add_argument('--port', type=int, default=8770)
    parser.add_argument('--open', action='store_true', help='open the default browser')
    args = parser.parse_args(argv)
    server = make_server(args.port)
    url = f'http://127.0.0.1:{server.server_address[1]}/'
    print(f'Photonic Architecture Explorer {VERSION}: {url}  (Ctrl+C로 종료)', flush=True)
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
