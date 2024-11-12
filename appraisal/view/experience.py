from django.forms import BaseModelForm
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.generic.edit import CreateView
from ..models import Experience
from ..forms import ExperienceForm


class ExperienceCreateView(CreateView):
    """View for creating new Experiences"""
    model = Experience
    form_class = ExperienceForm
    template_name = 'appraisal/experience/create.html'

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        self.object = form.save()
        
        if self.request.POST.get("popup"):
            # JSON response that inject JavaScript to close the popup and refresh the parent
            js_injector = "<script>opener.refreshExperienceDropdown(); window.close();</script>"
            return HttpResponse(js_injector)
        return super().form_valid(form)



def experience_list_api(request):
    """
    API endpoint to retrieve a list of all experiences.

    This view retrieves all experience records from the database, selecting 
    the `id`, `name`, and `created_date` fields. The experiences are ordered 
    by the `created_date` in descending order (newest first). The data is then 
    returned in JSON format as a response.

    Args:
        request: The HTTP request object. It is passed by Django when the API 
                 endpoint is called. This argument is unused in the function 
                 but is required by Django's view system.

    Returns:
        JsonResponse: A JSON response containing a list of experiences, with 
                      fields `id`, `name`, and `created_date`. The response 
                      is set to `safe=False` to allow the serialization of 
                      non-dict objects (in this case, a list of dictionaries).

    Example:
        GET /api/experiences/
        Response:
        [
            {"id": 1, "name": "Experience 1", "created_date": "2024-11-01T12:00:00"},
            {"id": 2, "name": "Experience 2", "created_date": "2024-10-20T09:30:00"},
            ...
        ]
    """
    experiences = Experience.objects.all().values("id", "name", "created_date").order_by("-created_date")
    return JsonResponse(list(experiences), safe=False)
