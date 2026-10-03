import re
import subprocess
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[2]
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    "OpenAI key": re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{32,}"),
    "Anthropic key": re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
}


class SecretScanTest(unittest.TestCase):
    def _find_credentials(self, paths: list[Path]) -> list[str]:
        findings = []
        for path in paths:
            if not path.is_file() or path.stat().st_size > 2_000_000:
                continue
            try:
                content = path.read_text()
            except UnicodeDecodeError:
                continue
            for name, pattern in SECRET_PATTERNS.items():
                if pattern.search(content):
                    findings.append(f"{path.relative_to(REPOSITORY_ROOT)}: {name}")
        return findings

    def test_source_configuration_and_fixtures_contain_no_credentials(self) -> None:
        listed = subprocess.run(
            ["rg", "--files", "--hidden", "-0", "-g", "!.git"],
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
        ).stdout
        paths = [
            REPOSITORY_ROOT / relative_path
            for relative_path in listed.decode().split("\0")
            if relative_path
        ]
        self.assertEqual(self._find_credentials(paths), [])

    def test_built_frontend_bundle_contains_no_credentials_when_present(self) -> None:
        bundle_root = REPOSITORY_ROOT / "dist"
        if not bundle_root.exists():
            self.skipTest("frontend bundle has not been built")
        self.assertEqual(self._find_credentials(list(bundle_root.rglob("*"))), [])


if __name__ == "__main__":
    unittest.main()
