from django.shortcuts import render

# Create your views here.
def create_change_request(request):
    
    
    return render(request, 'change_requests/create_change_request.html')

