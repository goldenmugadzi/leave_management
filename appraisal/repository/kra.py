from typing import List, Optional
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models.query import QuerySet
from django.core.files.uploadedfile import UploadedFile
from django.core.files.storage import default_storage

from ..models import KeyResultArea, YearQuarter, Activity, TargetScore, Appraisal, AppraisalKra, AppraisalKraReviewerStatus, PerformanceDimension, ScoreDocument, KeyResultAreaOutCome
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
            return KeyResultAreaOutCome.objects.fetch(key_result_area__id=kra_id)
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


class AppraisalKraRepository:
    def create(self, appraisal_object: Appraisal, quarter_obj: YearQuarter, kra_obj: KeyResultArea=None)->AppraisalKra:
        try:
            return AppraisalKra.objects.create(appraisal=appraisal_object, quarter=quarter_obj, key_result_area=kra_obj)
        except Exception as e:
            raise Exception(f"AppraisalKra Create Repo failed with error: {e}")

    def retrieve_quarter_appraisal_id(self, quarter_number: int, year_number: int, appraisal_id: int)->QuerySet[AppraisalKra]:
            """
                Retrieves a QuerySet of KRAs for a specified quarter and year and appraisal pk.

                Args:
                    quarter_number (int): The quarter number (e.g., 1 for Q1, 2 for Q2).
                    year_number (int): The year number (e.g., 2024).

                Returns:
                    QuerySet[KeyResultArea]: A QuerySet of KeyResultArea objects matching the specified quarter and year.

                Raises:
                    Exception: If the retrieval operation fails.
            """
            try:
                queryset = AppraisalKra.objects.filter(quarter__year=year_number, quarter__quarter=quarter_number, appraisal__id=appraisal_id)
                return queryset
            except Exception as e:
                raise Exception(f"KRA retrieve by quarter and year failed with error: {e}")

    def retrieve_by_pk(self, pk: int)->AppraisalKra:
        """
            Retrieves a QuerySet of Appraisal Kra by primary key.

            Args:
                pk (int): The primary key of KRA.

            Returns:
                AppraisalKra: AppraisalKra object matching the specified primary key.

            Raises:
                Exception: If the retrieval operation fails.
        """
        try:
            qr = AppraisalKra.objects.filter(id=pk)

            if not qr.exists():
                raise Exception("AppraisalKra object not found")

            return qr.first()
        except Exception as e:
            raise Exception(f"Appraisal Kra retrieval by PK failed with error: {e}")

    def update(self, appraisal_kra_obj: AppraisalKra, quarter_obj: YearQuarter, kra_obj: KeyResultArea)->AppraisalKra:
        try:
            updated = False
            if quarter_obj != appraisal_kra_obj.quarter:
                appraisal_kra_obj.quarter = quarter_obj
                updated = True
            if kra_obj != appraisal_kra_obj.key_result_area:
                appraisal_kra_obj.key_result_area = kra_obj
                updated = True
            

            if updated:
                appraisal_kra_obj.save()
            return appraisal_kra_obj
        except Exception as e:
            raise Exception(f"KRA update Repo failed with error: {e}")


class KraActivityRepository:
    def create(self, appraisal_kra_object: AppraisalKra, data: ActivityType)->Activity:
        try:
            return Activity.objects.create(
                appraisal_kra=appraisal_kra_object,
                name=data.name,
                description=data.description,
                weight=data.weight,
                )
        except Exception as e:
            raise Exception(f"KRA Activity Create Repo failed with error: {e}")

    def fetch_by_appraisal_kra_id(self, appraisal_kra_id: int)->QuerySet[Activity]:
        try:
            queryset = Activity.objects.filter(appraisal_kra__id=appraisal_kra_id).select_related("appraisal_kra")
            return queryset
        except Exception as e:
            raise Exception(f"KRA Activity Fetch Repo failed with error: {e}")

    def update(self, activity_obj: Activity, data: ActivityType)->Activity:
        try:
            updated = False

            if data.name != activity_obj.name:
                activity_obj.name = data.name
                updated = True

            if data.description != activity_obj.description:
                activity_obj.description = data.description
                updated = True

            if data.weight != activity_obj.weight:
                activity_obj.weight = data.weight
                updated = True

            if updated:
                activity_obj.save()
            return activity_obj
        except Exception as e:
            raise Exception(f"Activity update Repo failed with error: {e}")

    def get_activity_by_id(self, activity_id: int)->Activity:
        try:
            qr = Activity.objects.filter(id=activity_id)

            if not qr.exists():
                raise Exception("Activity object not found")

            return qr.first()
        except Exception as e:
            raise Exception(f"Activity object retrieval by PK failed with error: {e}")


    def get_activity_by_appraisal_kra_pk(self, appraisal_kra_pk: int)->Activity:
        try:
            qr = Activity.objects.filter(appraisal_kra__id=appraisal_kra_pk)

            if not qr.exists():
                raise Exception("Activity object not found")

            return qr.first()
        except Exception as e:
            raise Exception(f"Activity object retrieval by PK failed with error: {e}")



class TargetScoreRepository:
    def create(self, performance_dimension: PerformanceDimension, data: TargetScoreType)->TargetScore:
        try:
            obj = TargetScore.objects.create(performance_dimension=performance_dimension, score=data.score, comments=data.comment)
            return obj
        except Exception as e:
            raise Exception(f"score create repo failed with error: {e}")

    def get_by_id(self, score_id: int)->TargetScore|None:
        try:
            qr = TargetScore.objects.select_related('performance_dimension').filter(id=score_id)

            if not qr.exists():
                return None

            return qr.first()
        except Exception as e:
            raise Exception(f"score get repo failed with error: {e}")

    def get_by_performance_dimension_id(self, performance_dimension_id: int)->TargetScore:
        try:
            qr = TargetScore.objects.select_related('performance_dimension').filter(performance_dimension__id=performance_dimension_id)
            
            if not qr.exists():
                return None

            return qr.first()
        except Exception as e:
            raise Exception(f"score get repo failed with error: {e}")

    def update(self, target_score_obj: TargetScore, data: TargetScoreType)->TargetScore:
        try:
            is_updated = False

            if target_score_obj.score != data.score:
                target_score_obj.score = data.score
                is_updated = True

            if target_score_obj.comments != data.comment:
                target_score_obj.comments = data.comment
                is_updated = True

            if not target_score_obj.is_scored:
                target_score_obj.is_scored = True
                is_updated = True
                
            if target_score_obj.appraiser_confirmation != data.appraiser_confirmation:
                target_score_obj.appraiser_confirmation = data.appraiser_confirmation
                is_updated = True

            if is_updated:
                target_score_obj.save()
            return target_score_obj
        except Exception as e:
            raise Exception(f"Target score update Repo failed with error: {e}")

    def fetch_by_appraisal_id(self, appraisal_id: int)->QuerySet[TargetScore]:
        try:
            return TargetScore.objects.filter(performance_dimension__activity__appraisal_kra__appraisal__id=appraisal_id).select_related('performance_dimension__activity__appraisal_kra__appraisal')
        except Exception as e:
            raise Exception(f"Target score fetch by appraisal pk, failed with error: {e}")

    def fetch_by_appraisal_kra_id(self, appraisal_kra_id: int)->QuerySet[TargetScore]:
        try:
            return TargetScore.objects.filter(performance_dimension__activity__appraisal_kra__id=appraisal_kra_id).select_related('performance_dimension__activity__appraisal_kra__appraisal')
        except Exception as e:
            raise Exception(f"Target score fetch by appraisal_kra pk, failed with error: {e}")

    def appraisal_kra_activities_scored(self, appraisal_kra_id: int)->bool:
        try:
            qr = TargetScore.objects.filter(performance_dimension__activity__appraisal_kra__id=appraisal_kra_id, is_scored=False)
            if qr.exists():
                return False
        except Exception as e:
            raise Exception(f"Target score fetch by appraisal_kra pk, failed with error: {e}")
        return True
    
    
    def get_by_id_up_to_process_obj(self, target_score_id: int) -> TargetScore:
        """
            Retrieve a TargetScore object along with related objects up to the Process level.

        Args:
            target_score_id (int): The ID of the TargetScore to fetch.

        Returns:
            TargetScore: The TargetScore object with related objects preloaded.

        Raises:
            ObjectDoesNotExist: If the TargetScore is not found.
        """
        try:
            return TargetScore.objects.select_related(
                'target',
                'target__activity',
                'target__activity__kra',
                'target__activity__kra__appraisal',
                'target__activity__kra__appraisal__process'
            ).get(id=target_score_id)
        except ObjectDoesNotExist:
            raise ObjectDoesNotExist("TargetScore with the given ID does not exist.")
        except Exception as e:
            raise Exception(f"Unexpected error occurred while fetching TargetScore: {e}")



class KraRolesRepository:
    def create(self, application_object: Application, data: KraRolesCreateType)->Roles:
        obj,_ = Roles.objects.get_or_create(role=data.role, name=data.name, application=application_object.name, defaults={"app_id": application_object, "description": data.description})
        return obj

    def role_exists(self, role_name: str)->bool:
        qr = Roles.objects.filter(name__iexact=role_name)
        return qr.exists()

class ApprasialKraReviewerStatusRepository:
    def create(self, appraisal_kra_obj: AppraisalKra, status: str, comment: str = None)->AppraisalKraReviewerStatus:
        try:
            object, _ = AppraisalKraReviewerStatus.objects.get_or_create(appraisal_kra=appraisal_kra_obj, defaults={"status": status, "comment": comment})
            return object
        except Exception as e:
            raise Exception(f"ApprasialKraReviewerStatusRepository create repo failed with error: {e}")

    def fetch_by_appraisal_kra_id(self, appraisal_kra_id: int)->QuerySet[AppraisalKraReviewerStatus]:
        try:
            qr = AppraisalKraReviewerStatus.objects.filter(appraisal_kra__id=appraisal_kra_id).select_related('appraisal_kra')
            return qr
        except Exception as e:
            raise Exception(f"ApprasialKraReviewerStatusRepository fetch_by_appraisal_kra_id repo failed with error: {e}")
    
    def get_by_appraisal_kra_id(self, appraisal_kra_id: int)->AppraisalKraReviewerStatus:
        try:
            qr = self.fetch_by_appraisal_kra_id(appraisal_kra_id=appraisal_kra_id)
            if not qr.exists():
                return None
            return qr.first()
        except Exception as e:
            raise Exception(f"ApprasialKraReviewerStatusRepository get_by_appraisal_kra_id repo failed with error: {e}")

    def update(self, appraisal_kra_reviewer_status_obj: AppraisalKraReviewerStatus, status: str, comment: str)->AppraisalKraReviewerStatus:
        try:
            is_changed = False
            
            if appraisal_kra_reviewer_status_obj.status != status:
                appraisal_kra_reviewer_status_obj.status = status
                is_changed = True
            if appraisal_kra_reviewer_status_obj.comment != comment:
                appraisal_kra_reviewer_status_obj.comment = comment
                is_changed = True
            if is_changed:
                appraisal_kra_reviewer_status_obj.save()
            return appraisal_kra_reviewer_status_obj
        except Exception as e:
            raise Exception(f"ApprasialKraReviewerStatusRepository update repo failed with error: {e}")

    def fetch_by_quarter_year(self, year: int)->QuerySet[AppraisalKraReviewerStatus]:
        try:
            qr = AppraisalKraReviewerStatus.objects.filter(appraisal_kra__quarter__year=year).select_related('appraisal_kra__quarter')
            return qr
        except Exception as e:
            raise Exception(f"ApprasialKraReviewerStatusRepository fetch_by_quarter_year repo failed with error: {e}")


class PerformanceDimensionRepository:
    def create(self, activity_obj: Activity, data: PerformanceDimensionType):
        try:
            return PerformanceDimension.objects.create(
                activity=activity_obj,
                description=data.description,
                performance_indicator=data.performance_indicator,
                weight=data.weight,
                agreed_target=data.agreed_target,
                allowable_variance=data.allowable_variance,
                )
        except Exception as e:
            raise Exception(f"PerformanceDimensionRepository Create Repo failed with error: {e}")

    def get_by_pk(self, performance_dimension_id: int)->PerformanceDimension:
        try:
            perf_dimension_object = PerformanceDimension.objects.select_related('activity', 'activity__appraisal_kra', 'activity__appraisal_kra__appraisal').filter(id=performance_dimension_id).first()

            if perf_dimension_object is None:
                raise Exception("PerformanceDimension object not found")

            return perf_dimension_object
        except Exception as e:
            raise Exception(f"PerformanceDimensionRepository retrieval by PK failed with error: {e}")

    def get_by_activity_id(self, activity_id: int)->PerformanceDimension:
        try:
            perf_dimension_object = PerformanceDimension.objects.select_related('activity').filter(activity__id=activity_id).first()

            if perf_dimension_object is None:
                raise Exception("PerformanceDimension object not found")

            return perf_dimension_object
        except Exception as e:
            raise Exception(f"PerformanceDimensionRepository retrieval by activity id failed with error: {e}")
    
    def fetch_by_activity_id_performance_indicator(self, activity_id: int, performance_indicator: str)->QuerySet[PerformanceDimension]:
        try:
            perf_dimension_qr = PerformanceDimension.objects.select_related('activity').filter(activity__id=activity_id, performance_indicator=performance_indicator)
            return perf_dimension_qr
        except Exception as e:
            raise Exception(f"PerformanceDimensionRepository fetch by activity id and performance indicator failed with error: {e}")
    
    def fetch_by_activity_id(self, activity_id: int)->QuerySet[PerformanceDimension]:
        try:
            return PerformanceDimension.objects.select_related('activity').filter(activity__id=activity_id)
  
        except Exception as e:
            raise Exception(f"PerformanceDimensionRepository fetch by activity id failed with error: {e}")
    
    def fetch_by_appraisal_kra_id(self, appraisal_kra_id: int)->QuerySet[PerformanceDimension]:
        try:
            return PerformanceDimension.objects.select_related('activity').filter(activity__appraisal_kra__id=appraisal_kra_id)
  
        except Exception as e:
            raise Exception(f"PerformanceDimensionRepository fetch_by_appraisal_kra_id failed with error: {e}")
    
    def fetch_by_id(self, performance_dimension_id: int)->QuerySet[PerformanceDimension]:
        try:
            return PerformanceDimension.objects.select_related('activity').filter(id=performance_dimension_id)
  
        except Exception as e:
            raise Exception(f"PerformanceDimensionRepository fetch by id failed with error: {e}")
    
    def update(self, performance_dimension_obj: PerformanceDimension, data: PerformanceDimensionType, is_applicable: bool)->PerformanceDimension:
        try:
            updated = False
            if data.description != performance_dimension_obj.description:
                performance_dimension_obj.description = data.description
                updated = True

            if data.weight != performance_dimension_obj.weight:
                performance_dimension_obj.weight = data.weight
                updated = True

            if data.performance_indicator != performance_dimension_obj.performance_indicator:
                performance_dimension_obj.performance_indicator = data.performance_indicator
                updated = True

            if data.agreed_target != performance_dimension_obj.agreed_target:
                performance_dimension_obj.agreed_target = data.agreed_target
                updated = True

            if data.allowable_variance != performance_dimension_obj.allowable_variance:
                performance_dimension_obj.allowable_variance = data.allowable_variance
                updated = True
            
            if is_applicable != performance_dimension_obj.is_applicable:
                performance_dimension_obj.is_applicable = is_applicable
                updated = True

            if updated:
                performance_dimension_obj.save()
            return performance_dimension_obj
        except Exception as e:
            raise Exception(f"PerformanceDimensionRepository update Repo failed with error: {e}")



class ScoreDocumentRepository:
    def create(self, score_obj: TargetScore, name: str, file: UploadedFile) -> ScoreDocument:
        try:
            return ScoreDocument.objects.create(name=name, target_score=score_obj, documents=file)
        except Exception as e:
            raise Exception(f"[ScoreDocumentRepository] create repo failed with error: {e}")
    
    def fetch_by_score_id(self, score_id: int)->QuerySet[ScoreDocument]:
        try:
            return ScoreDocument.objects.filter(target_score__id=score_id)
        except Exception as e:
            raise ValueError(f"[ScoreDocumentRepository]  fetch_by_score_id failed with error: {e}")
    
    
    def get_by_id(self, score_doc_id: int)->ScoreDocument|None:
        """Retrieve single obj by its id, 

        Args:
            score_doc_id (int): primary key

        Raises:
            ValueError: Unexpected error

        Returns:
            ScoreDocument|None: None if obj not found else obj is returned.
        """
        try:
            qr = ScoreDocument.objects.filter(id=score_doc_id)
            
            if not qr.exists():
                return None
            return qr.first()
        except Exception as e:
            raise ValueError(f"[ScoreDocumentRepository]  get_by_score_id failed with error: {e}")

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