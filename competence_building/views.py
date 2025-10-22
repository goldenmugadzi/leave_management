from datetime import datetime
import json
import shutil
import logging
from django.shortcuts import render, redirect
from django.http import FileResponse, HttpResponseForbidden, HttpResponseNotFound
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from beii_v1 import settings
from .models import *
from .forms import *
from .models import Category
import os
from .forms import DocumentForm,editDocumentForm
from .models import Subcategory

# Configure logger for security events
logger = logging.getLogger(__name__)

@login_required
def view_competence(request):
        
        url_path = request.path.split("/")
        url_path = request.path.split("/")
        return render(request, 'competence_building/competence.html', {
                      "url_path": url_path})

@login_required
def view_qualifications(request):
    
    file_type = Category.objects.filter(name="Qualifications").first()
    first_category = Subcategory.objects.filter(category=file_type).all()
    folders_list = []
    for folder in first_category:
        url = ""
        if folder.name.count(" ") > 0:
            url = folder.name.replace(" ", "_").lower()
        else:
            url = folder.name.lower()  
            
        temp = {
            "id": folder.id,
            "name": folder.name,
            "url": url
        }
        folders_list.append(temp)

    url_path = request.path.split("/")
    return render(request, 'competence_building/qualifications.html',{"folders": folders_list, "page_title": "Qualifications Documents", "url_path": url_path} )

@login_required
def view_qualifications_files(request, folder_name):
    name = ""
    if folder_name.count("_") > 0:
        name = folder_name.replace("_", " ").lower()
    else:
        name = folder_name.lower()
    
    file_type = Category.objects.filter(name="Qualifications").first()
    print("file type: ", file_type.id)
    first_category = Subcategory.objects.filter(category=file_type, name=name).first()
    print("subcate: ", first_category.id)
    files = Document.objects.filter(archive=False, category=file_type, subcategory=first_category).all()
    print("files: ", files)
    
    url_path = request.path.split("/")
    return render(request, 'competence_building/itjobdescription.html',{"Documents": files, "page_title": "Qualifications Documents", "url_path": url_path} )


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
    """
    Secure file download with authentication and logging.
    Prevents unauthorized access to sensitive documents containing PII.
    """
    try:
        file_id = request.GET.get('file_id')
        
        if not file_id:
            logger.warning(f"Download attempt without file_id by user {request.user.username}")
            messages.error(request, "File ID is required")
            return redirect('/competence/competence')
        
        file_record = Document.objects.filter(id=file_id).first()
        
        if not file_record:
            logger.warning(f"Download attempt for non-existent file {file_id} by user {request.user.username}")
            messages.error(request, "File not found")
            return HttpResponseNotFound("File not found")
        
        # Log successful download attempt
        logger.info(f"File download: file_id={file_id}, filename={file_record.name}, user={request.user.username}, user_id={request.user.id}")
        
        # Verify file exists
        if not file_record.file or not os.path.exists(file_record.file.path):
            logger.error(f"File path not found on disk: {file_record.file.path if file_record.file else 'No path'}, file_id={file_id}")
            messages.error(request, "File not found on server")
            return HttpResponseNotFound("File not available")
        
        return FileResponse(file_record.file, content_type='application/pdf')
        
    except Exception as ex:
        logger.error(f"Error downloading file: {str(ex)}, user={request.user.username}, file_id={file_id}")
        messages.error(request, "Error downloading file")
        return redirect('/competence/competence')


@login_required
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

def view_procurement(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/procurement.html', {
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
    category= Category.objects.filter(name="Job Description").first()
    subcategory= Subcategory.objects.filter(name="Information Technology").first()
    documents = Document.objects.filter(category=category, subcategory=subcategory).all()
    return render(request, 'competence_building/itjobdescription.html', {"Documents": documents})

def view_hrjobdescription(request):
         subcategory = Subcategory.objects.filter(name="Human Resource").first()
         documents = Document.objects.filter(subcategory=subcategory).all()  # Fetch all documents
         return render(request, 'competence_building/itjobdescription.html', {"Documents": documents})

def view_srjobdescription(request):
         subcategory = Subcategory.objects.filter(name="Stakeholder Relations").first()
         documents = Document.objects.filter(subcategory=subcategory).all()  
         return render(request, 'competence_building/itjobdescription.html', {"Documents": documents})

def view_riskjobdescription(request):
         subcategory = Subcategory.objects.filter(name="Risk Management").first()
         documents = Document.objects.filter(subcategory=subcategory).all()  
         return render(request, 'competence_building/itjobdescription.html', {"Documents": documents})

def view_procjobdescription(request):
         subcategory = Subcategory.objects.filter(name="Procurement").first()
         documents = Document.objects.filter(subcategory=subcategory).all()  
         return render(request, 'competence_building/itjobdescription.html', {"Documents": documents})

def view_legaljobdescription(request):
         subcategory = Subcategory.objects.filter(name="Legal Services").first()
         documents = Document.objects.filter(subcategory=subcategory).all()  # Fetch all documents
         return render(request, 'competence_building/itjobdescription.html', {"Documents": documents})

def view_finjobdescription(request):
         subcategory = Subcategory.objects.filter(name="Finance").first()
         documents = Document.objects.filter(subcategory=subcategory).all()  
         return render(request, 'competence_building/itjobdescription.html', {"Documents": documents})

def view_engjobdescription(request):
         subcategory = Subcategory.objects.filter(name="Engineering").first()
         documents = Document.objects.filter(subcategory=subcategory).all() 
         return render(request, 'competence_building/itjobdescription.html', {"Documents": documents})

def view_comjobdescription(request):
         subcategory = Subcategory.objects.filter(name="Commercial").first()
         documents = Document.objects.filter(subcategory=subcategory).all()  
         return render(request, 'competence_building/itjobdescription.html', {"Documents": documents})

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
            logger.info(f"Document uploaded: id={document.id}, name={document.name}, user={request.user.username}")
            messages.success(request, "Document uploaded successfully")
            return redirect('/competence/upload_file') 
        else:
            logger.warning(f"Invalid form submission for document upload by user {request.user.username}")
            messages.error(request, "Error uploading document. Please check the form.")
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
    try:
        for file in documents:
            subcategory = None
            try:
                subcategory = file.subcategory
            except:
                subcategory = "None"
                
            new_file = {
            "id":file.id,
            "category": file.category,
            "sub_category":subcategory,
            "region": file.region,
            "archive": file.archive,
            "name": file.name,
            "file": file.file,
            "created by": file.created_by,
            "created at": file.created_at,
            }
            files_list.append(new_file)
    except Exception as e:
        print(e)
    
    context = json.dumps(files_list, default=str)

    return render(request, 'competence_building/competence_index.html', {"context": context, 'page':'competence_index'})

@login_required
def archived_documents(request):
    # Fetches job descriptions and renders them in a table.
    documents = Document.objects.filter(archive=True).all()  # Fetch all documents
    files_list = []
    try:
        for file in documents:
            subcategory = None
            try:
                subcategory = file.subcategory
            except:
                subcategory = "None"
                
            new_file = {
            "id":file.id,
            "region": file.region,
            "category": file.category,
            "sub_category":subcategory,
            "archive": file.archive,
            "file": file.file,
            "name": file.name,
            "created by": file.created_by,
            "created at": file.created_at,
            }
            files_list.append(new_file)
    except Exception as e:
        print(e)
    
    context = json.dumps(files_list, default=str)
#     context = {'documents': documents}
    return render(request, 'competence_building/competence_index.html', {"context": context})

@login_required
def archive_file(request, file_id):
    um = Document.objects.filter(id=file_id).first()
    if um:
        um.archive=True
        um.save()
        logger.info(f"Document archived: id={file_id}, name={um.name}, user={request.user.username}")
        messages.success(request, "Document archived successfully")
    else:
        logger.warning(f"Archive attempt for non-existent file {file_id} by user {request.user.username}")
        messages.error(request, "Document not found")
    
    return redirect('/competence/competence_index')

@login_required
def unarchive_file(request, file_id):
    um = Document.objects.filter(id=file_id).first()
    if um:
        um.archive=False
        um.save()
        logger.info(f"Document unarchived: id={file_id}, name={um.name}, user={request.user.username}")
        messages.success(request, "Document unarchived successfully")
    else:
        logger.warning(f"Unarchive attempt for non-existent file {file_id} by user {request.user.username}")
        messages.error(request, "Document not found")
    
    return redirect('/competence/archive')

@login_required
def edit_document(request, document_id):
    document = Document.objects.get(pk=document_id)

    if request.method == 'POST':
        form = editDocumentForm(request.POST, request.FILES, instance=document) 

        if form.is_valid():
            form.save()
            logger.info(f"Document edited: id={document_id}, name={document.name}, user={request.user.username}")
            messages.success(request, "Document updated successfully")
            return redirect('competence_index') 
        else:
            logger.warning(f"Invalid form submission for document edit by user {request.user.username}, document_id={document_id}")
            messages.error(request, "Error updating document. Please check the form.")

    else:
        form = editDocumentForm(instance=document)

    context = {'document': document, 'form': form}
    return render(request, 'competence_building/edit_document.html', context)


@login_required
def view_archived_documents(request):
    # This function appears to be incomplete and has errors
    # It should be removed or properly implemented
    messages.error(request, "This function is not properly implemented")
    return redirect('/competence/competence_index') 


@login_required
def create_subcategory(request):
    if request.method == 'POST':
      
        pass
    else:
        form = Subcategory()  
    context = {'form': form, 'subcategories': Subcategory.objects.all()}
    return render(request, 'competence_building/subcategory.html', context)

@login_required
def vacancies_view(request):
    # Fetches job vacancies and renders them in a table.
    category= Category.objects.filter(name="Vacancies").first()
    vacancies = Document.objects.filter(category=category,archive=False).all()
    vacancies_list = []
    for vacancy in vacancies: 
        new_vacancy = {
        "id":vacancy.id,
        "region": vacancy.region,
        "subcategory":vacancy.subcategory,
        # "department": vacancy.department,
        "archive": vacancy.archive,
        # "file": vacancy.file,
        "name": vacancy.name,
        "created_by": vacancy.created_by,
        "created_at": vacancy.created_at,
        }
        vacancies_list.append(new_vacancy)
    
    context = json.dumps(vacancies_list, default=str)
    return render(request, 'competence_building/vacancies.html', {"context": context, 'page':'vacancies'})

@login_required
def safetycircula_view(request):
        category= Category.objects.filter(name="Safety and Healthy").first()
        safetycircula = Document.objects.filter(category=category,archive=False).all()
        safetycircula_list = []
        for safety in safetycircula: 
                new_safety = {
                "id":safety.id,
                "region": safety.region,
                "archive": safety.archive,
                "name": safety.name,
                "subcategory": safety.subcategory,
                "created_by": safety.created_by,
                "created_at": safety.created_at,
                }
                safetycircula_list.append(new_safety)

        context = json.dumps(safetycircula_list, default=str)
        return render(request, 'competence_building/safety.html', {"context": context, 'page':'safety'})

@login_required
def trainingDevelopment_view(request):
        category= Category.objects.filter(name="Training and Development").first()
        trainingDevelopment = Document.objects.filter(category=category,archive=False).all()
        trainingDevelopment_list = []
        for training in trainingDevelopment: 
                new_safety = {
                "id":training.id,
                "region": training.region,
                # "department": training.department,
                "archive": training.archive,
                # "section": training.section,
                "subcategory": training.subcategory,
                "file": training.file,
                "name":training.name,
                "created_by": training.created_by,
                "created_at": training.created_at,
                }
                trainingDevelopment_list.append(new_safety)

        context = json.dumps(trainingDevelopment_list, default=str)
        return render(request, 'competence_building/trainings.html', {"context": context, 'page':'training'})

@login_required
def upcomingEvents_view(request):
        category= Category.objects.filter(name="Upcoming Events").first()
        upcomingEvents = Document.objects.filter(category=category,archive=False).all()
        upcomingEvents_list = []
        for event in upcomingEvents: 
                new_event = {
                "id":event.id,
                "region": event.region,
                # "department": event.department,
                "archive": event.archive,
                # "section": event.section,
                "subcategory": event.subcategory,
                "file": event.file,
                "name":event.name,
                "created_by":event.created_by,
                "created_at": event.created_at,
                }
                upcomingEvents_list.append(new_event)

        context = json.dumps(upcomingEvents_list, default=str)
        return render(request, 'competence_building/upcoming_events.html', {"context": context, 'page':'upcoming_events'})


























# def create_subcategory(request):
#         return render(request, 'competence_building/subcategory.html', {'subcategory': Subcategory.objects.all()})

# def create_subcategory(request, pk):
#     if request.method == 'POST':
#         subcategory = Category.objects.get(id=pk)
#         form = Subcategory(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('subcategory.html') 
#         else:
#             pass
#     else:
#         form = Subcategory()  

#     context = {'form': form}
#     return render(request, 'subcategory.html', context)







