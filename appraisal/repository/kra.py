from typing import List
from ..models import KeyResultArea, YearQuarter, Activity, Target
from ..helpers.types.kra import KRAType, TargetType
from it.users.models import UserProfile

class KRARepository:
    def create(self, quarter_obj: YearQuarter, creator_obj, data: KRAType)->KeyResultArea:
        """
            Creates a new KeyResultArea (KRA) record in the database.

            Args:
                quarter_obj (YearQuarter): The quarter associated with the KRA.
                creator_obj: The user or entity responsible for creating the KRA.
                data (KRAType): The data object containing the name, description, and weight of the KRA.

            Returns:
                KeyResultArea: The newly created KRA object.

            Raises:
                Exception: If the creation operation fails.
        """

        try:
            return KeyResultArea.objects.create(quarter=quarter_obj, created_by=creator_obj, name=data.name, description=data.description, weight=data.weight)
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


class KraActivityRepository:
    def create(self, kra_obj: KeyResultArea, assigned_user: UserProfile, data: KRAType)->Activity:
        try:
            return Activity.objects.create(kra=kra_obj, assigned_user=assigned_user, name=data.name, description=data.description, weight=data.weight)
        except Exception as e:
            raise Exception(f"KRA Activity Create Repo failed with error: {e}")

    def fetch_by_kra_id(self, kra_id: int)->List[Activity]:
        try:
            queryset = Activity.objects.filter(kra__id=kra_id)
            return queryset
        except Exception as e:
            raise Exception(f"KRA Activity Fetch Repo failed with error: {e}")

    def update(self, activity_obj: Activity, assigned_user: UserProfile, data: KRAType)->Activity:
        try:
            updated = False
            if assigned_user != activity_obj.assigned_user:
                activity_obj.assigned_user = assigned_user
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


class ActivityTargetRepository:
    
    def fetch_by_activity_id(self, activity_id: int)->List[Target]:
        try:
            queryset = Target.objects.filter(activity__id=activity_id).select_related("activity")
            return queryset
        except Exception as e:
                raise Exception(f"Targets retrieval by PK failed with error: {e}")
            
    def create(self, activity_obj: Activity, data: TargetType)->Target:
        try:
            obj = Target.objects.create(activity=activity_obj,
                                        metric_type=data.metric_type,
                                        name=data.name,
                                        weight=data.weight,
                                        allowance_variance=data.allowance_variance,
                                        target_value=data.target_value,
                                        unit=data.unit
                                        )
            return obj
        except Exception as e:
                raise Exception(f"Targets retrieval by PK failed with error: {e}")
    
    def get_target_by_id(self, target_id: int)->Target:
        try:
            target_object = Target.objects.select_related('activity').filter(id=target_id).first()

            if target_object is None:
                raise Exception("Target object not found")

            return target_object
        except Exception as e:
            raise Exception(f"Target object retrieval by PK failed with error: {e}")
