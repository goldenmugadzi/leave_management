from typing import List, Optional
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models.query import QuerySet
from django.core.files.uploadedfile import UploadedFile
from django.core.files.storage import default_storage

from ..models import KeyResultArea, YearQuarter,  Appraisal, ScoreDocument, KeyResultAreaOutCome
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



