#!/usr/bin/env python3
"""Extract statement text locally; transaction interpretation remains a reviewed step."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    executable = shutil.which('pdftotext')
    if not executable:
        parser.error('pdftotext is not installed. Use a local PDF application to export text; never an online converter for private statements.')
    if not args.source.is_file() or args.source.is_symlink() or args.source.stat().st_size > 20_000_000:
        parser.error('Choose a regular PDF up to 20 MB.')
    try:
        result = subprocess.run([executable, '-layout', str(args.source.resolve()), '-'], capture_output=True, timeout=30)
        if result.returncode or not result.stdout.strip():
            parser.error('Text extraction failed or the PDF is a scan. Use local unlocking/OCR and reconcile the result.')
        fd = os.open(args.destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as output:
            output.write(result.stdout)
        print('Private text file created. Reconcile activity before converting it to an import CSV.')
    except (OSError, subprocess.TimeoutExpired):
        parser.error('Could not create the text file. Check local tools, paths and permissions; existing files are never overwritten.')


if __name__ == '__main__':
    main()
