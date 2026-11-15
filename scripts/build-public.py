"""Build an allowlisted Pages artifact into a NEW directory; never deploy or delete."""
import argparse
import shutil
from pathlib import Path
from public_files import ROOT, public_files


def build(destination, root=ROOT):
    names = public_files(root)
    destination = Path(destination).resolve()
    if destination.exists():
        raise ValueError('Output already exists; choose a new directory (nothing deleted)')
    destination.mkdir(parents=True)
    for name in names:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, target)
    actual = sorted(p.relative_to(destination).as_posix() for p in destination.rglob('*') if p.is_file())
    if actual != names:
        raise ValueError('Public artifact does not match the allowlist')
    print(f'Public artifact verified: {len(names)} files; no content/, docs/, tests/ or build scripts.')
    return names


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    build(args.output)
