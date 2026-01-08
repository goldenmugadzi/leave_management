"""
Views for document operations
"""
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views import View
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import Request, Document, Sign, Signature, UserProfile
from io import BytesIO
from PIL import Image
import qrcode
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import json
import os



@require_http_methods(["GET"])
def download_with_qr(request, request_id):
    """
    Download document with QR code added to last page bottom center
    """
    try:
        # Get the signing request
        signing_request = Request.objects.get(id=request_id)
        document = signing_request.document
        
        if not document or not document.file:
            return HttpResponseNotFound("Document not found")
        
        # Read the PDF file
        document.file.open('rb')
        pdf_content = document.file.read()
        document.file.close()
        
        # Create PDF reader
        pdf_buffer = BytesIO(pdf_content)
        reader = PdfReader(pdf_buffer)
        writer = PdfWriter()
        
        # Generate QR code with verification URL (frontend URL)
        frontend_host = request.get_host().split(':')[0]  # Get hostname without port
        verification_url = f"http://{frontend_host}:3000/view-request/{request_id}"
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(verification_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code to BytesIO
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # Process all pages
        num_pages = len(reader.pages)
        for page_num in range(num_pages):
            page = reader.pages[page_num]
            writer.add_page(page)
        
        # Add a new verification information page
        verification_packet = BytesIO()
        page_width = float(reader.pages[0].mediabox.width)
        page_height = float(reader.pages[0].mediabox.height)
        ver_canvas = canvas.Canvas(verification_packet, pagesize=(page_width, page_height))
        
        # Title
        ver_canvas.setFont("Helvetica-Bold", 16)
        ver_canvas.drawCentredString(page_width / 2, page_height - 60, "Document Verification Information")
        
        # Draw a line
        ver_canvas.line(50, page_height - 80, page_width - 50, page_height - 80)
        
        # Verification section - compact and bold
        y_position = page_height - 105
        ver_canvas.setFont("Helvetica-Bold", 10)
        ver_canvas.drawString(50, y_position, "Verification Details:")
        
        y_position -= 20
        ver_canvas.setFont("Helvetica-Bold", 8)
        ver_canvas.drawString(70, y_position, f"Document: {document.title}")
        
        y_position -= 14
        ver_canvas.drawString(70, y_position, f"Request ID: {request_id}")
        
        y_position -= 14
        ver_canvas.drawString(70, y_position, f"Status: {signing_request.status}")
        
        y_position -= 14
        ver_canvas.drawString(70, y_position, f"Requested At: {signing_request.requested_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Signers information - compact and bold
        y_position -= 25
        ver_canvas.setFont("Helvetica-Bold", 10)
        ver_canvas.drawString(50, y_position, "Signers:")
        
        y_position -= 18
        ver_canvas.setFont("Helvetica-Bold", 8)
        signs = signing_request.signs.all()
        if signs.exists():
            for sign in signs:
                signer_name = sign.signer.username if sign.signer else "Unknown"
                signed_at = sign.signed_at.strftime('%Y-%m-%d %H:%M:%S') if sign.signed_at else "N/A"
                ver_canvas.drawString(70, y_position, f"• {signer_name} - Signed at: {signed_at}")
                y_position -= 14
        else:
            ver_canvas.drawString(70, y_position, "No signatures yet")
            y_position -= 14
        
        # QR Code for verification
        y_position -= 25
        ver_canvas.setFont("Helvetica-Bold", 11)
        ver_canvas.drawString(50, y_position, "Verify Online:")
        
        y_position -= 20
        ver_canvas.setFont("Helvetica", 8)
        ver_canvas.drawString(70, y_position, "Scan the QR code or visit the link:")
        
        # Add QR code (smaller size)
        y_position -= 80
        qr_buffer.seek(0)
        qr_display_size = 70
        qr_x_centered = (page_width - qr_display_size) / 2
        ver_canvas.drawImage(ImageReader(qr_buffer), qr_x_centered, y_position, width=qr_display_size, height=qr_display_size)
        
        # Add verification link
        y_position -= 12
        ver_canvas.setFont("Helvetica", 7)
        ver_canvas.setFillColorRGB(0, 0, 1)
        link_width = ver_canvas.stringWidth(verification_url, "Helvetica", 7)
        link_x = (page_width - link_width) / 2
        ver_canvas.drawString(link_x, y_position, verification_url)
        ver_canvas.linkURL(verification_url, (link_x, y_position - 2, link_x + link_width, y_position + 8), relative=0)
        
        # Disclaimer section
        y_position -= 40
        ver_canvas.line(50, y_position, page_width - 50, y_position)
        y_position -= 25
        ver_canvas.setFont("Helvetica-Bold", 11)
        ver_canvas.setFillColorRGB(0, 0, 0)
        ver_canvas.drawString(50, y_position, "DISCLAIMER")
        
        y_position -= 20
        ver_canvas.setFont("Helvetica", 8)
        disclaimer_text = [
            "This document has been digitally signed using PKI technology.",
            "",
            "IMPORTANT - DOCUMENT VERIFICATION:",
            "• Recipients MUST verify this document's authenticity using the QR code or link above",
            "• Any modification after signing will invalidate the signature",
            "• Forged or altered documents are INVALID and may constitute fraud",
            "• Always verify signatures before acting on the content of this document",
            "",
            "LIABILITY DISCLAIMER:",
            "• ZETDC (Zimbabwe Electricity Transmission and Distribution Company) shall NOT be held",
            "  accountable for any misconduct, damages, or losses that may arise from:",
            "  - Use of forged, altered, or tampered documents",
            "  - Failure to verify document authenticity before use",
            "  - Misuse or unauthorized distribution of this document",
            "  - Any actions taken based on unverified documents",
            "",
            "• Recipients assume full responsibility for verifying document authenticity",
            "• ZETDC's liability is limited to documents verified through official channels only",
            "",
            "For verification or questions, visit the URL above or contact ZETDC directly.",
        ]
        
        for line in disclaimer_text:
            if y_position < 40:  # Stop if running out of space
                break
            ver_canvas.drawString(70, y_position, line)
            y_position -= 11
        
        ver_canvas.save()
        
        # Add the verification page to the PDF
        verification_packet.seek(0)
        verification_pdf = PdfReader(verification_packet)
        writer.add_page(verification_pdf.pages[0])
        
        # Apply read-only protection - prevent editing but allow printing and copying
        # Get encryption password from environment variable (empty string = no password)
        encryption_password = os.environ.get('PDF_ENCRYPTION_PASSWORD', '')
        writer.encrypt(
            user_password=encryption_password,
            owner_password=None,  # No owner password needed
            permissions_flag=0b0000010100110100  # Allow printing and copying, but prevent editing
        )
        
        # Write to output
        output_buffer = BytesIO()
        writer.write(output_buffer)
        output_buffer.seek(0)
        
        # Create response
        response = HttpResponse(output_buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{document.title}_with_qr.pdf"'
        
        return response
        
    except Request.DoesNotExist:
        return HttpResponseNotFound("Signing request not found")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return HttpResponse(f"Error: {str(e)}", status=500)


# Placeholder class-based views for URL routing
class SignatureRequestView(View):
    """View for creating new signature requests"""
    def get(self, request):
        return JsonResponse({"message": "GET signature request form"})
    
    def post(self, request):
        return JsonResponse({"message": "POST create signature request"})


class UserSearchView(View):
    """View for searching users"""
    def get(self, request):
        query = request.GET.get('q', '')
        users = UserProfile.objects.filter(username__icontains=query)[:10]
        return JsonResponse({
            "users": [{"id": u.id, "username": u.username} for u in users]
        })


class RequestListView(ListView):
    """View for listing signature requests"""
    model = Request
    template_name = 'docusign/request_list.html'
    context_object_name = 'requests'


class RequestDetailView(DetailView):
    """View for viewing signature request details"""
    model = Request
    template_name = 'docusign/request_detail.html'
    context_object_name = 'request'


class PDFPreviewView(View):
    """View for previewing PDF"""
    def get(self, request, req_id):
        return JsonResponse({"message": f"Preview PDF for request {req_id}"})


class RequestSignView(View):
    """View for signing a request"""
    def post(self, request, pk):
        return JsonResponse({"message": f"Sign request {pk}"})


class DocumentView(View):
    """View for viewing a document"""
    def get(self, request, pk):
        try:
            document = Document.objects.get(pk=pk)
            if document.file:
                response = HttpResponse(document.file.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'inline; filename="{document.title}.pdf"'
                return response
            return HttpResponseNotFound("Document file not found")
        except Document.DoesNotExist:
            return HttpResponseNotFound("Document not found")


class SignatureUploadView(View):
    """View for uploading signature images"""
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        return JsonResponse({"message": "Signature uploaded"})


class SignatureCanvasUploadView(View):
    """View for uploading canvas-drawn signatures"""
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        return JsonResponse({"message": "Canvas signature uploaded"})


class ApplySignatureView(View):
    """View for applying signature to document"""
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        return JsonResponse({"message": "Signature applied"})


class DocumentPageImageView(View):
    """View for rendering PDF page as image"""
    def get(self, request, pk, page):
        return JsonResponse({"message": f"Render page {page} of document {pk}"})

