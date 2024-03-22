from django.shortcuts import render, redirect
from django.views import View
from .models import *
from .forms import *
from .models import Category
import os


def view_competence(request):
        
        url_path = request.path.split("/")
        url_path = request.path.split("/")
        return render(request, 'competence_building/competence.html', {
                      "url_path": url_path})

def view_charts(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/charts.html', {
                      "url_path": url_path})

def view_headoffice(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/headoffice.html', {
                      "url_path": url_path})

def view_regionaloffice(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/regionaloffice.html', {
                      "url_path": url_path})

def view_jobdescription(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/jobdescription.html', {
                      "url_path": url_path})

def view_IT(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/IT.html', {
                      "url_path": url_path})

def view_finance(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/finance.html', {
                      "url_path": url_path})
   
def view_humanresource(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/humanresource.html', {
                      "url_path": url_path})

def view_losscontrol(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/losscontrol.html', {
                      "url_path": url_path})

def view_engineering(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/engineering.html', {
                      "url_path": url_path})

def view_commercial(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/commercial.html', {
                      "url_path": url_path})

def view_district(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/district.html', {
                      "url_path": url_path})

def view_sales(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/sales.html', {
                      "url_path": url_path})

def view_networkdevelopment(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/networkdevelopment.html', {
                      "url_path": url_path})

def view_operations(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/operations.html', {
                      "url_path": url_path})
        return render(request, 'competence_building/operations.html')

def view_suplies(request):
        return render(request, 'competence_building/suplies.html')

def view_southdistrict(request):
        return render(request, 'competence_building/southdistrict.html')

def view_southglenview(request):
        return render(request, 'competence_building/southglenview.html')

def view_southwaterfalls(request):
        return render(request, 'competence_building/southwaterfalls.html')

def view_southsales(request):
        return render(request, 'competence_building/southsales.html')

def view_northdistrict(request):
        return render(request, 'competence_building/northdistrict.html')

def view_northkuwadzana(request):
        return render(request, 'competence_building/northkuwadzana.html')

def view_northmabelreign(request):
        return render(request, 'competence_building/northmabelreign.html')

def view_northwarrenpark(request):
        return render(request, 'competence_building/northwarrenpark.html')

def view_northsales(request):
        return render(request, 'competence_building/northsales.html')

def view_eastdistrict(request):
        return render(request, 'competence_building/eastdistrict.html')

def view_eastcbd(request):
        return render(request, 'competence_building/eastcbd.html')

def view_eastborrowdale(request):
        return render(request, 'competence_building/eastborrowdale.html')

def view_eastmabvuku(request):
        return render(request, 'competence_building/eastmabvuku.html')

def view_eastruwa(request):
        return render(request, 'competence_building/eastruwa.html')

def view_chitownsales(request):
        return render(request, 'competence_building/chitownsales.html')

def view_eastsales(request):
        return render(request, 'competence_building/eastsales.html')

def view_chitownseke(request):
        return render(request, 'competence_building/chitownseke.html')

def view_chitownzengeza(request):
        return render(request, 'competence_building/chitownzengeza.html')

def view_chitowndistrict(request):
        return render(request, 'competence_building/chitowndistrict.html')

def view_itjobdescription(request):
        return render(request, 'competence_building/itjobdescription.html')

def view_hrjobdescription(request):
        return render(request, 'competence_building/hrjobdescription.html')

def view_srjobdescription(request):
        return render(request, 'competence_building/srjobdescription.html')

def view_riskjobdescription(request):
        return render(request, 'competence_building/riskjobdescription.html')

def view_procjobdescription(request):
        return render(request, 'competence_building/procjobdescription.html')

def view_legaljobdescription(request):
        return render(request, 'competence_building/legaljobdescription.html')

def view_finjobdescription(request):
        return render(request, 'competence_building/finjobdescription.html')

def view_engjobdescription(request):
        return render(request, 'competence_building/engjobdescription.html')

def view_comjobdescription(request):
        return render(request, 'competence_building/comjobdescription.html')

def view_infojobdescription(request):
        return render(request, 'competence_building/infojobdescription.html')

def view_eastengineering(request):
        return render(request, 'competence_building/eastengineering.html')

def view_easternregion(request):
        return render(request, 'competence_building/easternregion.html')

def view_chitownengineering(request):
        return render(request, 'competence_building/chitownengineering.html')

def view_northengineering(request):
        return render(request, 'competence_building/northengineering.html')

def view_southengineering(request):
        return render(request, 'competence_building/southengineering.html')

def view_southertoncommercial(request):
        return render(request, 'competence_building/southertoncommercial.html')

def view_rfqview(request):
        return render(request, 'competence_building/rfqview.html')


def view_upload_file(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)  
            document.created_by = request.user
            if not document.name:  # If name is not given in the form
                file_name = request.FILES['file'].name
                document.name = os.path.splitext(file_name)[0]  # Set document name from uploaded file
            document.save()  # Commit the changes to the database
            return redirect('/') 
    return render(request, 'competence_building/upload_file.html', {'form': DocumentForm()})

def view_categories(request):
        return render(request, 'competence_building/categories.html', {'categories': Category.objects.all()})


def view_files(request, category):
    category_obj = Category.objects.get(id=category)
    files = category_obj.document_set.all()
    return render(request, 'competence_building/files.html', {'files': files})



def uploaded_jobs_view(request):
#     Fetches job descriptions and renders them in a table.
    documents = Document.objects.all()  # Fetch all documents
    context = {'documents': documents}
    return render(request, 'competence_building/competence_index.html', context)