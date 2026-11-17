"""Real subprocess lifecycle checks without a full optimizer search."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest

from photonic_architecture_explorer.design import design_two_ports
from photonic_architecture_explorer.workflow_jobs import JobManager, TERMINAL
from photonic_architecture_explorer.workspace import Workspace, initial_values

ROOT = Path(__file__).resolve().parents[1]


class WorkerLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads((ROOT / 'examples/m7a_smf_glass_proxy.json').read_text())
        cls.exact = design_two_ports(cls.document)

    def wait_state(self, manager, identity, states, limit=10):
        deadline = time.monotonic() + limit
        while time.monotonic() < deadline:
            data = manager.poll(identity)
            if data['state'] in states:
                return data
            time.sleep(.02)
        self.fail('Job did not reach expected state: ' + str(manager.poll(identity)))

    def test_timeout_terminates_unresponsive_process_and_withholds_result(self):
        manager = JobManager(timeout=.15, command=[sys.executable, '-c', 'import time; time.sleep(30)'])
        try:
            identity = manager.submit(self.document, self.exact)
            final = self.wait_state(manager, identity, TERMINAL)
            self.assertEqual(final['state'], 'TimedOut')
            self.assertIsNone(final['result'])
            self.assertIsNotNone(manager.jobs[identity['job_id']]['process'].poll())
        finally:
            manager.close()

    def test_crash_and_wrong_revision_cannot_publish(self):
        manager = JobManager(command=[sys.executable, '-c', 'raise SystemExit(7)'])
        try:
            identity = manager.submit(self.document, self.exact)
            self.assertIsNone(manager.poll({**identity, 'revision': 'old'}))
            self.assertFalse(manager.cancel({**identity, 'input_sha256': 'wrong'}))
            final = self.wait_state(manager, identity, TERMINAL)
            self.assertEqual(final['state'], 'Failed')
            self.assertIsNone(final['result'])
        finally:
            manager.close()

    def test_replacement_waits_for_old_exit_and_has_immutable_snapshot(self):
        manager = JobManager(command=[sys.executable, '-c', 'import time; time.sleep(30)'])
        try:
            mutable = copy.deepcopy(self.document)
            first = manager.submit(mutable, self.exact)
            self.wait_state(manager, first, {'Running'})
            mutable['description'] = 'Changed after submission'
            second = manager.submit(self.document, self.exact)
            self.assertNotEqual(first['job_id'], second['job_id'])
            self.assertEqual(manager.jobs[first['job_id']]['request']['document'], self.document)
            self.wait_state(manager, second, {'Running'})
            self.assertEqual(manager.poll(first)['state'], 'Cancelled')
            self.assertIsNotNone(manager.jobs[first['job_id']]['process'].poll())
            self.assertTrue(manager.cancel(second))
            self.assertEqual(self.wait_state(manager, second, TERMINAL)['state'], 'Cancelled')
        finally:
            manager.close()

    def test_next_exact_design_cancels_workspace_worker(self):
        workspace = Workspace()
        workspace.jobs = JobManager(command=[sys.executable, '-c', 'import time; time.sleep(30)'])
        try:
            identity = workspace.jobs.submit(self.document, self.exact)
            self.wait_state(workspace.jobs, identity, {'Running'})
            html, code = workspace.post(initial_values(workspace.templates['example'], 'example'))
            self.assertEqual(code, 200)
            self.assertIn('G009-B1', html)
            self.assertEqual(self.wait_state(workspace.jobs, identity, TERMINAL)['state'], 'Cancelled')
        finally:
            workspace.close()

    def test_installed_worker_checks_request_snapshot_before_search(self):
        manager = JobManager()
        try:
            # A malformed internal request must fail, rather than evaluating a stale q snapshot.
            exact = copy.deepcopy(self.exact)
            exact['input_snapshot']['description'] = 'stale'
            identity = manager.submit(self.document, exact)
            final = self.wait_state(manager, identity, TERMINAL)
            self.assertEqual(final['state'], 'Failed')
            self.assertIsNone(final['result'])
            self.assertIn('mismatch', final['error'])
        finally:
            manager.close()


if __name__ == '__main__':
    unittest.main()
