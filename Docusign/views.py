import os
import tempfile
import base64
from io import BytesIO

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse, Http404, HttpResponse
from django.views import View
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from pdf2image import convert_from_path, pdfinfo_from_path

from .models import Request, Document, Sign, Signature
from .forms import SignatureRequestForm, DocumentUploadForm, RequestForm, PossibleSignerForm, SignatureForm

from django.contrib.auth import get_user_model
User = get_user_model()


class UserSearchView(LoginRequiredMixin, View):
    def get(self, request):
        q = request.GET.get('q', '').strip()
        results = []
        try:
            qs = User.objects.filter()
            if q:
                qs = User.objects.filter(username__icontains=q) | User.objects.filter(first_name__icontains=q) | User.objects.filter(last_name__icontains=q)
            qs = qs.order_by('username')[:30]
            for u in qs:
                results.append({'id': str(u.pk), 'text': getattr(u, 'get_full_name', lambda: str(u))() , 'description': getattr(u, 'section', '')})
        except Exception as e:
            print('user search error', e)
            results = []
        return JsonResponse({'results': results})


class SignatureRequestView(LoginRequiredMixin, View):
    form_class = SignatureRequestForm
    template_name = 'docusign/request_form.html'
    success_url = reverse_lazy('docusign:request_list')

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        documentform = DocumentUploadForm(request.POST, request.FILES)
        requestform = RequestForm(request.POST)
        if documentform.is_valid() and requestform.is_valid():
            document = documentform.save(commit=False)
            document.uploaded_by = request.user
            document.save()
            req = requestform.save(commit=False)
            req.document = document
            req.requester = request.user
            req.save()
            for signer_id in request.POST.getlist('signers'):
                try:
                    user = User.objects.get(pk=signer_id)
                    ps = PossibleSignerForm(data={'request': req.pk, 'signer': user.pk})
                    if ps.is_valid():
                        ps.save()
                except Exception:
                    pass
            return redirect(self.success_url)
        return render(request, self.template_name, {'form': requestform, 'form1': documentform})


class RequestListView(LoginRequiredMixin, ListView):
    model = Request
    template_name = 'docusign/request_list.html'
    context_object_name = 'requests'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().select_related('requester', 'document')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-requested_at')


class RequestDetailView(LoginRequiredMixin, View):
    template_name = 'docusign/request_detail.html'

    def get(self, request, pk):
        try:
            req = Request.objects.select_related('document', 'requester').prefetch_related('poss_signers__signer', 'signs__signer').get(pk=pk)
        except Request.DoesNotExist:
            return render(request, '404.html', status=404)

        user_profile = request.user
        can_sign = req.poss_signers.filter(signer=user_profile).exists()
        has_signed = req.signs.filter(signer=user_profile).exists()
        signed_signer_ids = list(req.signs.values_list('signer_id', flat=True))

        pages = []
        if req.document and getattr(req.document, 'file', None):
            temp_pdf_path = None
            poppler_path = getattr(settings, 'POPPLER_PATH', None)
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    for chunk in req.document.file.chunks():
                        tmp.write(chunk)
                    temp_pdf_path = tmp.name
                try:
                    info = pdfinfo_from_path(temp_pdf_path, poppler_path=poppler_path)
                    page_count = int(info.get('Pages', 0)) if info else 0
                    if page_count > 0:
                        pages = list(range(1, page_count + 1))
                except Exception as e:
                    print('pdf2image/poppler unavailable or PDF unreadable:', e, 'poppler_path=', poppler_path)
                    pages = []
            except Exception as e:
                print('Error during PDF processing:', e)
                pages = []
            finally:
                if temp_pdf_path and os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)

        context = {
            'request_obj': req,
            'can_sign': can_sign and not has_signed and req.status != 'completed',
            'has_signed': has_signed,
            'signed_signer_ids': signed_signer_ids,
            'user_signature': user_profile.sigs.order_by('-created_at').first() if hasattr(user_profile, 'sigs') else None,
            'pages': pages,
        }
        return render(request, self.template_name, context)


class RequestSignView(LoginRequiredMixin, View):
    def post(self, request, pk):
        try:
            req = Request.objects.get(pk=pk)
        except Request.DoesNotExist:
            return render(request, '404.html', status=404)
        user_profile = request.user
        if not req.poss_signers.filter(signer=user_profile).exists():
            return render(request, '403.html', status=403)
        if req.signs.filter(signer=user_profile).exists():
            return redirect(reverse_lazy('docusign:request_detail', kwargs={'pk': req.pk}))

        signature_obj = None
        sig_id = request.POST.get('signature_id')
        if sig_id:
            try:
                signature_obj = Signature.objects.get(pk=sig_id)
            except Exception:
                signature_obj = None
        if not signature_obj:
            try:
                signature_obj = user_profile.sigs.order_by('-created_at').first()
            except Exception:
                signature_obj = None

        Sign.objects.create(request=req, signer=user_profile, signature=signature_obj)
        poss_count = req.poss_signers.count()
        sign_count = req.signs.count()
        if poss_count > 0 and sign_count >= poss_count:
            req.status = 'completed'
            req.save()
        return redirect(reverse_lazy('docusign:request_detail', kwargs={'pk': req.pk}))


class PDFPreviewView(View):
    template_name = 'docusign/pdf_preview.html'

    def get(self, request, req_id):
        req = get_object_or_404(Request, pk=req_id)
        pdf_path = req.document.file.path
        images = []
        output_dir = os.path.join(settings.MEDIA_ROOT, 'docusign', 'previews')
        os.makedirs(output_dir, exist_ok=True)
        poppler_path = getattr(settings, 'POPPLER_PATH', None)
        try:
            pages = convert_from_path(pdf_path, dpi=150, poppler_path=poppler_path)
            for i, page in enumerate(pages):
                filename = f'preview_{req.id}_{i}.png'
                save_path = os.path.join(output_dir, filename)
                page.save(save_path, 'PNG')
                images.append({'page_num': i, 'url': settings.MEDIA_URL + f'docusign/previews/{filename}'})
        except Exception as e:
            print('pdf2image/poppler failed for preview:', e, '(poppler_path=' + str(poppler_path) + ')')
            try:
                import fitz
                doc = fitz.open(pdf_path)
                for i in range(doc.page_count):
                    p = doc.load_page(i)
                    pix = p.get_pixmap(dpi=150)
                    filename = f'preview_{req.id}_{i}.png'
                    save_path = os.path.join(output_dir, filename)
                    with open(save_path, 'wb') as f:
                        f.write(pix.tobytes('png'))
                    images.append({'page_num': i, 'url': settings.MEDIA_URL + f'docusign/previews/{filename}'})
            except Exception as fitz_err:
                print('PyMuPDF fallback failed for preview:', fitz_err)

        # include user's saved signature templates (if available on the user object)
        user_sigs = []
        try:
            user_sigs = request.user.sigs.order_by('-created_at')
        except Exception:
            user_sigs = []

        return render(request, self.template_name, {'req': req, 'images': images, 'user_sigs': user_sigs})
        


class DocumentPageImageView(LoginRequiredMixin, View):
    def get(self, request, pk, page):
        try:
            doc = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            raise Http404('Document not found')
        if not doc.file:
            raise Http404('No file attached')
        temp_pdf_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                for chunk in doc.file.chunks():
                    tmp.write(chunk)
                temp_pdf_path = tmp.name
            poppler_path = getattr(settings, 'POPPLER_PATH', None)
            try:
                images = convert_from_path(temp_pdf_path, first_page=page, last_page=page, poppler_path=poppler_path)
                if not images:
                    raise Http404('Page not found')
                img = images[0]
                img_bytes = BytesIO()
                img.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                return HttpResponse(img_bytes.getvalue(), content_type='image/png')
            except Exception as conv_err:
                print('convert_from_path failed:', conv_err, 'poppler_path=', poppler_path)
                try:
                    import fitz
                    doc_fitz = fitz.open(temp_pdf_path)
                    if page < 1 or page > doc_fitz.page_count:
                        raise Http404('Page not found')
                    p = doc_fitz.load_page(page - 1)
                    pix = p.get_pixmap(dpi=200)
                    png_bytes = pix.tobytes('png')
                    return HttpResponse(png_bytes, content_type='image/png')
                except Exception as fitz_err:
                    print('PyMuPDF fallback failed:', fitz_err)
                    return HttpResponse('PDF rendering unavailable on server', status=503, content_type='text/plain')
        finally:
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)


class SignatureUploadView(LoginRequiredMixin, View):
    def post(self, request):
        form = SignatureForm(request.POST, request.FILES)
        # ensure the owner's presence on the form instance before validation
        try:
            form.instance.owner = request.user
        except Exception:
            pass
        print("SignatureForm")
        if form.is_valid():
            print("form.is_valid")
            sig = form.save(commit=False)
            # owner should already be attached to form.instance, but enforce it again
            try:
                sig.owner = request.user
            except Exception:
                pass
            sig.save()
            print("sig.save")
            return JsonResponse({'id': sig.pk, 'url': sig.image.url})
        print('errors', form.errors)
        return JsonResponse({'errors': form.errors}, status=400)


class SignatureCanvasUploadView(LoginRequiredMixin, View):
    def post(self, request):
        data_url = request.POST.get('image') or request.body.decode('utf-8')
        if not data_url:
            return JsonResponse({'error': 'No image data provided'}, status=400)
        if data_url.startswith('data:'):
            header, encoded = data_url.split(',', 1)
            try:
                file_ext = header.split('/')[1].split(';')[0]
            except Exception:
                file_ext = 'png'
        else:
            encoded = data_url
            file_ext = 'png'
        try:
            decoded = base64.b64decode(encoded)
        except Exception:
            return JsonResponse({'error': 'Invalid image data'}, status=400)
        file_name = f'signature_{request.user.pk}_{int(__import__("time").time())}.{file_ext}'
        from django.core.files.base import ContentFile
        content = ContentFile(decoded, name=file_name)
        sig = Signature(owner=request.user)
        sig.image.save(file_name, content)
        sig.save()
        return JsonResponse({'id': sig.pk, 'url': sig.image.url})


class DocumentView(LoginRequiredMixin, View):
    def get(self, request, pk):
        try:
            doc = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            raise Http404('Document not found')
        if not doc.file:
            raise Http404('No file attached to this document')
        fh = doc.file.open('rb')
        filename = getattr(doc.file, 'name', str(pk)).split('/')[-1]
        resp = FileResponse(fh, content_type='application/pdf')
        resp['Content-Disposition'] = f'inline; filename="{filename}"'
        return resp


class ApplySignatureView(LoginRequiredMixin, View):
    """Apply a saved signature image onto a specific page/location of a PDF and save a new signed Document."""
    def post(self, request):
        import json, time
        from django.core.files import File as DjangoFile

        try:
            payload = json.loads(request.body.decode('utf-8'))
        except Exception:
            payload = request.POST.dict()

        req_id = payload.get('req_id')
        try:
            page = int(payload.get('page', 0))
        except Exception:
            page = 0
        sig_id = payload.get('signature_id')
        try:
            x_pct = float(payload.get('x_pct'))
            y_pct = float(payload.get('y_pct'))
            w_pct = float(payload.get('w_pct'))
            h_pct = float(payload.get('h_pct'))
        except Exception:
            return JsonResponse({'error': 'Invalid placement coordinates'}, status=400)

        req = get_object_or_404(Request, pk=req_id)
        if not req.document or not getattr(req.document, 'file', None):
            return JsonResponse({'error': 'No source document'}, status=400)

        try:
            signature = Signature.objects.get(pk=sig_id)
        except Exception:
            return JsonResponse({'error': 'Signature not found'}, status=404)

        # Use PyMuPDF to composite the signature onto the PDF
        try:
            import fitz
        except Exception:
            return JsonResponse({'error': 'Server-side PDF editing requires PyMuPDF (fitz).'}, status=503)

        src_pdf_path = req.document.file.path
        output_dir = os.path.join(settings.MEDIA_ROOT, 'docusign', 'signed')
        os.makedirs(output_dir, exist_ok=True)
        out_name = f'signed_{req.id}_{int(time.time())}.pdf'
        out_path = os.path.join(output_dir, out_name)

        try:
            doc = fitz.open(src_pdf_path)
            if page < 0 or page >= doc.page_count:
                return JsonResponse({'error': 'Page out of range'}, status=400)
            p = doc.load_page(page)
            page_rect = p.rect

            # compute placement rectangle in PDF coordinates
            x = page_rect.x0 + (x_pct * page_rect.width)
            y = page_rect.y0 + (y_pct * page_rect.height)
            w = w_pct * page_rect.width
            h = h_pct * page_rect.height
            img_rect = fitz.Rect(x, y, x + w, y + h)

            sig_path = signature.image.path
            # insert image
            p.insert_image(img_rect, filename=sig_path)

            doc.save(out_path)
            doc.close()

            # Save as new Document model instance
            from django.core.files import File as DFile
            with open(out_path, 'rb') as f:
                django_file = DFile(f)
                new_doc = Document(title=(req.document.title or 'Signed Document'), uploaded_by=request.user)
                new_doc.file.save(out_name, django_file, save=True)

            signed_url = settings.MEDIA_URL + f'docusign/signed/{out_name}'
            return JsonResponse({'signed_url': signed_url, 'signed_doc_id': new_doc.pk})
        except Exception as e:
            print('ApplySignatureView error:', e)
            return JsonResponse({'error': 'Failed to apply signature: ' + str(e)}, status=500)
