"""
View for displaying latest GraphQL error logs
"""
from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, Http404
import os
import re
from datetime import datetime


class LatestGraphQLErrorView(LoginRequiredMixin, View):
    """Display the latest GraphQL error HTML file"""
    
    def get(self, request):
        # Path to the latest_error.html file
        error_file_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'graphql_errors', 
            'latest_error.html'
        )
        
        try:
            if os.path.exists(error_file_path):
                with open(error_file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                return HttpResponse(html_content, content_type='text/html')
            else:
                raise Http404("No GraphQL error file found")
        except Exception as e:
            return HttpResponse(
                f"<html><body><h1>Error reading file</h1><p>{str(e)}</p></body></html>",
                content_type='text/html'
            )
