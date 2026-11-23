"""Build the self-contained Windows x64 package (CPython 3.12 + NumPy + SciPy + Workspace)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAME = 'Photonic-Architecture-Explorer-Windows-x64'
PINS = ['numpy==2.3.5', 'scipy==1.17.0']
APP_FOLDERS = ('src', 'examples', 'docs')
APP_FILES = ('README.md', 'AGENTS.md', 'pyproject.toml')


def hashes(directory):
    return {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(directory.rglob('*')) if p.is_file()
            and p.name != 'PACKAGE_MANIFEST.json' and '__pycache__' not in p.parts}


def verify(directory):
    manifest = json.loads((directory / 'PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
    if hashes(directory) != manifest['files_sha256']:
        raise RuntimeError('Distribution file inventory/SHA mismatch')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    if sys.platform != 'win32' or sys.version_info[:2] != (3, 12) or platform.machine().lower() not in ('amd64', 'x86_64'):
        raise RuntimeError('Build on Windows x64 CPython 3.12')
    if not (ROOT / 'src/photonic_architecture_explorer/web/index.html').is_file():
        raise RuntimeError('Frontend build missing: run npm run build in frontend/')
    args.output_dir.mkdir(parents=True, exist_ok=False)
    args.output_dir = args.output_dir.resolve()
    package = args.output_dir / NAME
    runtime = package / 'runtime'
    runtime.mkdir(parents=True)
    base = Path(sys.base_prefix)
    for pattern in ('python*.exe', 'python*.dll', 'vcruntime*.dll', 'LICENSE*'):
        for path in base.glob(pattern):
            if path.is_file():
                shutil.copy2(path, runtime / path.name)
    if not list(runtime.glob('LICENSE*')):
        raise RuntimeError('CPython license missing')
    ignore = shutil.ignore_patterns('__pycache__', 'site-packages', 'test', 'tests',
                                   'idlelib', 'tkinter', 'turtledemo', 'ensurepip')
    shutil.copytree(base / 'Lib', runtime / 'Lib', ignore=ignore)
    shutil.copytree(base / 'DLLs', runtime / 'DLLs')
    site = runtime / 'Lib/site-packages'
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check',
                    '--only-binary=:all:', '--no-compile', '--target', str(site), *PINS], check=True)
    (site / 'pae_app.pth').write_text('../../../app/src\n', encoding='ascii')
    app = package / 'app'
    app.mkdir()
    for folder in APP_FOLDERS:
        shutil.copytree(ROOT / folder, app / folder, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.egg-info'))
    for name in APP_FILES:
        shutil.copy2(ROOT / name, app / name)
    shutil.copy2(ROOT / 'distribution/launcher.py', app / 'launcher.py')
    for name in ('README_WINDOWS.md', 'Start-Photonic-Architecture-Explorer.cmd'):
        shutil.copy2(ROOT / 'distribution' / name, package / name)

    # Validate with the copied runtime and application, not the checkout interpreter.
    executable = runtime / 'python.exe'
    smoke = subprocess.run([str(executable), '-I', '-X', 'utf8', str(app / 'launcher.py'), '--self-test'],
                           capture_output=True, text=True, encoding='utf-8', check=True)
    record = json.loads(smoke.stdout)
    if record['status'] != 'Pass' or record['numpy'] != '2.3.5' or record['scipy'] != '1.17.0' or not record['utf8_mode']:
        raise RuntimeError(f'Bundled self-test failed: {record}')
    environment = dict(os.environ, PYTHONUTF8='1', PYTHONNOUSERSITE='1')
    environment.pop('PYTHONHOME', None)
    environment.pop('PYTHONPATH', None)
    subprocess.run([str(executable), '-c', 'import photonic_architecture_explorer.app'], cwd=args.output_dir, env=environment, check=True)
    for cache in list(package.rglob('__pycache__')):
        shutil.rmtree(cache)
    git = lambda *a: subprocess.check_output(['git', *a], cwd=ROOT, text=True).strip()  # noqa: E731
    manifest = {
        'schema': 'pae-windows-package-1', 'version': record['version'],
        'source_head': git('rev-parse', 'HEAD'), 'source_tree': git('rev-parse', 'HEAD^{tree}'),
        'source_dirty': bool(git('status', '--porcelain')),
        'platform': 'Windows x64', 'python': record['python'],
        'dependencies': {name: record[name] for name in ('numpy', 'scipy')},
        'self_test_S1_document_sha256': record['S1_document_sha256'],
        'files_sha256': hashes(package),
        'limitations': 'Scalar paraxial two-reflector concepts; Total Coupling, package and assembly are Uncomputed',
    }
    (package / 'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    verify(package)
    archive = args.output_dir / (NAME + '.zip')
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in sorted(package.rglob('*')):
            if path.is_file():
                z.write(path, path.relative_to(args.output_dir))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (args.output_dir / (archive.name + '.sha256')).write_text(digest + '  ' + archive.name + '\n', encoding='ascii')
    print(json.dumps({'status': 'Pass', 'archive': str(archive), 'sha256': digest, 'bytes': archive.stat().st_size,
                      'source_head': manifest['source_head']}))


if __name__ == '__main__':
    main()
