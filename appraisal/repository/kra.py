from typing import List
from django.core.exceptions import ObjectDoesNotExist
from ..models import KeyResultArea, YearQuarter, Activity, TargetScore, Appraisal, AppraisalKra
from ..helpers.types.kra import KRAType, TargetScoreType, KraRolesCreateType
from it.users.models import UserProfile, Application, Roles

class KRARepository:
    def create(self, quarter_obj: YearQuarter, creator_obj: UserProfile, appraisal_obj: Appraisal, data: KRAType)->KeyResultArea:
        """
            Creates a new KeyResultArea (KRA) record in the database.

            Args:
                quarter_obj (YearQuarter): The quarter associated with the KRA.
                creator_obj: The user or entity responsible for creating the KRA.
                appraisal_obj: The appraisal associated with the KRA.
                data (KRAType): The data object containing the name, description, and weight of the KRA.

            Returns:
                KeyResultArea: The newly created KRA object.

            Raises:
                Exception: If the creation operation fails.
        """

        try:
            return KeyResultArea.objects.create(quarter=quarter_obj, created_by=creator_obj, name=data.name, description=data.description, weight=data.weight, appraisal=appraisal_obj)
        except Exception as e:
            raise Exception(f"KRA Create Repo failed with error: {e}")

    def retrieve(self, quarter_number: int, year_number: int)->List[KeyResultArea]:
        """
            Retrieves a list of KRAs for a specified quarter and year.

            Args:
                quarter_number (int): The quarter number (e.g., 1 for Q1, 2 for Q2).
                year_number (int): The year number (e.g., 2024).

            Returns:
                List[KeyResultArea]: A list of KeyResultArea objects matching the specified quarter and year.

            Raises:
                Exception: If the retrieval operation fails.
        """

        try:
            queryset = KeyResultArea.objects.filter(quarter__year=year_number, quarter__quarter=quarter_number)
            return queryset
        except Exception as e:
            raise Exception(f"KRA retrieve by quarter and year failed with error: {e}")
        
    def retrieve_quarter_appraisal_id(self, quarter_number: int, year_number: int, appraisal_id: int)->List[KeyResultArea]:
        """
            Retrieves a list of KRAs for a specified quarter and year and appraisal pk.

            Args:
                quarter_number (int): The quarter number (e.g., 1 for Q1, 2 for Q2).
                year_number (int): The year number (e.g., 2024).

            Returns:
                List[KeyResultArea]: A list of KeyResultArea objects matching the specified quarter and year.

            Raises:
                Exception: If the retrieval operation fails.
        """

        try:
            queryset = KeyResultArea.objects.filter(quarter__year=year_number, quarter__quarter=quarter_number, appraisal__id=appraisal_id)
            return queryset
        except Exception as e:
            raise Exception(f"KRA retrieve by quarter and year failed with error: {e}")

    def retrieve_by_pk(self, kra_id: int)->KeyResultArea:
        """
            Retrieves a list of KRA by primary key.

            Args:
                kra_id (int): The primary key of KRA.

            Returns:
                KeyResultArea: KeyResultArea object matching the specified primary key.

            Raises:
                Exception: If the retrieval operation fails.
        """
        try:
            kra_object = KeyResultArea.objects.select_related('quarter').filter(id=kra_id).first()

            if kra_object is None:
                raise Exception("KRA object not found")

            return kra_object
        except Exception as e:
            raise Exception(f"KRA retrieval by PK failed with error: {e}")

    def update(self, kra_object: KeyResultArea, quarter_obj: YearQuarter, data: KRAType) -> KeyResultArea:
        """
            Updates the fields of a KeyResultArea object and saves the changes to the database.

            Args:
                kra_object (KeyResultArea): The KRA object to be updated.
                quarter_obj (YearQuarter): The quarter to associate with the KRA.
                data (KRAType): The new data to update the KRA with.

            Returns:
                KeyResultArea: The updated KRA object.

            Raises:
                KRAUpdateError: If the update operation fails.
        """
        try:
            # Update fields only if they have changed
            updated = False

            if kra_object.quarter != quarter_obj:
                kra_object.quarter = quarter_obj
                updated = True

            if kra_object.name != data.name:
                kra_object.name = data.name
                updated = True

            if kra_object.description != data.description:
                kra_object.description = data.description
                updated = True

            if kra_object.weight != data.weight:
                kra_object.weight = data.weight
                updated = True

            # Save only if changes were made
            if updated:
                kra_object.save()

            return kra_object

        except Exception as e:
            raise Exception(f"KRA update Repo failed with error: {e}")


class AppraisalKraRepository:
    def create(self, appraisal_object: Appraisal, quarter_obj: YearQuarter, kra_obj: KeyResultArea=None, activity_object=None)->AppraisalKra:
        try:
            return AppraisalKra.objects.create(appraisal=appraisal_object, quarter=quarter_obj, kra_reference=kra_obj, activity_reference=activity_object)
        except Exception as e:
            raise Exception(f"AppraisalKra Create Repo failed with error: {e}")
    
    def retrieve_quarter_appraisal_id(self, quarter_number: int, year_number: int, appraisal_id: int)->List[AppraisalKra]:
            """
                Retrieves a list of KRAs for a specified quarter and year and appraisal pk.

                Args:
                    quarter_number (int): The quarter number (e.g., 1 for Q1, 2 for Q2).
                    year_number (int): The year number (e.g., 2024).

                Returns:
                    List[KeyResultArea]: A list of KeyResultArea objects matching the specified quarter and year.

                Raises:
                    Exception: If the retrieval operation fails.
            """
            try:
                queryset = AppraisalKra.objects.filter(quarter__year=year_number, quarter__quarter=quarter_number, appraisal__id=appraisal_id)
                return queryset
            except Exception as e:
                raise Exception(f"KRA retrieve by quarter and year failed with error: {e}")

    
class KraActivityRepository:
    def create(self, kra_obj: KeyResultArea, data: KRAType)->Activity:
        try:
            return Activity.objects.create(kra=kra_obj, name=data.name, description=data.description, weight=data.weight)
        except Exception as e:
            raise Exception(f"KRA Activity Create Repo failed with error: {e}")

    def fetch_by_kra_id(self, kra_id: int)->List[Activity]:
        try:
            queryset = Activity.objects.filter(kra__id=kra_id)
            return queryset
        except Exception as e:
            raise Exception(f"KRA Activity Fetch Repo failed with error: {e}")

    def update(self, activity_obj: Activity, assigned_user: UserProfile, appraiser: UserProfile, data: KRAType)->Activity:
        try:
            updated = False
            if assigned_user != activity_obj.assigned_user:
                activity_obj.assigned_user = assigned_user
                updated = True

            if appraiser != activity_obj.appraiser:
                activity_obj.appraiser = appraiser
                updated = True

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
            raise Exception(f"KRA update Repo failed with error: {e}")

    def get_activity_by_id(self, activity_id: int)->Activity:
        try:
            activity_object = Activity.objects.select_related('kra').filter(id=activity_id).first()

            if activity_object is None:
                raise Exception("Activity object not found")

            return activity_object
        except Exception as e:
            raise Exception(f"Activity object retrieval by PK failed with error: {e}")


    
class TargetScoreRepository:
    # def create(self, target_obj: Target, data: TargetScoreType)->TargetScore:
    #     try:
    #         obj = TargetScore.objects.create(target=target_obj, score=data.score)
    #         return obj
    #     except Exception as e:
    #         raise Exception(f"score create repo failed with error: {e}")

    def get_by_target_id(self, target_id: int)->TargetScore:
        try:
            obj = TargetScore.objects.select_related('target', 'target__activity').filter(target__id=target_id).first()

            if obj is None:
                raise Exception("Target score object not found")

            return obj
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

            if target_score_obj.comments != data.comment:
                target_score_obj.comments = data.comment
                is_updated = True
                
            if not target_score_obj.is_scored:
                target_score_obj.is_scored = True
                is_updated = True

            if is_updated:
                target_score_obj.save()
            return target_score_obj
        except Exception as e:
            raise Exception(f"Target score update Repo failed with error: {e}")

    def fetch_by_id(self, target_score_id: int) -> TargetScore:
        try:
            qr = TargetScore.objects.select_related('target', 'target__activity').filter(
                id=target_score_id
            )
            if not qr.exists():
                raise Exception("Target score not found")
            return qr.first()
        except Exception as e:
            raise Exception(f"TargetScore fetch failed with error: {e}")
        
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

    def fetch_by_activity_id(self, activity_id: int) -> List[TargetScore]:
        try:
            qr = TargetScore.objects.select_related('target', 'target__activity').filter(
                target__activity__id=activity_id
            )

            return qr
        except Exception as e:
            raise Exception(f"TargetScore fetch failed with error: {e}")


class KraRolesRepository:
    def create(self, application_object: Application, data: KraRolesCreateType)->Roles:
        obj,_ = Roles.objects.get_or_create(role=data.role, name=data.name, application=application_object.name, defaults={"app_id": application_object, "description": data.description})
        return obj
    
    def role_exists(self, role_name: str)->bool:
        qr = Roles.objects.filter(name__iexact=role_name)
        return qr.exists()