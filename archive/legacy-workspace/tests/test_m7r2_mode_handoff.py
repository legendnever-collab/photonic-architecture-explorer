"""Reference review boundaries and the unchanged concept handoff."""

import hashlib
from html.parser import HTMLParser
import json
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from photonic_architecture_explorer.design import design_two_ports
from photonic_architecture_explorer.inspector import ROOT, make_server
from photonic_architecture_explorer.mode_reference import CATALOG
from photonic_architecture_explorer.workspace import Workspace, build_document, initial_values


class ReferenceMarkup(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.ids = []
        self.tags = []
        self.hrefs = []
        self.feed(html)

    def handle_starttag(self, tag, attributes):
        self.tags.append(tag)
        attrs = dict(attributes)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a":
            self.hrefs.append(attrs["href"])


class ModeHandoffTests(unittest.TestCase):
    def test_read_only_reference_route_and_blank_handoff(self):
        workspace = Workspace()
        with make_server((), port=0, workspace=workspace) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                with patch("photonic_architecture_explorer.workspace.design_two_ports",
                           side_effect=AssertionError("GET must never evaluate Design")):
                    with urlopen(base, timeout=3) as response:
                        home = ReferenceMarkup(response.read().decode())
                        self.assertIn("/?entry=mode-references", home.hrefs)
                    with urlopen(base + "/?entry=mode-references&unused=example", timeout=3) as response:
                        html = response.read().decode()
                        markup = ReferenceMarkup(html)
                        self.assertIn("comparison-1550", markup.ids)
                        self.assertIn("readiness-1310", markup.ids)
                        self.assertEqual(markup.tags.count("polyline"), 6)
                        self.assertNotIn("form", markup.tags)
                        self.assertIn(hashlib.sha256(CATALOG.read_bytes()).hexdigest(), html)
                        self.assertIn("Glass Waveguide External Port · Uncomputed", html)
                        self.assertIn("sun-fldw-55mw-1310", markup.ids)
                        self.assertIn("/?entry=blank", markup.hrefs)
                        self.assertIn("/?entry=smf-glass", markup.hrefs)
                    with urlopen(base + "/?entry=blank", timeout=3) as response:
                        blank = response.read().decode()
                        self.assertIn('name="source_mfd_ts_m_0"', blank)
                        self.assertNotIn('id="design-review"', blank)
                    with self.assertRaises(HTTPError) as error:
                        urlopen(Request(base + "/design", data=b"entry=mode-references"), timeout=3)
                    self.assertEqual(error.exception.code, 400)
                    error.exception.close()
            finally:
                server.shutdown()
                thread.join(timeout=3)

    def test_explicit_proxy_handoff_preserves_the_frozen_input(self):
        workspace = Workspace()
        template = workspace.templates["smf-glass"]
        raw = initial_values(template, "smf-glass")
        actual = build_document(template, raw)
        expected = json.loads((ROOT / "examples/m7a_smf_glass_proxy.json").read_text(encoding="utf-8"))
        self.assertEqual(actual, expected)
        result = design_two_ports(actual)
        self.assertEqual(result["input_sha256"], "9d6d55bc8c4a06ca99c7ffcae205954a634678162986d2565c111b76df510988")
        self.assertEqual(result["search"]["geometry_count"], 36)
        self.assertEqual(len(result["search"]["attempts"]), 144)
        self.assertEqual(result["search"]["accepted_count"], 0)
        self.assertEqual(result["actual_applicability"]["status"], "Uncomputed")
