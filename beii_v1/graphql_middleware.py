"""
Middleware to log all GraphQL requests and errors
"""
import json
import traceback
import os
from datetime import datetime
from django.conf import settings


class GraphQLLoggingMiddleware:
    """Log all GraphQL requests and responses"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Create error directory
        self.error_dir = os.path.join(settings.BASE_DIR, 'graphql_errors')
        os.makedirs(self.error_dir, exist_ok=True)
    
    def __call__(self, request):
        # Capture GraphQL request data
        query_text = None
        variables = {}
        operation_name = None
        
        if request.path == '/gql/' or 'graphql' in request.path.lower():
            if request.method == 'POST':
                try:
                    body = json.loads(request.body.decode('utf-8'))
                    query_text = body.get('query', 'N/A')
                    variables = body.get('variables', {})
                    operation_name = body.get('operationName', 'N/A')
                except Exception as e:
                    pass
        
        # Get response
        try:
            response = self.get_response(request)
            
            # Save GraphQL errors to HTML
            if request.path == '/gql/' or 'graphql' in request.path.lower():
                if response.status_code >= 400:
                    try:
                        content = response.content.decode('utf-8')
                        
                        # Save error to HTML file
                        self._save_error_html(
                            query=query_text,
                            variables=variables,
                            operation_name=operation_name,
                            response_content=content,
                            status_code=response.status_code
                        )
                    except:
                        pass
            
            return response
            
        except Exception as e:
            # Save exception to HTML file
            if request.path == '/gql/' or 'graphql' in request.path.lower():
                self._save_error_html(
                    query=query_text,
                    variables=variables,
                    operation_name=operation_name,
                    exception=str(e),
                    traceback_text=traceback.format_exc()
                )
            
            raise
    
    def _save_error_html(self, query=None, variables=None, operation_name=None, 
                        response_content=None, status_code=None, exception=None, traceback_text=None):
        """Save error details to HTML file - overwrite previous errors"""
        try:
            timestamp = datetime.now()
            filename = 'latest_error.html'  # Always use the same filename
            filepath = os.path.join(self.error_dir, filename)
            
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>GraphQL Error - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: #dc3545;
            color: white;
            padding: 20px 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 2px solid #dc3545;
        }}
        .error-box {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        pre {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            border: 1px solid #dee2e6;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .code {{
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.5;
        }}
        .timestamp {{
            color: rgba(255,255,255,0.8);
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚠️ GraphQL Error</h1>
            <div class="timestamp">{timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')}</div>
            {f'<div class="timestamp">Status Code: {status_code}</div>' if status_code else ''}
        </div>
        <div class="content">
            {f'<div class="section"><div class="section-title">Exception</div><div class="error-box">{exception}</div></div>' if exception else ''}
            
            {f'<div class="section"><div class="section-title">Response Content</div><pre class="code">{response_content}</pre></div>' if response_content else ''}
            
            {f'<div class="section"><div class="section-title">Query</div><pre class="code">{query}</pre></div>' if query else ''}
            
            {f'<div class="section"><div class="section-title">Variables</div><pre class="code">{json.dumps(variables, indent=2)}</pre></div>' if variables else ''}
            
            {f'<div class="section"><div class="section-title">Operation Name</div><div>{operation_name}</div></div>' if operation_name else ''}
            
            {f'<div class="section"><div class="section-title">Stack Trace</div><pre class="code">{traceback_text}</pre></div>' if traceback_text else ''}
        </div>
    </div>
</body>
</html>
"""
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)
            
        except Exception as e:
            pass  # Silently fail
    
    def process_exception(self, request, exception):
        """Catch exceptions during request processing"""
        if request.path == '/gql/' or 'graphql' in request.path.lower():
            # Save to HTML
            self._save_error_html(
                exception=str(exception),
                traceback_text=traceback.format_exc()
            )
        return None
