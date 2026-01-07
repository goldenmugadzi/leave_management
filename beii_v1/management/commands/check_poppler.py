from django.core.management.base import BaseCommand
import os
import shutil
import subprocess
import sys

from django.conf import settings

class Command(BaseCommand):
    help = 'Check Poppler/pdfinfo availability and optionally run pdfinfo on a PDF'

    def add_arguments(self, parser):
        parser.add_argument('pdf', nargs='?', help='Optional path to a PDF file to run pdfinfo on')

    def handle(self, *args, **options):
        poppler_path = getattr(settings, 'POPPLER_PATH', None)
        self.stdout.write(f'POPPLER_PATH (from settings): {poppler_path!r}')

        # Check whether pdfinfo is on PATH
        which_pdfinfo = shutil.which('pdfinfo')
        self.stdout.write(f"shutil.which('pdfinfo') -> {which_pdfinfo}")

        # Check pdfinfo in POPPLER_PATH if provided
        pdfinfo_in_poppler = None
        if poppler_path:
            candidate = os.path.join(poppler_path, 'pdfinfo.exe' if os.name == 'nt' else 'pdfinfo')
            pdfinfo_in_poppler = candidate if os.path.exists(candidate) else None
            self.stdout.write(f'pdfinfo at POPPLER_PATH -> {pdfinfo_in_poppler}')

        # Prefer explicit POPPLER_PATH binary if present, else rely on PATH
        exe = pdfinfo_in_poppler or which_pdfinfo
        if not exe:
            self.stderr.write('ERROR: pdfinfo executable not found. Please install Poppler or set POPPLER_PATH in settings/.env')
            return 2

        # Run pdfinfo --version (or plain pdfinfo) to show it's runnable
        try:
            proc = subprocess.run([exe, '--version'], capture_output=True, text=True, timeout=5)
            out = proc.stdout.strip() or proc.stderr.strip()
            self.stdout.write(f'pdfinfo output: {out!r}')
        except Exception as e:
            self.stderr.write(f'ERROR running pdfinfo: {e}')

        # If a PDF path is provided, call pdfinfo on it and also try pdf2image.pdfinfo_from_path
        pdf_path = options.get('pdf')
        if pdf_path:
            pdf_path = os.path.abspath(pdf_path)
            if not os.path.exists(pdf_path):
                self.stderr.write(f'Provided PDF not found: {pdf_path}')
                return 3

            # Run pdfinfo directly
            try:
                proc = subprocess.run([exe, pdf_path], capture_output=True, text=True, timeout=10)
                self.stdout.write('pdfinfo raw output:\n' + (proc.stdout or proc.stderr))
            except Exception as e:
                self.stderr.write(f'ERROR running pdfinfo on {pdf_path}: {e}')

            # Try pdf2image.pdfinfo_from_path if available
            try:
                from pdf2image import pdfinfo_from_path
                info = pdfinfo_from_path(pdf_path, poppler_path=poppler_path)
                self.stdout.write('pdf2image.pdfinfo_from_path returned:')
                for k, v in (info or {}).items():
                    self.stdout.write(f'  {k}: {v}')
            except Exception as e:
                self.stderr.write(f'pdf2image.pdfinfo_from_path failed: {e}')

        return 0
