"""Checks of the repository. The VIs are binary, so these tests do not run them."""

import html
import re
import unittest
import xml.dom.minidom
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PROJECTS = [ROOT / "CSUB LabVIEW Project.lvproj", ROOT / "v1.22 CSUB LabVIEW Project"]

# Files that the project names but that LabVIEW installs (not in this repository).
EXTERNAL = {
    "Create AO Sine Waves (SubVI).vi",
}

IP = re.compile(r"\b(?!0\.0\.0\.0\b)(?:\d{1,3}\.){3}\d{1,3}\b")
API_KEY = re.compile(r'SecurityAPIKey" Type="Str">(?!REMOVED<)[^<]+<')


def xml_files():
    names = ["*.lvproj", "*.lvlib", "*.lvbitx", "Config.xml"]
    files = [p for n in names for p in ROOT.rglob(n) if ".git" not in p.parts]
    return files + [ROOT / "v1.22 CSUB LabVIEW Project"]


class TestXml(unittest.TestCase):
    def test_xml_files_are_valid(self):
        files = xml_files()
        self.assertGreater(len(files), 5)
        for path in files:
            with self.subTest(path=path.name):
                xml.dom.minidom.parse(str(path))


class TestProject(unittest.TestCase):
    def test_project_copies_are_the_same(self):
        self.assertEqual(PROJECTS[0].read_bytes(), PROJECTS[1].read_bytes())

    def test_labview_version_is_2016(self):
        text = PROJECTS[0].read_text(encoding="utf-8-sig")
        self.assertIn('LVVersion="16008000"', text)

    def test_named_files_exist(self):
        text = PROJECTS[0].read_text(encoding="utf-8-sig")
        urls = [html.unescape(u) for u in re.findall(r'URL="([^"]*)"', text)]
        local = [u[3:] for u in urls if u.startswith("../")]
        self.assertGreater(len(local), 50)
        for rel in local:
            if Path(rel).name in EXTERNAL:
                continue
            with self.subTest(file=rel):
                self.assertTrue((ROOT / rel).exists(), rel)


class TestBinaries(unittest.TestCase):
    def test_vis_and_controls_have_the_labview_header(self):
        files = [p for e in ("*.vi", "*.ctl") for p in ROOT.rglob(e) if ".git" not in p.parts]
        self.assertGreater(len(files), 40)
        for path in files:
            with self.subTest(path=path.name):
                head = path.read_bytes()[:16]
                self.assertTrue(head.startswith(b"RSRC"), head)
                self.assertTrue(b"LVIN" in head or b"LVCC" in head, head)


class TestNoSecrets(unittest.TestCase):
    def test_no_ip_address_and_no_key(self):
        names = ["*.lvproj", "*.aliases", "*.lvlib", "*.lvlps", "Config.xml"]
        files = [p for n in names for p in ROOT.rglob(n) if ".git" not in p.parts]
        files.append(ROOT / "v1.22 CSUB LabVIEW Project")
        for path in files:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
            text = re.sub(r'Version" Type="Str">[\d.]+<', "", text)  # 1.0.0.0 is a version
            with self.subTest(path=path.name):
                self.assertIsNone(IP.search(text), "IP address")
                self.assertIsNone(API_KEY.search(text), "web services key")


def prose(markdown):
    """The sentences of the README, without code, tables, HTML and links."""
    text = re.sub(r"```.*?```", "", markdown, flags=re.S)
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith(("|", "<", "#", "[![", "- marola", "- ww3", "- picasso",
                                  "- closed", "- nashkell")):
            lines.append("")
            continue
        s = re.sub(r"^(> ?)+(\[!\w+\])?", "", s)
        if re.match(r"^(\d+\.|-)\s+", s):
            lines.append("")  # a list item is a sentence of its own
            s = re.sub(r"^(\d+\.|-)\s+", "", s)
        lines.append(s)
    text = "\n".join(lines)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"`[^`]*`", "X", text)
    text = text.replace("**", "")
    paragraphs = re.split(r"\n\s*\n", text)
    for p in paragraphs:
        for sentence in re.split(r"(?<=[.:!?])\s+", " ".join(p.split())):
            if sentence:
                yield sentence


class TestReadme(unittest.TestCase):
    def setUp(self):
        self.text = (ROOT / "README.md").read_text(encoding="utf-8")

    def test_archive_notice(self):
        self.assertIn("**Archive notice.**", self.text)
        self.assertIn("not maintained", self.text)
        self.assertIn("@lfelipem", self.text)

    def test_logo_exists(self):
        self.assertIn('src="docs/logo.svg"', self.text)
        xml.dom.minidom.parse(str(ROOT / "docs" / "logo.svg"))

    def test_sentences_are_short(self):
        # ASD-STE100: at most 20 words in a procedural sentence, 25 in a descriptive one.
        sentences = list(prose(self.text))
        self.assertGreater(len(sentences), 40)
        for s in sentences:
            with self.subTest(sentence=s[:60]):
                self.assertLessEqual(len(s.split()), 25, s)


if __name__ == "__main__":
    unittest.main()
