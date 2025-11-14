"""Utility helpers for Docusign. ReportLab import is guarded so the project
does not crash at import time if the optional dependency is missing.
"""
try:
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except Exception:
    canvas = None
    REPORTLAB_AVAILABLE = False

def generate_signed_pdf(document_path, signature_text, out_path):
    """Generate a simple signed PDF. Requires reportlab.

    document_path: path to original file (not used in simple stub)
    signature_text: text to render as signature
    out_path: output PDF path
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError('reportlab is not installed')

    c = canvas.Canvas(out_path)
    c.drawString(50, 800, "Signed document")
    c.drawString(50, 780, f"Signature: {signature_text}")
    c.showPage()
    c.save()
