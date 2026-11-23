"""One local worker at a time, bounded lifetime and revision-checked results."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import uuid

TERMINAL = {'Succeeded', 'NoCandidate', 'Cancelled', 'TimedOut', 'Failed'}


class JobManager:
    def __init__(self, *, root=None, timeout=600, command=None):
        self.temporary = tempfile.TemporaryDirectory(prefix='pae-jobs-') if root is None else None
        self.root = Path(self.temporary.name if self.temporary else root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.timeout = min(timeout, 600)
        self.command = command or [sys.executable, '-m', 'photonic_architecture_explorer.workflow_worker']
        self.jobs = {}
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._watch, daemon=True, name='pae-worker-watchdog')
        self.thread.start()

    def submit(self, document, exact):
        with self.lock:
            if self.stop.is_set():
                raise RuntimeError('Workspace closed')
            for job in self.jobs.values():
                self._cancel(job)
            # Old pages can no longer retrieve an evicted result.
            for key in list(self.jobs)[:-15]:
                if self.jobs[key]['state'] in TERMINAL:
                    del self.jobs[key]
            identifier, revision = uuid.uuid4().hex, uuid.uuid4().hex
            identity = {'job_id': identifier, 'revision': revision, 'input_sha256': exact['input_sha256']}
            directory = self.root / identifier
            directory.mkdir()
            request = json.loads(json.dumps({'identity': identity, 'document': document, 'exact': exact}, allow_nan=False))
            (directory / 'request.json').write_text(json.dumps(request, ensure_ascii=False, allow_nan=False))
            self.jobs[identifier] = {'identity': identity, 'directory': directory, 'request': request,
                                     'state': 'Queued', 'process': None, 'result': None, 'progress': {}}
            return copy.deepcopy(identity)

    def _cancel(self, job, state='Cancelled'):
        if job['state'] in TERMINAL:
            return
        job['stop_state'] = state
        (job['directory'] / 'cancel').touch()
        if job['process'] is None:
            job['state'] = state
        elif job['state'] != 'Cancelling':
            job.update(state='Cancelling', stop_time=time.monotonic())

    def cancel(self, identity):
        with self.lock:
            job = self._lookup(identity)
            if job is None:
                return False
            self._cancel(job)
            return True

    def cancel_active(self):
        with self.lock:
            for job in self.jobs.values():
                self._cancel(job)

    def _lookup(self, identity):
        job = self.jobs.get(identity.get('job_id'))
        return job if job and job['identity'] == identity else None

    def poll(self, identity):
        with self.lock:
            job = self._lookup(identity)
            if job is None:
                return None
            return {**identity, 'state': job['state'], 'progress': copy.deepcopy(job['progress']),
                    'error': job.get('error'), 'result': copy.deepcopy(job['result'])}

    def _finish(self, job):
        process = job['process']
        job['log'].close()
        if 'stop_state' in job:
            job.update(state=job['stop_state'], result=None)
            return
        try:
            if process.returncode != 0:
                raise RuntimeError(f'Worker exited with code {process.returncode}; see worker.log')
            report = json.loads((job['directory'] / 'worker.json').read_text())
            if report['identity'] != job['identity']:
                raise ValueError('Worker identity mismatch')
            state = report['state']
            if state not in TERMINAL:
                raise ValueError('Invalid worker terminal state')
            result = report.get('design_result')
            if state in ('Succeeded', 'NoCandidate'):
                if not isinstance(result, dict) or result['input_snapshot'] != job['request']['document']:
                    raise ValueError('Worker changed input snapshot')
                if result['input_sha256'] != job['identity']['input_sha256']:
                    raise ValueError('Worker result input SHA mismatch')
                if (state == 'Succeeded') != bool(result['candidates']):
                    raise ValueError('Worker result status mismatch')
                for candidate in result['candidates']:
                    if candidate.get('independent_validation', {}).get('status') != 'Pass':
                        raise ValueError('Worker recommendation lacks independent validation')
                result['workflow'] = {**job['identity'], 'state': state, 'method': report['policy']['id'],
                    'policy': report['policy'], 'versions': report['versions'],
                    'elapsed_seconds': report['elapsed_seconds'], 'source_sha256': report['source_sha256'],
                    'exact_search': report['exact_result']['search'], 'near_match': report['fallback']}
            else:
                result = None
            job.update(state=state, result=result, error=report.get('error'))
        except Exception as error:
            job.update(state='Failed', result=None, error=str(error))

    def _watch(self):
        while not self.stop.wait(.05):
            with self.lock:
                try:
                    self._tick()
                except Exception as error:
                    # Keep the watchdog alive and withhold affected results.
                    for job in self.jobs.values():
                        if job['state'] not in TERMINAL:
                            job['error'] = str(error)
                            self._cancel(job, 'Failed')

    def _tick(self):
        for job in self.jobs.values():
            process = job['process']
            if process is None or job['state'] in TERMINAL:
                continue
            if time.monotonic() - job['started'] >= self.timeout:
                self._cancel(job, 'TimedOut')
            if process.poll() is not None:
                self._finish(job)
                continue
            if job['state'] == 'Cancelling':
                elapsed = time.monotonic() - job['stop_time']
                if elapsed > 2:
                    process.kill()
                elif elapsed > .5:
                    process.terminate()
            try:
                job['progress'] = json.loads((job['directory'] / 'progress.json').read_text())
            except (OSError, ValueError):
                pass
        active = any(j['process'] is not None and j['process'].poll() is None for j in self.jobs.values())
        if not active:
            next_job = next((j for j in self.jobs.values() if j['state'] == 'Queued'), None)
            if next_job:
                try:
                    next_job['log'] = (next_job['directory'] / 'worker.log').open('w')
                    next_job['process'] = subprocess.Popen([*self.command, str(next_job['directory'])],
                        stdin=subprocess.DEVNULL, stdout=next_job['log'], stderr=subprocess.STDOUT)
                    next_job.update(state='Running', started=time.monotonic())
                except OSError as error:
                    if 'log' in next_job:
                        next_job['log'].close()
                    next_job.update(state='Failed', error=str(error), result=None)

    def close(self):
        self.stop.set()
        self.thread.join(timeout=3)
        with self.lock:
            for job in self.jobs.values():
                process = job['process']
                if process and process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)
                if 'log' in job:
                    job['log'].close()
            if self.temporary:
                self.temporary.cleanup()
