"""Run contract checks on a disposable copy of a candidate; stdlib only."""
from pathlib import Path
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--case', choices=['recovery', 'projection', 'publication'], required=True)
parser.add_argument('--candidate', type=Path, required=True, help='Root containing candidate Python module/package')
args = parser.parse_args()
checks = Path(__file__).resolve().parent / 'cases' / args.case / 'checks'
candidate = args.candidate.resolve(strict=True)
if not candidate.is_dir():
    parser.error('--candidate must be a directory')
with tempfile.TemporaryDirectory(prefix='engineering-contract-check-') as directory:
    work = Path(directory) / 'candidate'
    shutil.copytree(candidate, work, ignore=shutil.ignore_patterns(
        '__pycache__', '.git', '.runtime-state', 'product-engineering', '.tmp'))
    env = dict(os.environ, PYTHONPATH=str(work), PYTHONDONTWRITEBYTECODE='1')
    command = [sys.executable, '-B', '-m', 'unittest', 'discover',
               '-s', str(checks), '-p', 'test_*.py', '-v']
    result = subprocess.run(command, cwd=work, env=env)
raise SystemExit(result.returncode)
