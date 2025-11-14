from django.views import View
from django import forms
import json
from django.shortcuts import render, redirect
from django.db import transaction
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q
# Assume these are available and imported correctly
from .models import Document, Request, PossibleSigner
from it.users.models import UserProfile 
from django.contrib.auth.mixins import LoginRequiredMixin 
from django.http import HttpResponseBadRequest
from .forms import *


class UserSearchView(LoginRequiredMixin, View):
    """AJAX endpoint for searching users for the signers select.

    Returns JSON in Select2-compatible format: { results: [{id, text, description}, ...] }
    """
    def get(self, request):
        q = request.GET.get('q', '').strip()
        results = []
        try:
            if q:
                qs = UserProfile.objects.filter(
                    Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
                ).order_by('username')[:30]
            else:
                qs = UserProfile.objects.all().order_by('username')[:30]

            for u in qs:
                # try to find a plausible avatar/url attribute on the UserProfile
                icon = ''
                for attr in ('avatar_url', 'photo_url', 'avatar', 'photo', 'image'):
                    if hasattr(u, attr):
                        try:
                            val = getattr(u, attr)
                            if callable(val):
                                val = val()
                            if val:
                                icon = str(val)
                                break
                        except Exception:
                            continue

                results.append({
                    'id': str(u.pk),
                    'text': u.get_full_name() or getattr(u, 'username', str(u.pk)),
                    'description': getattr(u, 'section', '') if hasattr(u, 'section') else '',
                    'icon': icon,
                })
        except Exception:
            # On error return empty list (don't surface internal errors to client)
            results = []

        # Ensure description and icon are JSON serializable (strings)
        safe_results = []
        for r in results:
            desc = r.get('description')
            if desc is None:
                desc_text = ''
            else:
                try:
                    desc_text = str(desc)
                except Exception:
                    desc_text = ''

            icon = r.get('icon') or ''
            try:
                icon_text = str(icon)
            except Exception:
                icon_text = ''

            safe_results.append({
                'id': r.get('id', ''),
                'text': r.get('text', ''),
                'description': desc_text,
                'icon': icon_text,
            })

        return JsonResponse({'results': safe_results})

# --- Minimal Class-Based View (Mock helper function removed) ---
class SignatureRequestView(LoginRequiredMixin, View):
    # Use the form class itself, not an instance
    form_class = SignatureRequestForm
    template_name = 'docusign/request_form.html'
    success_url = reverse_lazy('docusign:dashboard')
    print('aaaaaaaaaaaaaaaaaaaa')

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST, request.FILES)
        print('aaaaaaaaaaaaaaaaaaaass')
        if form.is_valid():
            title = form.cleaned_data['title']
            doc_file = form.cleaned_data['file']
            # signers is a list of selected user PKs (strings)
            signer_ids = form.cleaned_data['signers']
            # Resolve selected IDs to UserProfile instances while preserving order
            if not signer_ids:
                return HttpResponseBadRequest("No signers selected.")
            users_qs = UserProfile.objects.filter(pk__in=signer_ids)
            users_map = {str(u.pk): u for u in users_qs}
            signer_profiles = [users_map[pk] for pk in signer_ids if pk in users_map]
            
            # if mapping produced no valid users, reject
            if not signer_profiles:
                return HttpResponseBadRequest("No valid signers selected.")
            
            try:
                with transaction.atomic():
                    # 1. Create Document
                    doc = Document.objects.create(
                        title=title,
                        file=doc_file,
                        uploaded_by=request.user
                    )

                    # 2. Create Request
                    req = Request.objects.create(
                        document=doc,
                        requester=request.user,
                        status='pending'
                    )

                    # 3. Create PossibleSigner records
                    signer_objects = [
                        PossibleSigner(request=req, signer=signer)
                        for signer in signer_profiles
                    ]
                    PossibleSigner.objects.bulk_create(signer_objects)

                return redirect(self.success_url)

            except Exception as e:
                # Log error 'e'
                return HttpResponseBadRequest("An error occurred during transaction.")

        return render(request, self.template_name, {'form': form})