from typing import List, Optional
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models.query import QuerySet
from django.core.files.uploadedfile import UploadedFile
from django.core.files.storage import default_storage

from ..models import KeyResultArea, YearQuarter,  Appraisal, KeyResultAreaOutCome, DepartmentOutput, AppraisalDepartmentOutput, AppraisalOutPutPerformanceDimensionScore, OutPutPerformanceDimension, ScoreDocument
from ..helpers.types.kra import KRAType, TargetScoreType, KraRolesCreateType, ActivityType, PerformanceDimensionType
from it.users.models import UserProfile, Application, Roles, Designations
from loguru import logger

class KRARepository:
    def create(self, data: KRAType, creator: UserProfile) -> Optional[KeyResultArea]:
        """
            Creates a new KeyResultArea (KRA) record in the database.

            Args:
                creator (UserProfile): The user creating the KRA.
                data (KRAType): The data object containing the key result area description and goal description.

            Returns:
                KeyResultArea: The newly created KRA object on success.
                None: If a KRA with the same key_result_area_description already exists.

            Raises:
                Exception: If any other unexpected error occurs during creation.
        """
        try:
            return KeyResultArea.objects.create(
                key_result_area_description=data.key_result_area_description,
                goal_description=data.goal_description,
                created_by=creator
            )
        except IntegrityError as e:
            # Unique constraint violation: KRA already exists
            logger.warning("KRA Create Repo failed, KRA with 'key_result_area_description' already exists")
            return None
        except Exception as e:
            raise Exception(f"KRA Create Repo failed with error: {e}")
    
    def fetch_all(self):
        return KeyResultArea.objects.all()
    
    def retrieve_by_id(self, kra_id: int):
        try:
            qr = KeyResultArea.objects.filter(id=kra_id)
            if not qr.exists():
                return None
            
            return qr.first()
        except Exception as e:
            raise Exception(f"KRA retrieve_by_id Repo with pk: {kra_id}, failed with error: {e}")

    def update(self, kra_object: KeyResultArea, data: KRAType, updated_by: UserProfile) -> KeyResultArea:
        """
            Updates the fields of a KeyResultArea object and saves the changes to the database.

            Args:
                kra_object (KeyResultArea): The KRA object to be updated.
                updated_by: UserProfile object
                data (KRAType): The data object containing the name, description, and weight of the KRA.

            Returns:
                KeyResultArea: The updated KRA object.

            Raises:
                KRAUpdateError: If the update operation fails.
        """
        try:
            # Update fields only if they have changed
            updated = False

            if kra_object.key_result_area_description != data.key_result_area_description:
                kra_object.key_result_area_description = data.key_result_area_description
                updated = True

            if kra_object.goal_description != data.goal_description:
                kra_object.goal_description = data.goal_description
                updated = True
                
            if kra_object.updated_by != updated_by:
                kra_object.updated_by = updated_by
                updated = True

            # Save only if changes were made
            if updated:
                kra_object.save()

            return kra_object

        except Exception as e:
            raise Exception(f"KRA update Repo failed with error: {e}")

class KRAOutComeRepository:
    def create(self, outcome_description: str, kra_obj: KeyResultArea)->KeyResultAreaOutCome:
        """
            Creates a new KeyResultAreaOutCome (KRA) record in the database.

            Args:
                outcome_description: Outcome description name
                kra_obj: KeyResultArea object.

            Returns:
                KeyResultAreaOutCome: The newly created KeyResultAreaOutCome object.

            Raises:
                Exception: If the creation operation fails.
        """

        try:
            return KeyResultAreaOutCome.objects.create(key_result_area=kra_obj, outcome_description=outcome_description)
        except Exception as e:
            raise Exception(f"KRAOutComeRepository Create Repo failed with error: {e}")

    def fetch_all(self):
        return KeyResultAreaOutCome.objects.all()
    
    def fetch_by_kra_id(self, kra_id: int):
        try:
            return KeyResultAreaOutCome.objects.filter(key_result_area__id=kra_id)
        except Exception as e:
            raise Exception(f"KRAOutComeRepository fetch_by_kra_id with pk: {kra_id}, failed with error: {e}")

    def update(self, kra_outcome_object: KeyResultAreaOutCome, outcome_description: str) -> KeyResultArea:
        """
            Updates the fields of a KeyResultArea object and saves the changes to the database.

            Args:
                kra_outcome_object (KeyResultArea): The KRA object to be updated.
                outcome_description (str): description of the KRA outcome.

            Returns:
                KeyResultArea: The updated KRA outcome object.

            Raises:
                KRAUpdateError: If the update operation fails.
        """
        try:
            # Update fields only if they have changed
            updated = False

            if kra_outcome_object.outcome_description != outcome_description:
                kra_outcome_object.outcome_description = outcome_description
                updated = True

            # Save only if changes were made
            if updated:
                kra_outcome_object.save()

            return kra_outcome_object

        except Exception as e:
            raise Exception(f"KRAOutComeRepository with object pk: {kra_outcome_object.id} update Repo failed with error: {e}")


class YearQuarterRepository:
    def fetch_by_year(self, year: int)->QuerySet[YearQuarter]:
        try:
            return YearQuarter.objects.filter(year=year)
        except Exception as e:
            raise Exception(f"[YearQuarterRepository] fetch_by_year Repo with year: {year}, failed with error: {e}")
    
    def get_by_year_quarter(self, year: int, quarter: int)->YearQuarter:
        try:
            qr = YearQuarter.objects.filter(year=year, quarter=quarter)
            return qr.first()
        except Exception as e:
            raise Exception(f"[YearQuarterRepository] get_by_year_quarter Repo with year: {year}, quarter: {quarter}, failed with error: {e}")

class AppraisalDepartmentOutputRepository:
    def create(self, appraisal_object: Appraisal, department_output_obj: DepartmentOutput, year_quarter_obj: YearQuarter)->AppraisalDepartmentOutput:
        try:
            return AppraisalDepartmentOutput.objects.create(appraisal=appraisal_object, department_output=department_output_obj, year_quarter=year_quarter_obj)
        except Exception as e:
            raise Exception(f"[AppraisalDepartmentOutputRepository] Create Repo failed with error: {e}")

    def update(self, appraisal_department_output_object: AppraisalDepartmentOutput, appraisal_object: Appraisal, department_output_obj: DepartmentOutput, year_quarter_obj: YearQuarter)->AppraisalDepartmentOutput:
        try:
            is_changed = False
            
            if appraisal_department_output_object.appraisal != appraisal_object:
                appraisal_department_output_object.appraisal = appraisal_object
                is_changed = True
            
            if appraisal_department_output_object.department_output != department_output_obj:
                appraisal_department_output_object.department_output = department_output_obj
                is_changed = True
            
            if appraisal_department_output_object.year_quarter != year_quarter_obj:
                appraisal_department_output_object.year_quarter = year_quarter_obj
                is_changed = True
            
            if is_changed:
                appraisal_department_output_object.save()
                
            return appraisal_department_output_object
        except Exception as e:
            raise Exception(f"[AppraisalDepartmentOutputRepository] Create Repo failed with error: {e}")

    def fetch_by_appraisal_id_and_year(self, appraisal_id: int, year: int)->QuerySet[AppraisalDepartmentOutput]:
        try:
            return AppraisalDepartmentOutput.objects.filter(appraisal__id=appraisal_id, year_quarter__year=year).select_related('appraisal', 'department_output', 'department_output__department_objective', 'year_quarter')
        except Exception as e:
            raise Exception(f"[AppraisalDepartmentOutputRepository] fetch_by_appraisal_id_and_year, appraisal id: {appraisal_id} and year: {year}, failed with error: {e}")
    
    def get_by_id(self, appraisal_department_output_id: int)->AppraisalDepartmentOutput:
        try:
            qr = AppraisalDepartmentOutput.objects.filter(id=appraisal_department_output_id).select_related('appraisal', 'department_output', 'appraisal__user')
            
            if not qr.exists():
                return None
            return qr.first()
        except Exception as e:
            raise Exception(f"[AppraisalDepartmentOutputRepository] get_by_id, appraisal_department_output id: {appraisal_department_output_id}, failed with error: {e}")



class AppraisalOutPutPerformanceDimensionScoreRepository:
    def create(self, appraisal_department_output_obj: AppraisalOutPutPerformanceDimensionScore, perf_dimension_obj: OutPutPerformanceDimension)->AppraisalOutPutPerformanceDimensionScore:
        try:
            return AppraisalOutPutPerformanceDimensionScore.objects.create(appraisal_department_output=appraisal_department_output_obj, performance_dimension=perf_dimension_obj)
        except Exception as e:
            raise Exception(f"[AppraisalOutPutPerformanceDimensionScoreRepository] Create Repo failed with error: {e}")
    
    def bulk_create(self, appraisal_output_perf_dimension_objs_list: List[AppraisalOutPutPerformanceDimensionScore])->bool:
        try:
            AppraisalOutPutPerformanceDimensionScore.objects.bulk_create(appraisal_output_perf_dimension_objs_list)
            return True
        except Exception as e:
            raise Exception(f"[AppraisalOutPutPerformanceDimensionScoreRepository] bulk_create Repo failed with error: {e}")

    def update(self, appraisal_perf_dimension: AppraisalOutPutPerformanceDimensionScore, score: float, comments: str, is_scored: bool, appraiser_confirmation: str)->AppraisalOutPutPerformanceDimensionScore:
        try:
            is_changed = False
            
            if appraisal_perf_dimension.score != score:
                appraisal_perf_dimension.score = score
                is_changed = True
                
            if appraisal_perf_dimension.comments != comments:
                appraisal_perf_dimension.comments = comments
                is_changed = True
                
            if appraisal_perf_dimension.is_scored != is_scored:
                appraisal_perf_dimension.is_scored = is_scored
                is_changed = True
                
            if appraisal_perf_dimension.appraiser_confirmation != appraiser_confirmation:
                appraisal_perf_dimension.appraiser_confirmation = appraiser_confirmation
                is_changed = True
                
            if is_changed:
                appraisal_perf_dimension.save()
            return appraisal_perf_dimension
        except Exception as e:
            raise Exception(f"[AppraisalOutPutPerformanceDimensionScoreRepository] update Repo with pk: {appraisal_perf_dimension.id}, failed with error: {e}")

    def fetch_by_department_output_id(self, appraisal_department_output_id: int)->QuerySet[AppraisalOutPutPerformanceDimensionScore]:
        try:
            return AppraisalOutPutPerformanceDimensionScore.objects.filter(appraisal_department_output__id=appraisal_department_output_id).select_related('appraisal_department_output', 'performance_dimension', 'appraisal_department_output__department_output')
        except Exception as e:
            raise Exception(f"[AppraisalOutPutPerformanceDimensionScoreRepository] fetch_by_department_output_id Repo with pk: {appraisal_department_output_id}, failed with error: {e}")
    
    def fetch_by_department_objective_id(self, department_objective_id: int)->QuerySet[AppraisalOutPutPerformanceDimensionScore]:
        try:
            return AppraisalOutPutPerformanceDimensionScore.objects.filter(appraisal_department_output__department_output__department_objective__id=department_objective_id).select_related('appraisal_department_output', 'performance_dimension', 'appraisal_department_output__department_output')
        except Exception as e:
            raise Exception(f"[AppraisalOutPutPerformanceDimensionScoreRepository] fetch_by_department_objective_id Repo with pk: {department_objective_id}, failed with error: {e}")
    
    def fetch_by_year_quarter_id(self, year_quarter_id: int)->QuerySet[AppraisalOutPutPerformanceDimensionScore]:
        try:
            return AppraisalOutPutPerformanceDimensionScore.objects.filter(appraisal_department_output__year_quarter__id=year_quarter_id).select_related('appraisal_department_output', 'performance_dimension', 'appraisal_department_output__department_output')
        except Exception as e:
            raise Exception(f"[AppraisalOutPutPerformanceDimensionScoreRepository] fetch_by_year_quarter_id Repo with pk: {year_quarter_id}, failed with error: {e}")
    
    def fetch_by_appraisal_id_year_quarter_id(self, year_quarter_id: int, appraisal_id: int)->QuerySet[AppraisalOutPutPerformanceDimensionScore]:
        try:
            return AppraisalOutPutPerformanceDimensionScore.objects.filter(appraisal_department_output__year_quarter__id=year_quarter_id, appraisal_department_output__appraisal__id=appraisal_id).select_related('appraisal_department_output', 'performance_dimension', 'appraisal_department_output__department_output')
        except Exception as e:
            raise Exception(f"[AppraisalOutPutPerformanceDimensionScoreRepository] fetch_by_year_quarter_id Repo with pk: {year_quarter_id}, failed with error: {e}")
    
    def get_by_id(self, pk: int)->AppraisalOutPutPerformanceDimensionScore:
        try:
            qr = AppraisalOutPutPerformanceDimensionScore.objects.filter(appraisal_department_output__id=pk).select_related('appraisal_department_output', 'performance_dimension', 'appraisal_department_output__department_output')
            
            
            if not qr.exists():
                return None
            
            return qr.first()
        except Exception as e:
            raise Exception(f"[AppraisalOutPutPerformanceDimensionScoreRepository] get_by_id Repo with pk: {pk}, failed with error: {e}")

class ScoreDocumentRepository:
    def create(self, performance_dimension_score: AppraisalOutPutPerformanceDimensionScore, name: str, documents: str)->ScoreDocument:
        try:
            return ScoreDocument.objects.create(performance_dimension_score=performance_dimension_score, name=name, documents=documents)
        except Exception as e:
            raise Exception(f"[ScoreDocumentRepository] Create Repo failed with error: {e}")

    def delete_obj(self, score_doc_obj: ScoreDocument)->None:
        try:
            document_path = score_doc_obj.documents.path
            
            if not default_storage.exists(document_path):
                raise Exception("ScoreDocument  does not exist")
            
            score_doc_obj.delete()
            default_storage.delete(document_path)   
        except Exception as e:
            raise ValueError(f"[ScoreDocumentRepository]  delete_obj with ID {score_doc_obj.id} failed with error: {e}")

    def update(self, score_doc_obj: ScoreDocument, name: str, file: UploadedFile)->ScoreDocument:
        try:
            if score_doc_obj.name != name:
                score_doc_obj.name = name
            score_doc_obj.documents = file
            score_doc_obj.save()
            return score_doc_obj
        except Exception as e:
            raise Exception(f"ScoreDocumentRepository update repo with score doc obj pk: {score_doc_obj.id},  failed with error: {e}")
        
    def fetch_by_score_id(self, score_obj_id: int)->QuerySet[ScoreDocument]:
        try:
            return ScoreDocument.objects.filter(performance_dimension_score__id=score_obj_id)
        except Exception as e:
            raise Exception(f"ScoreDocumentRepository fetch_by_score_obj_id repo with score_obj pk: {score_obj_id},  failed with error: {e}")
    
    def get_by_id(self, pk: int)->ScoreDocument:
        try:
            qr = ScoreDocument.objects.filter(id=pk)
            if not qr.exists():
                return None
            
            return qr.first()
        except Exception as e:
            raise Exception(f"ScoreDocumentRepository get_by_id repo with score_doc_obj pk: {pk},  failed with error: {e}")
       