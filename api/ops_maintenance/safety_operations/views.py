from django.shortcuts import render
from .models import ControllerInstruction, Instruction, PermitToWork, WorkerDeclaration

from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime

from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser, MultiPartParser, FileUploadParser

from django.contrib.auth import get_user_model

# Create your views here.
# CONTROLLER INSTRUCTIONS
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_controller_instruction(request):
    
    if request.method == 'POST':
        data = request.data
        cif_id = 'CIF'+datetime.now().strftime("%y%m%d%H%M")
        current_user = request.user
        print("current_user ...", request, current_user)
        
        controller_instruction = ControllerInstruction.objects.create(
            cif_id=cif_id,
            district_or_station=data['district_or_station'],
            instruction_by=current_user.username,
            instruction_to=data['received_by'],
            related_equipment=data['related_equipment'],
            received_at=datetime.now(),
            time_at=datetime.now().time(),
            created_at=datetime.now()
        )
                
        instructions = data['instruction']
        print(instructions)
        for index, instruction in enumerate(instructions):

            Instruction.objects.create(
                cif_id=cif_id,
                description=instructions[instruction],
                completed_at=datetime.now(),
                completed_status=False,
                created_at=datetime.now()
            )
        
        return JsonResponse(model_to_dict(controller_instruction), status=201)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_controller_instructions(request):
    if request.method == 'GET':
        controller_instructions = ControllerInstruction.objects.all()
        
        i = 0
        controller_instructions_list = []
        for instruction in controller_instructions:
            
            try:
                user = get_user_model().objects.get(username=instruction.instruction_by)
                
                if user:
                    data = {
                        "key": instruction.id,
                        "id": instruction.cif_id,
                        "createdBy": user.first_name + " " + user.last_name,
                        "relatedEquipment": instruction.related_equipment,
                        "status": 'PROCESSING'
                    }
                    
                    controller_instructions_list.append(data)
                    i = i+1
                    
            except Exception as ex:
                print('Exception', str(ex))
            
        return JsonResponse(controller_instructions_list, safe=False, status=200)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_controller_instruction(request):
    
    if request.method == 'POST':
        try:
            cif_id = request.data['id']
            controller_instruction = ControllerInstruction.objects.get(cif_id=cif_id)
            instruction_by = get_user_model().objects.get(username=controller_instruction.instruction_by) if controller_instruction.instruction_by else None
            instruction_to = get_user_model().objects.get(username=controller_instruction.instruction_to) if controller_instruction.instruction_to else None
            
            inst_list = []
            instructions = Instruction.objects.filter(cif_id=controller_instruction.cif_id).all()
            for inst in instructions:
                inst_dict = {
                    "key": inst.id,
                    "description": inst.description,
                    "completed_status": inst.completed_status,
                    "created_at": inst.created_at,
                    "completed_at": inst.completed_at
                }
                
                inst_list.append(inst_dict)
            
            data = {
                "key": controller_instruction.id,
                "id": controller_instruction.cif_id,
                "senior": controller_instruction.instruction_to,
                "district_or_station": controller_instruction.district_or_station, 
                "instruction_by": instruction_by.first_name + " " + instruction_by.last_name if instruction_by else "",
                "instruction_to": instruction_to.first_name + " " + instruction_to.last_name if instruction_to else "",
                "relatedEquipment": controller_instruction.related_equipment,
                "status": 'PROCESSING',
                "received_at": controller_instruction.received_at,
                "created_at": controller_instruction.created_at,
                "instructions": inst_list
            }
            
            return JsonResponse(data, status=200)
        except ControllerInstruction.DoesNotExist:
            return JsonResponse({"error": "ControllerInstruction not found"}, status=404)

@csrf_exempt
def update_controller_instruction(request, cif_id):
    
    if request.method == 'POST':
        data = request.data
        current_user = request.user
        
        try:
            controller_instruction = ControllerInstruction.objects.get(cif_id=cif_id)
            
            controller_instruction.district_or_station = data.get('district_or_station', controller_instruction.district_or_station)
            controller_instruction.instruction_by = current_user.username
            controller_instruction.instruction_to = data.get('instruction_to', controller_instruction.instruction_to)
            controller_instruction.related_equipment = data.get('related_equipment', controller_instruction.related_equipment)
            controller_instruction.received_at = datetime.now()
            
            controller_instruction.save()
            
            return JsonResponse(model_to_dict(controller_instruction), status=200)
        except ControllerInstruction.DoesNotExist:
            return JsonResponse({"error": "ControllerInstruction not found"}, status=404)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)
    
@csrf_exempt
def delete_controller_instruction(request, cif_id):
    
    if request.method == 'DELETE':
        try:
            controller_instruction = ControllerInstruction.objects.get(cif_id=cif_id)
            controller_instruction.delete()
            
            return JsonResponse({"success": "ControllerInstruction deleted successfully"}, status=200)
        except ControllerInstruction.DoesNotExist:
            return JsonResponse({"error": "ControllerInstruction not found"}, status=404)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)
    
@csrf_exempt
def update_instruction_status(request, instruction_id):
    
    if request.method == 'POST':
        data = request.data
        current_user = request.user
        
        try:
            instruction = Instruction.objects.get(id=instruction_id)
            
            instruction.completed_status = data.get('completed_status', instruction.completed_status)
            instruction.completed_by = current_user.username
            instruction.completed_at = datetime.now() if data.get('completed_status', False) else None
            
            instruction.save()
            
            return JsonResponse(model_to_dict(instruction), status=200)
        except Instruction.DoesNotExist:
            return JsonResponse({"error": "Instruction not found"}, status=404)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)

# PERMIT TO WORK VIEWS
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_permit_to_work(request):
    
    if request.method == 'POST':
        data = request.data
        cif_id = data['cif_id']
        ptw_id = "PTW"+datetime.now().strftime("%Y%m%d%H%M")
        current_user = request.user
        workers = data['workers']       
        
        permit_to_work = PermitToWork.objects.create(
            cif_id=cif_id,
            ptw_id=ptw_id,
            work_done = data['work_done'],
            plant_equipment = data['plant_equipment'],
            points_of_isolation = data['points_of_isolation'],
            nearest_points_live = data['nearest_points_live'],
            circuit_main_earths = data['circuit_main_earths'],
            danger_notices = data['danger_notices'],
            caution_notices = data['caution_notices'],
            special_keys = data['special_keys'],
            other_precautions = data['other_precautions'],
            additional_earths = data['additional_earths'],
            circuit_identity_wristlets = data['circuit_identity_wristlets'],
            responsible_official = data['responsible_official'],
            recipt_person = data['competent_person'],
            clearance_person = data['competent_person'],
            created_by=current_user.username,
            time_at=datetime.now().time(),
            created_at=datetime.now()
        )
        
        print(workers)
        # Create workers declarations
        for index, worker in enumerate(workers):
            worker_declaration = WorkerDeclaration.objects.create(
                worker_username= workers[worker],    
                ptw_id= ptw_id
            )
            
            worker_declaration.save()
        
        return JsonResponse(model_to_dict(permit_to_work), status=201)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_permit_to_work(request):
    if request.method == 'GET':
        permit_to_works = PermitToWork.objects.all()
        
        # Create a custom permit-to-works list object
        custom_permit_to_works = []
        for ptw in permit_to_works:
            user = get_user_model().objects.get(username=ptw.created_by)
            
            if user:
                custom_ptw = {
                    "issued_to": user.first_name + " " + user.last_name,
                    "cif_id": ptw.cif_id,
                    "ptw_id": ptw.ptw_id,
                    "work_done": ptw.work_done,
                    "plant_equipment": ptw.plant_equipment,
                    "points_of_isolation": ptw.points_of_isolation,
                    "nearest_points_live": ptw.nearest_points_live,
                    "circuit_main_earths": ptw.circuit_main_earths,
                    "danger_notices": ptw.danger_notices,
                    "caution_notices": ptw.caution_notices,
                    "special_keys": ptw.special_keys,
                    "other_precautions": ptw.other_precautions,
                    "additional_earths": ptw.additional_earths,
                    "circuit_identity_wristlets": ptw.circuit_identity_wristlets,
                    "created_by": ptw.created_by,
                    "created_at": ptw.created_at
                }
                
                custom_permit_to_works.append(custom_ptw)
        
        return JsonResponse(custom_permit_to_works, status=200, safe=False)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)

def get_ptw_details(id):
    try:
        print("id: ", id)
        ptw = PermitToWork.objects.get(ptw_id=id)
        
        user = get_user_model().objects.get(username=ptw.created_by)
        ptw_workers = WorkerDeclaration.objects.filter(ptw_id=ptw.ptw_id)
        # get workers
        custom_workers = []
        safe_workers = []
        not_safe_workers = []
        if ptw_workers and (len(ptw_workers) > 0):
            for worker in ptw_workers:
                safe_worker = {
                    "id": worker.id,
                    "name": worker.worker_username,
                    "signature": worker.signature_safe,
                    "date": worker.date_safe,
                    "time": worker.time_safe
                }
                safe_workers.append(safe_worker)
                not_safe_worker = {
                    "id": worker.id,
                    "name": worker.worker_username,
                    "signature": worker.signature_not_safe,
                    "date": worker.date_not_safe,
                    "time": worker.time_not_safe
                }
                not_safe_workers.append(not_safe_worker)
        
        if user:
            
            cif = ControllerInstruction.objects.get(cif_id=ptw.cif_id)
            controller_user = get_user_model().objects.get(username=cif.instruction_by)
            controller_consent_data = {}
            if controller_user:
                controller_consent_data = {
                    "username": controller_user.username,
                    "name": controller_user.first_name + " " + controller_user.last_name,
                    "time": ptw.time_at,
                    "date": ptw.created_at,
                }
            
            senior_user = get_user_model().objects.get(username=ptw.created_by)
            senior_authorization_data = {}
            if senior_user:
                senior_authorization_data = {
                    "username": ptw.created_by,
                    "name": senior_user.first_name + " " + senior_user.last_name,
                    "time": ptw.time_at,
                    "date": ptw.created_at,
                }
            
            responsible_user = get_user_model().objects.filter(username=ptw.responsible_official).first()
            responsible_official_data = {}
            if responsible_user:
                responsible_official_data = {
                    "username": ptw.responsible_official,
                    "name": responsible_user.first_name + " " + responsible_user.last_name,
                    "employ_of": "",
                    "designation": "",
                    "signature": ptw.official_signature, 
                    "time": ptw.official_time,
                    "date": ptw.official_date,
                }
            
            competent_user = get_user_model().objects.filter(username=ptw.recipt_person).first()
            receipt_person_data = {}
            if competent_user:
                receipt_person_data = {
                    "username": ptw.recipt_person,
                    "name": competent_user.first_name + " " + competent_user.last_name,
                    "signature": ptw.recipt_person_signature, 
                    "time": ptw.recipt_person_time,
                    "date": ptw.recipt_person_date,
                }
            
            clearance_data = {}
            if competent_user:
                clearance_data = {
                    "username": ptw.clearance_person,
                    "signature": ptw.clearance_signature,
                    "time": ptw.clearance_time,
                    "date": ptw.clearance_date,
                }
            
            senior_cancellation = {}
            if senior_user and controller_user:
                senior_cancellation = {
                    "username": ptw.snr_cancellation_person,
                    "controller_name": controller_user.first_name + " " + controller_user.last_name,
                    "controller_time": ptw.time_at,
                    "senior_name": senior_user.first_name + " " + senior_user.last_name,
                    "senior_signature": ptw.snr_cancellation_signature,
                    "time": ptw.snr_cancellation_time,
                    "date": ptw.snr_cancellation_date,
                }
            
            responsible_cancellation = {}
            if responsible_user:
                responsible_cancellation = {
                    "username": ptw.official_cancellation_person,
                    "name": responsible_user.first_name + " " + responsible_user.last_name,
                    "signature": ptw.official_cancellation_signature,
                    "time": ptw.official_cancellation_time,
                    "date": ptw.official_cancellation_date,
                }
            
            indirect_issue_user = get_user_model().objects.filter(username=ptw.indirect_issue).first()
            indirect_issue_data = {}
            if indirect_issue_user: 
                indirect_issue_data = {
                    "indirect_issue": ptw.indirect_issue, 
                    "name": indirect_issue_user.first_name + " " + indirect_issue_user.last_name,
                    "senior": ptw.indirect_senior,
                    "senior_name": senior_user.first_name + " " + senior_user.last_name,
                    "signature": ptw.indirect_signature, 
                    "time": ptw.indirect_time,
                    "date": ptw.indirect_date,
                }

            indirect_clearance_user = get_user_model().objects.filter(username=ptw.indirect_clearance).first()
            indirect_clearance_data = {}
            if indirect_clearance_user:             
                indirect_clearance_data = {
                    "indirect_clearance": ptw.indirect_clearance, 
                    "name": indirect_clearance_user.first_name + " " + indirect_clearance_user.last_name,
                    "senior_name": indirect_issue_user.first_name + " " + indirect_issue_user.last_name,
                    "signature": ptw.indirect_clr_signature,
                    "time": ptw.indirect_clr_time,
                    "date": ptw.indirect_clr_date,
                }
            
            custom_ptw = {
                "issued_to": user.first_name + " " + user.last_name,
                "cif_id": ptw.cif_id,
                "ptw_id": ptw.ptw_id,
                
                "work_done": ptw.work_done,
                "plant_equipment": ptw.plant_equipment,
                "points_of_isolation": ptw.points_of_isolation,
                "nearest_points_live": ptw.nearest_points_live,
                "circuit_main_earths": ptw.circuit_main_earths,
                "danger_notices": ptw.danger_notices,
                "caution_notices": ptw.caution_notices,
                "special_keys": ptw.special_keys,
                "other_precautions": ptw.other_precautions,
                "additional_earths": ptw.additional_earths,
                "circuit_identity_wristlets": ptw.circuit_identity_wristlets,
                    
                "controller_consent": controller_consent_data,
                "senior_authorization": senior_authorization_data,
                "responsible_official": responsible_official_data,
                "receipt_person": receipt_person_data,
                "clearance_data": clearance_data,
                "senior_cancellation": senior_cancellation,
                "responsible_cancellation": responsible_cancellation,
                "indirect_issue": indirect_issue_data,
                "indirect_clearance": indirect_clearance_data,
                
                "workers": custom_workers,
                "safeWorkers": safe_workers,
                "notSafeWorkers": not_safe_workers, 
                
                "created_by": ptw.created_by,
                "created_at": ptw.created_at
            }
        
            return custom_ptw
    except Exception as ex:
        print(ex)
        return None

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_permit_to_work(request):
    
    if request.method == 'POST':
        try:
            ptw_id = request.data['instruction_id']
            ptw = get_ptw_details(ptw_id)
            if ptw:
                return JsonResponse(ptw, status=200)
            else:
                return JsonResponse({"error": "PermitToWork not found"}, status=404) 
        except Exception as ex:
            print(ex)
            return JsonResponse({"error": "PermitToWork not found"}, status=404)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)
  
@csrf_exempt
def senior_authorized_approve(request, ptw_id):
    
    if request.method == 'POST':
        data = request.data
        current_user = request.user
        
        try:
            
            permit_to_work = PermitToWork.objects.get(ptw_id=ptw_id)
            
            permit_to_work.senior_authorization = current_user.username
            permit_to_work.senior_signature = data.get('senior_signature', True)
            permit_to_work.senior_time = datetime.now().time()
            permit_to_work.senior_date = datetime.now().date()
            
            permit_to_work.save()
            
            return JsonResponse(model_to_dict(permit_to_work), status=200)
        except PermitToWork.DoesNotExist:
            return JsonResponse({"error": "PermitToWork not found"}, status=404)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def responsible_official_approve(request):

    if request.method == 'POST':
        data = request.data
        ptw_id = data['ptw_id']
        status = data['status']
        
        try:
            permit_to_work = PermitToWork.objects.get(ptw_id=ptw_id)
            
            permit_to_work.official_signature = status
            permit_to_work.official_time = datetime.now().time()
            permit_to_work.official_date = datetime.now().date()
            
            permit_to_work.save()
            
            ptw = get_ptw_details(ptw_id)
            if ptw:
                return JsonResponse(ptw, status=200)
            else:
                return JsonResponse({"error": "PermitToWork not found"}, status=404) 

        except PermitToWork.DoesNotExist:
            return JsonResponse({"error": "PermitToWork not found"}, status=404)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def receipt_person_approve(request):

    if request.method == 'POST':
        data = request.data
        ptw_id = data['ptw_id']
        status = data['status']
        
        try:
            permit_to_work = PermitToWork.objects.get(ptw_id=ptw_id)
            
            permit_to_work.recipt_person_signature = status
            permit_to_work.recipt_person_time = datetime.now().time()
            permit_to_work.recipt_person_date = datetime.now().date()
            
            permit_to_work.save()
            
            ptw = get_ptw_details(ptw_id)
            if ptw:
                return JsonResponse(ptw, status=200)
            else:
                return JsonResponse({"error": "PermitToWork not found"}, status=404)
            
        except PermitToWork.DoesNotExist:
            return JsonResponse({"error": "PermitToWork not found"}, status=404)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clearance_person_approve(request):

    if request.method == 'POST':
        data = request.data
        ptw_id = data['ptw_id']
        status = data['status']
        
        try:
            permit_to_work = PermitToWork.objects.get(ptw_id=ptw_id)
            
            permit_to_work.clearance_signature = status
            permit_to_work.clearance_time = datetime.now().time()
            permit_to_work.clearance_date = datetime.now().date()
            
            permit_to_work.save()
            
            ptw = get_ptw_details(ptw_id)
            if ptw:
                return JsonResponse(ptw, status=200)
            else:
                return JsonResponse({"error": "PermitToWork not found"}, status=404)
            
        except PermitToWork.DoesNotExist:
            return JsonResponse({"error": "PermitToWork not found"}, status=404)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def snr_clearance_approve(request):

    if request.method == 'POST':
        data = request.data
        ptw_id = data['ptw_id']
        status = data['status']
        
        try:
            permit_to_work = PermitToWork.objects.get(ptw_id=ptw_id)
            
            permit_to_work.snr_cancellation_signature = status
            permit_to_work.snr_cancellation_time = datetime.now().time()
            permit_to_work.snr_cancellation_date = datetime.now().date()
            
            permit_to_work.save()
            
            ptw = get_ptw_details(ptw_id)
            if ptw:
                return JsonResponse(ptw, status=200)
            else:
                return JsonResponse({"error": "PermitToWork not found"}, status=404)
            
        except PermitToWork.DoesNotExist:
            return JsonResponse({"error": "PermitToWork not found"}, status=404)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def official_clearance_approve(request):

    if request.method == 'POST':
        data = request.data
        ptw_id = data['ptw_id']
        status = data['status']
        
        try:
            permit_to_work = PermitToWork.objects.get(ptw_id=ptw_id)
            
            permit_to_work.official_cancellation_signature = status
            permit_to_work.official_cancellation_time = datetime.now().time()
            permit_to_work.official_cancellation_date = datetime.now().date()
            
            permit_to_work.save()
            
            ptw = get_ptw_details(ptw_id)
            if ptw:
                return JsonResponse(ptw, status=200)
            else:
                return JsonResponse({"error": "PermitToWork not found"}, status=404)
            
        except PermitToWork.DoesNotExist:
            return JsonResponse({"error": "PermitToWork not found"}, status=404)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def worker_approve(request):

    if request.method == 'POST':
        data = request.data
        id = data['id']
        ptw_id = data['ptw_id']
        safe = data['safe']
        signature = data['signatureImage']

        import base64
        imgdata = base64.b64decode(signature.split(';base64,')[1])
        filename = 'uploads/signatures/ops_n_maintenance/signature'+datetime.now().strftime("%Y%m%d%H%M%S")+'.png'  # I assume you have a way of picking unique filenames
        with open(filename, 'wb') as f:
            f.write(imgdata)
            
        try:
            worker_declaration = WorkerDeclaration.objects.filter(id=id, ptw_id=ptw_id).first()
            
            if safe and safe == True:
                worker_declaration.signature_safe = True
                worker_declaration.signature_safe_path = filename
                worker_declaration.time_safe = datetime.now().time()
                worker_declaration.date_safe = datetime.now().date()
            elif safe == False:
                worker_declaration.signature_not_safe = True
                worker_declaration.signature_not_safe_path = filename
                worker_declaration.time_not_safe = datetime.now().time()
                worker_declaration.date_not_safe = datetime.now().date()
            
            worker_declaration.save()
            
            ptw = get_ptw_details(ptw_id)
            if ptw:
                return JsonResponse(ptw, status=200)
            else:
                return JsonResponse({"error": "PermitToWork not found"}, status=404)
            
        except PermitToWork.DoesNotExist:
            return JsonResponse({"error": "PermitToWork not found"}, status=404)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)


@csrf_exempt
def controller_cancellation(request, ptw_id):

    if request.method == 'POST':
        data = request.data
        current_user = request.user
        
        try:
            permit_to_work = PermitToWork.objects.get(ptw_id=ptw_id)
            
            permit_to_work.cancellation_controller = current_user.username
            permit_to_work.cancellation_senior = data.get('cancellation_senior', permit_to_work.cancellation_senior)
            permit_to_work.cancellation_status = data.get('cancellation_status', permit_to_work.cancellation_status)
            
            permit_to_work.save()
            
            return JsonResponse(model_to_dict(permit_to_work), status=200)
        except PermitToWork.DoesNotExist:
            return JsonResponse({"error": "PermitToWork not found"}, status=404)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)
    
@csrf_exempt
def indirect_issue_approve(request, ptw_id):

    if request.method == 'POST':
        data = request.data
        current_user = request.user
        
        try:
            permit_to_work = PermitToWork.objects.get(ptw_id=ptw_id)
            
            permit_to_work.indirect_issue = data.get('indirect_issue', True)
            permit_to_work.indirect_name = current_user.username
            permit_to_work.indirect_senior = data.get('indirect_senior', permit_to_work.indirect_senior)
            permit_to_work.indirect_signature = data.get('indirect_signature', True)
            permit_to_work.indirect_time = datetime.now().time()
            permit_to_work.indirect_date = datetime.now().date()
            
            permit_to_work.save()
            
            return JsonResponse(model_to_dict(permit_to_work), status=200)
        except PermitToWork.DoesNotExist:
            return JsonResponse({"error": "PermitToWork not found"}, status=404)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)

@csrf_exempt
def indirect_clearance_approve(request, ptw_id):

    if request.method == 'POST':
        data = request.data
        current_user = request.user
        
        try:
            permit_to_work = PermitToWork.objects.get(ptw_id=ptw_id)
            
            permit_to_work.indirect_clearance = data.get('indirect_clearance', permit_to_work.indirect_clearance)
            permit_to_work.indirect_clr_name = current_user.username
            permit_to_work.indirect_clr_senior = data.get('indirect_clr_senior', permit_to_work.indirect_clr_senior)
            permit_to_work.indirect_clr_signature = data.get('indirect_clr_signature', permit_to_work.indirect_clr_signature)
            permit_to_work.indirect_clr_time = datetime.now().time()
            permit_to_work.indirect_clr_date = datetime.now().date()
            
            permit_to_work.save()
            
            return JsonResponse(model_to_dict(permit_to_work), status=200)
        except PermitToWork.DoesNotExist:
            return JsonResponse({"error": "PermitToWork not found"}, status=404)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)

@csrf_exempt
def update_permit_to_work(request, ptw_id):
    
    if request.method == 'POST':
        data = request.data
        current_user = request.user
        
        try:
            permit_to_work = PermitToWork.objects.get(ptw_id=ptw_id)
            
            permit_to_work.hr_number = data.get('hr_number', permit_to_work.hr_number)
            permit_to_work.local_number = data.get('local_number', permit_to_work.local_number)
            permit_to_work.ncc_number = data.get('ncc_number', permit_to_work.ncc_number)
            permit_to_work.comments = data.get('comments', permit_to_work.comments)
            permit_to_work.serial_number = data.get('serial_number', permit_to_work.serial_number)
            permit_to_work.issue_to = data.get('issue_to', permit_to_work.issue_to)
            permit_to_work.employ_of = data.get('employ_of', permit_to_work.employ_of)
            permit_to_work.work_done = data.get('work_done', permit_to_work.work_done)
            permit_to_work.plant_equipment = data.get('plant_equipment', permit_to_work.plant_equipment)
            permit_to_work.points_of_isolation = data.get('points_of_isolation', permit_to_work.points_of_isolation)
            permit_to_work.nearest_points_live = data.get('nearest_points_live', permit_to_work.nearest_points_live)
            permit_to_work.circuit_main_earths = data.get('circuit_main_earths', permit_to_work.circuit_main_earths)
            permit_to_work.danger_notices = data.get('danger_notices', permit_to_work.danger_notices)
            permit_to_work.caution_notices = data.get('caution_notices', permit_to_work.caution_notices)
            permit_to_work.special_keys = data.get('special_keys', permit_to_work.special_keys)
            permit_to_work.other_precautions = data.get('other_precautions', permit_to_work.other_precautions)
            permit_to_work.additional_earths = data.get('additional_earths', permit_to_work.additional_earths)
            permit_to_work.circuit_identity_wristlets = data.get('circuit_identity_wristlets', permit_to_work.circuit_identity_wristlets)
            
            permit_to_work.save()
            
            return JsonResponse(model_to_dict(permit_to_work), status=200)
        except PermitToWork.DoesNotExist:
            return JsonResponse({"error": "PermitToWork not found"}, status=404)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)

@csrf_exempt
def delete_permit_to_work(request, ptw_id):
    
    if request.method == 'DELETE':
        try:
            permit_to_work = PermitToWork.objects.get(ptw_id=ptw_id)
            permit_to_work.delete()
            
            return JsonResponse({"success": "PermitToWork deleted successfully"}, status=200)
        except PermitToWork.DoesNotExist:
            return JsonResponse({"error": "PermitToWork not found"}, status=404)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)

@csrf_exempt
def controller_consent(request, ptw_id):

    if request.method == 'POST':
        data = request.data
        current_user = request.user
    
        try:
            permit_to_work = PermitToWork.objects.get(ptw_id=ptw_id)
        
            permit_to_work.controller_consent = data.get('controller_consent', True)
            permit_to_work.controller_name = current_user.username
            permit_to_work.controller_consent_time = datetime.now().time()
            permit_to_work.controller_consent_date = datetime.now().date()
        
            permit_to_work.save()
        
            return JsonResponse(model_to_dict(permit_to_work), status=200)
        except PermitToWork.DoesNotExist:
            return JsonResponse({"error": "PermitToWork not found"}, status=404)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)
 
# lia

# sft

# WORKERS
@csrf_exempt
@api_view(['GET'])
def get_ops_users(request):
    
    if request.method == 'GET':
        User = get_user_model()
        users = User.objects.all()
        user_list = [{
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username
            } for user in users]
        
        return JsonResponse(user_list, safe=False, status=200)
    else:
        
        return JsonResponse({"error": "Invalid request method"}, status=400)

 


