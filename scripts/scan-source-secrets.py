"""Redacted tracked-source scan. Environment files and symlinks are excluded."""
import re
import subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
PATTERNS = (
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    r"\bgh[pousr]_[A-Za-z0-9]{30,}\b",
    r"\bgithub_pat_[A-Za-z0-9_]{50,}\b",
    r"\bAKIA[A-Z0-9]{16}\b",
    r"\bsk-(?:proj-)?[A-Za-z0-9_-]{40,}\b",
    r"\b(?:sk|rk)_live_[A-Za-z0-9]{20,}\b",
    r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b",
    r"\bAIza[A-Za-z0-9_-]{35}\b",
)
BINARY = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".woff", ".woff2", ".mp4", ".mp3", ".pdf"}

def candidate_count(text):
    return sum(len(re.findall(pattern, text)) for pattern in PATTERNS)

def main():
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    findings = checked = excluded = 0
    for name in filter(None, names):
        path = ROOT / name
        if path.name.startswith(".env") or path.suffix.lower() in BINARY or path.is_symlink():
            excluded += 1
            continue
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            excluded += 1
            continue
        checked += 1
        findings += candidate_count(text)
    print(f"Redacted source scan: {checked} tracked text files; {excluded} environment/binary/symlink exclusions; {findings} candidate matches. No values or filenames emitted. Not a history scan.")
    return int(findings > 0)

if __name__ == "__main__":
    raise SystemExit(main())
