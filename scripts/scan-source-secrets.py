"""Redacted tracked-source scan; never opens environment files."""
import re, subprocess
from pathlib import Path
root=Path(__file__).resolve().parent.parent
files=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
patterns=[r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',r'\bgh[pousr]_[A-Za-z0-9]{30,}\b',r'\bgithub_pat_[A-Za-z0-9_]{50,}\b',r'\bAKIA[A-Z0-9]{16}\b',r'\bsk-(?:proj-)?[A-Za-z0-9_-]{40,}\b']
findings=0; checked=0; excluded=0
for name in files:
    if not name: continue
    p=root/name
    if p.name.startswith('.env') or p.suffix.lower() in {'.png','.jpg','.jpeg','.webp','.gif','.ico','.woff','.woff2','.mp4','.mp3','.pdf'}:
        excluded+=1; continue
    if not p.is_file(): continue
    try: text=p.read_text(encoding='utf-8')
    except UnicodeDecodeError: excluded+=1; continue
    checked+=1
    findings+=sum(len(re.findall(pattern,text)) for pattern in patterns)
print(f'Redacted secret scan: {checked} tracked text files checked; {excluded} environment/binary files excluded; {findings} candidate matches. No values emitted. Not a full history scan.')
raise SystemExit(1 if findings else 0)