"""
Custom GraphQL view with enhanced error handling and logging
"""
import logging
import traceback
import json
from graphene_file_upload.django import FileUploadGraphQLView
from django.http import JsonResponse, HttpResponse
from django.template import Template, Context

logger = logging.getLogger(__name__)


ERROR_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>GraphQL Error</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: #dc3545;
            color: white;
            padding: 20px 30px;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
        }
        .content {
            padding: 30px;
        }
        .section {
            margin-bottom: 30px;
        }
        .section-title {
            font-size: 18px;
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 2px solid #dc3545;
        }
        .error-box {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .error-message {
            font-weight: 600;
            color: #856404;
        }
        pre {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            border: 1px solid #dee2e6;
        }
        .code {
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.5;
        }
        .timestamp {
            color: #6c757d;
            font-size: 12px;
        }
        .variable-item {
            background: #e9ecef;
            padding: 8px 12px;
            margin: 5px 0;
            border-radius: 4px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚠️ GraphQL Execution Error</h1>
            <div class="timestamp">{{ timestamp }}</div>
        </div>
        <div class="content">
            {% if errors %}
            <div class="section">
                <div class="section-title">Errors</div>
                {% for error in errors %}
                <div class="error-box">
                    <div class="error-message">{{ error.message }}</div>
                    {% if error.path %}
                    <div style="margin-top: 10px; font-size: 12px; color: #666;">
                        Path: {{ error.path }}
                    </div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            {% if query %}
            <div class="section">
                <div class="section-title">Query</div>
                <pre class="code">{{ query }}</pre>
            </div>
            {% endif %}
            
            {% if variables %}
            <div class="section">
                <div class="section-title">Variables</div>
                {% for key, value in variables.items %}
                <div class="variable-item">
                    <strong>{{ key }}:</strong> {{ value }}
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            {% if operation_name %}
            <div class="section">
                <div class="section-title">Operation</div>
                <div>{{ operation_name }}</div>
            </div>
            {% endif %}
            
            {% if traceback %}
            <div class="section">
                <div class="section-title">Stack Trace</div>
                <pre class="code">{{ traceback }}</pre>
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""


class CustomGraphQLView(FileUploadGraphQLView):
    """
    Custom GraphQL view that adds comprehensive error handling and logging
    """
    
    def execute_graphql_request(self, request, data, query, variables, operation_name, show_graphiql=False):
        """Override to add error logging - save HTML errors to file only"""
        try:
            logger.info(f"GraphQL Request - Operation: {operation_name}")
            logger.info(f"Query: {query}")
            logger.info(f"Variables: {variables}")
            
            result = super().execute_graphql_request(
                request, data, query, variables, operation_name, show_graphiql
            )
            
            # Check for GraphQL errors and save to HTML file
            if result and hasattr(result, 'errors') and result.errors:
                logger.error(f"GraphQL Errors: {result.errors}")
                
                # Save HTML error page to file (don't return it)
                self._save_error_html(
                    query=query,
                    variables=variables,
                    operation_name=operation_name,
                    errors=result.errors
                )
                
                # Log details
                for error in result.errors:
                    logger.error(f"Error details: {error}")
                    if hasattr(error, 'original_error'):
                        logger.error(f"Original error: {error.original_error}")
                        logger.error(traceback.format_exception(
                            type(error.original_error),
                            error.original_error,
                            error.original_error.__traceback__
                        ))
            
            # Always return the GraphQL result object, never HttpResponse
            return result
            
        except Exception as e:
            logger.error(f"=== GraphQL View Exception ===")
            logger.error(f"Error: {str(e)}")
            logger.error(f"Type: {type(e)}")
            logger.error(f"Traceback:")
            tb = traceback.format_exc()
            logger.error(tb)
            
            # Print to console as well
            print(f"\n{'='*60}")
            print(f"GRAPHQL VIEW ERROR")
            print(f"{'='*60}")
            print(f"Error: {str(e)}")
            print(f"Type: {type(e)}")
            print(f"\nFull Traceback:")
            print(tb)
            print(f"{'='*60}\n")
            
            # Save HTML error page to file
            self._save_error_html(
                query=query,
                variables=variables,
                operation_name=operation_name,
                errors=[{'message': str(e), 'path': None}],
                traceback_text=tb
            )
            
            # Re-raise so GraphQL can handle it properly
            raise
    
    def _save_error_html(self, query, variables, operation_name, errors, traceback_text=None):
        """Save GraphQL errors as HTML page to file (for viewing via /eseal/errors/graphql/)"""
        from datetime import datetime
        import os
        
        # Format errors
        formatted_errors = []
        for error in errors:
            if hasattr(error, 'message'):
                formatted_errors.append({
                    'message': str(error.message),
                    'path': getattr(error, 'path', None)
                })
            elif isinstance(error, dict):
                formatted_errors.append(error)
            else:
                formatted_errors.append({
                    'message': str(error),
                    'path': None
                })
        
        template = Template(ERROR_HTML_TEMPLATE)
        context = Context({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
            'errors': formatted_errors,
            'query': query,
            'variables': variables or {},
            'operation_name': operation_name,
            'traceback': traceback_text
        })
        
        html = template.render(context)
        
        # Save to file
        try:
            from django.conf import settings
            error_dir = os.path.join(settings.BASE_DIR, 'graphql_errors')
            os.makedirs(error_dir, exist_ok=True)
            
            # Save as latest_error.html (overwrites previous)
            latest_filepath = os.path.join(error_dir, 'latest_error.html')
            with open(latest_filepath, 'w', encoding='utf-8') as f:
                f.write(html)
            
            # Also save with timestamp for history
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'error_{timestamp}.html'
            filepath = os.path.join(error_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)
            
            print(f"\n{'='*60}")
            print(f"GraphQL Error saved to: {filepath}")
            print(f"View at: /eseal/errors/graphql/")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"Could not save error HTML: {e}")

