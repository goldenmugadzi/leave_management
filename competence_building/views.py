from datetime import datetime
import json
import shutil
from django.shortcuts import render, redirect
from django.http import FileResponse
from django.views import View
from django.contrib.auth.decorators import login_required

from beii_v1 import settings
from .models import *
from .forms import *
from .models import Category
import os
from .forms import DocumentForm,editDocumentForm

@login_required
def view_competence(request):
        
        url_path = request.path.split("/")
        url_path = request.path.split("/")
        return render(request, 'competence_building/competence.html', {
                      "url_path": url_path})

@login_required
def bulk_create(request):
        user_id = request.user.id
        user = UserProfile.objects.filter(id=user_id).first()
        region = Regions.objects.filter(id=1).first()
        created_by = user
        created_at = datetime.now()

        files = []
        directories = []
        for root, dirnames, filename in os.walk('static/job_descriptions'):
                for filename in filename:
                        filepath = os.path.join(root, filename)
                        file_info ={
                                "name": filename,
                                "path": filepath,
                        }
                        files.append(file_info)
                        directories +=dirnames

                        if os.path.sep in root:
                                norm = os.path.normpath(root)
                                items = norm.split(os.path.sep)
                                destination_folder = 'media/'
                                destination_path = os.path.join(destination_folder, filename)

                                try:
                                        if not os.path.exists(destination_path):
                                                shutil.copy2(filepath, destination_path)
                                        else:
                                                print(f"File {filename} already exists in the destination folder.")
                                except shutil.Error as e:
                                        print(f"error occured while coping files: {e}")

                                ft = items[2] if len(items) >=3 else ""
                                dp = items[3] if len(items) >=4 else ""
                                print(ft, dp)
                                doc_ = Document.objects.filter(name=filename).first()
                                print("doc_", doc_)
                                if ft and doc_ is None:
                                        ft = ft.capitalize()
                                        section = Sections.objects.filter(section=ft).first()

                                        cat = Category.objects.filter(id=section.id).first()
                                        documentObj = Document(
                                                category=cat,
                                                name = filename,
                                                region= region,
                                                section= section,
                                                created_at = created_at,
                                                created_by = created_by,
                                                file = filename
                                                )
                                        documentObj.save()
                                        print(f"Document {filename} has been saved to the database.")
                                else:
                                        print(f"Document {filename} already exists in the database.")

        return redirect("/competence/competence")



@login_required
def download_file(request):

    file_id = request.GET['file_id']
    file_record = Document.objects.filter(id=file_id).first()
#     file_path = "media/" + file_record.file

    # search for file in system
    try:
        # base_directory_path = os.path.join(settings.BASE_DIR,file_path )

        return FileResponse(file_record.file, content_type='application/pdf')
    except Exception as ex:
        print(ex)

    return redirect('/competence/competence')


@login_required
def view_charts(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/charts.html', {
                      "url_path": url_path})

@login_required
def view_headoffice(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/headoffice.html', {
                      "url_path": url_path})

@login_required
def view_regionaloffice(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/regionaloffice.html', {
                      "url_path": url_path})

@login_required
def view_jobdescription(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/jobdescription.html', {
                      "url_path": url_path})

@login_required
def view_IT(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/IT.html', {
                      "url_path": url_path})

@login_required
def view_finance(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/finance.html', {
                      "url_path": url_path})

@login_required   
def view_humanresource(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/humanresource.html', {
                      "url_path": url_path})

@login_required
def view_losscontrol(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/losscontrol.html', {
                      "url_path": url_path})

@login_required
def view_engineering(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/engineering.html', {
                      "url_path": url_path})

@login_required
def view_commercial(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/commercial.html', {
                      "url_path": url_path})

@login_required
def view_district(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/district.html', {
                      "url_path": url_path})

@login_required
def view_sales(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/sales.html', {
                      "url_path": url_path})

@login_required
def view_networkdevelopment(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/networkdevelopment.html', {
                      "url_path": url_path})

@login_required
def view_operations(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/operations.html', {
                      "url_path": url_path})
        return render(request, 'competence_building/operations.html')

@login_required
def view_suplies(request):
        return render(request, 'competence_building/suplies.html')

@login_required
def view_southdistrict(request):
        return render(request, 'competence_building/southdistrict.html')

@login_required
def view_southglenview(request):
        return render(request, 'competence_building/southglenview.html')

@login_required
def view_southwaterfalls(request):
        return render(request, 'competence_building/southwaterfalls.html')

@login_required
def view_southsales(request):
        return render(request, 'competence_building/southsales.html')

@login_required
def view_northdistrict(request):
        return render(request, 'competence_building/northdistrict.html')

@login_required
def view_northkuwadzana(request):
        return render(request, 'competence_building/northkuwadzana.html')

@login_required
def view_northmabelreign(request):
        return render(request, 'competence_building/northmabelreign.html')

@login_required
def view_northwarrenpark(request):
        return render(request, 'competence_building/northwarrenpark.html')

@login_required
def view_northsales(request):
        return render(request, 'competence_building/northsales.html')

@login_required
def view_eastdistrict(request):
        return render(request, 'competence_building/eastdistrict.html')

@login_required
def view_eastcbd(request):
        return render(request, 'competence_building/eastcbd.html')

@login_required
def view_eastborrowdale(request):
        return render(request, 'competence_building/eastborrowdale.html')

@login_required
def view_eastmabvuku(request):
        return render(request, 'competence_building/eastmabvuku.html')

@login_required
def view_eastruwa(request):
        return render(request, 'competence_building/eastruwa.html')

@login_required
def view_chitownsales(request):
        return render(request, 'competence_building/chitownsales.html')

@login_required
def view_eastsales(request):
        return render(request, 'competence_building/eastsales.html')

@login_required
def view_chitownseke(request):
        return render(request, 'competence_building/chitownseke.html')

@login_required
def view_chitownzengeza(request):
        return render(request, 'competence_building/chitownzengeza.html')

@login_required
def view_chitowndistrict(request):
        return render(request, 'competence_building/chitowndistrict.html')

@login_required
def view_itjobdescription(request):
    section = Sections.objects.filter(section="Information Technology").first()
    documents = Document.objects.filter(section=section).all()  # Fetch all documents
    return render(request, 'competence_building/itjobdescription.html', {"Documents": documents})

@login_required
def view_hrjobdescription(request):
         section = Sections.objects.filter(section="Human Resource").first()
         documents = Document.objects.filter(section=section).all()  # Fetch all documents
         return render(request, 'competence_building/itjobdescription.html', {"Documents": documents})

@login_required
def view_srjobdescription(request):
         section = Sections.objects.filter(section="Stakeholder Relations").first()
         documents = Document.objects.filter(section=section).all()  # Fetch all documents
         return render(request, 'competence_building/itjobdescription.html', {"Documents": documents})

@login_required
def view_riskjobdescription(request):
         section = Sections.objects.filter(section="Risk Management").first()
         documents = Document.objects.filter(section=section).all()  # Fetch all documents
         return render(request, 'competence_building/itjobdescription.html', {"Documents": documents})

@login_required
def view_procjobdescription(request):
         section = Sections.objects.filter(section="Procurement").first()
         documents = Document.objects.filter(section=section).all()  # Fetch all documents
         return render(request, 'competence_building/itjobdescription.html', {"Documents": documents})

@login_required
def view_legaljobdescription(request):
         section = Sections.objects.filter(section="Legal Services").first()
         documents = Document.objects.filter(section=section).all()  # Fetch all documents
         return render(request, 'competence_building/itjobdescription.html', {"Documents": documents})

@login_required
def view_finjobdescription(request):
         section = Sections.objects.filter(section="Finance").first()
         documents = Document.objects.filter(section=section).all()  # Fetch all documents
         return render(request, 'competence_building/itjobdescription.html', {"Documents": documents})

@login_required
def view_engjobdescription(request):
         section = Sections.objects.filter(section="Engineering").first()
         documents = Document.objects.filter(section=section).all()  # Fetch all documents
         return render(request, 'competence_building/itjobdescription.html', {"Documents": documents})

@login_required
def view_comjobdescription(request):
         section = Sections.objects.filter(section="Commercial").first()
         documents = Document.objects.filter(section=section).all()  # Fetch all documents
         return render(request, 'competence_building/itjobdescription.html', {"Documents": documents})

@login_required
def view_infojobdescription(request):
        return render(request, 'competence_building/infojobdescription.html')

@login_required
def view_eastengineering(request):
        return render(request, 'competence_building/eastengineering.html')

@login_required
def view_easternregion(request):
        return render(request, 'competence_building/easternregion.html')

@login_required
def view_chitownengineering(request):
        return render(request, 'competence_building/chitownengineering.html')

@login_required
def view_northengineering(request):
        return render(request, 'competence_building/northengineering.html')

@login_required
def view_southengineering(request):
        return render(request, 'competence_building/southengineering.html')

@login_required
def view_southertoncommercial(request):
        return render(request, 'competence_building/southertoncommercial.html')

@login_required
def view_rfqview(request):
        return render(request, 'competence_building/rfqview.html')


@login_required
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

@login_required
def view_categories(request):
        return render(request, 'competence_building/categories.html', {'categories': Category.objects.all()})

@login_required
def view_files(request, category):
    category_obj = Category.objects.get(id=category)
    files = category_obj.document_set.all()
    return render(request, 'competence_building/files.html', {'files': files})

@login_required
def uploaded_jobs_view(request):
    # Fetches job descriptions and renders them in a table.
    documents = Document.objects.filter(archive=False).all()  # Fetch all documents
    files_list = []
    for file in documents:
        new_file = {
        "id":file.id,
        "region": file.region,
        "category": file.category,
        "archive": file.archive,
        "section": file.section,
        "file": file.file,
        "name": file.name,
        "created by": file.created_by,
        "created at": file.created_at,
        }
        files_list.append(new_file)
    
    context = json.dumps(files_list, default=str)
#     context = {'documents': documents}
    return render(request, 'competence_building/competence_index.html', {"context": context, 'page':'competence_index'})

@login_required
def archived_documents(request):
    # Fetches job descriptions and renders them in a table.
    documents = Document.objects.filter(archive=True).all()  # Fetch all documents
    files_list = []
    for file in documents:
        new_file = {
        "id":file.id,
        "region": file.region,
        "category": file.category,
        "archive": file.archive,
        "section": file.section,
        "file": file.file,
        "name": file.name,
        "created by": file.created_by,
        "created at": file.created_at,
        }
        files_list.append(new_file)
    
    context = json.dumps(files_list, default=str)
#     context = {'documents': documents}
    return render(request, 'competence_building/competence_index.html', {"context": context})

@login_required
def archive_file(request, file_id):

    um = Document.objects.filter(id=file_id).first()
    um.archive=True
    um.save()
    
    return redirect('/competence/competence_index')

@login_required
def unarchive_file(request, file_id):

    um = Document.objects.filter(id=file_id).first()
    um.archive=False
    um.save()
    
    return redirect('/competence/archive')

@login_required
def edit_document(request, document_id):
    document = Document.objects.get(pk=document_id)

    if request.method == 'POST':
        form = editDocumentForm(request.POST, request.FILES, instance=document) 

        if form.is_valid():
            form.save()  
            return redirect('competence_index') 

    else:
        form = editDocumentForm(instance=document)

    context = {'document': document, 'form': form}
    return render(request, 'competence_building/edit_document.html', context)


@login_required
def view_archived_documents(request):

  if request.method == 'POST':
    document.archived = True
    document.save()
  context = {'archive_document': archive_document}
  return render(request, 'archive_document', context) 








