from typing import Dict, Any, List
from ..models import Appraisal, PersonalAttribute, AppraiseePersonalAttribute, AppraisalOverallComments
from ..models.helpers import YearQuarter
from it.users.models import UserProfile


class AppraisalRepository:
    def create(self, appraisee_object: UserProfile, appraiser_object: UserProfile) -> Appraisal:
        try:
            return Appraisal.objects.create(user=appraisee_object, appraiser=appraiser_object, reviewer=None)
        except Exception as e:
            raise Exception(f"Appraisal Create Repo failed with error: {e}")

    def fetch_by_user_id(self, user_id: UserProfile) -> List[Appraisal]:
        try:
            return Appraisal.objects.filter(user__id=user_id)
        except Exception as e:
            raise Exception(f"Appraisal fetch_by_user_id Repo with appraisee or user pk: {user_id}, failed with error: {e}")

    def fetch_by_appraiser_id(self, appraiser_id: int) -> List[Appraisal]:
        try:
            return Appraisal.objects.filter(appraiser__id=appraiser_id)
        except Exception as e:
            raise Exception(f"Appraisal fetch_by_appraiser_id Repo with appraiser pk: {appraiser_id}, failed with error: {e}")

    def fetch_by_reviewer_id(self, reviewer_id: int) -> List[Appraisal]:
        try:
            return Appraisal.objects.filter(reviewer__id=reviewer_id)
        except Exception as e:
            raise Exception(f"Appraisal fetch_by_reviewer_id Repo with reviewer pk: {reviewer__id}, failed with error: {e}")

    def fetch_by_hr_id(self, hr_id: int) -> List[Appraisal]:
        try:
            return Appraisal.objects.filter(hr__id=hr_id)
        except Exception as e:
            raise Exception(f"Appraisal fetch_by_hr_id Repo with hr pk: {hr_id}, failed with error: {e}")

    def get_appraisal_by_pk(self, appraisal_id: int)->Appraisal:
        try:
            qr = Appraisal.objects.filter(id=appraisal_id).select_related("user", "appraiser", "reviewer")
            
            if not qr.exists():
                return None
            return qr.first()
        except Exception as e:
            raise Exception(f"Appraisal get_appraisal_by_pk Repo with appraisal pk: {appraisal_id}, failed with error: {e}")

    
    def get_all_appraisal_objects(self)->list:
        return Appraisal.objects.all()
    
    def update(self, appraisal_object: Appraisal, appraiser_object: UserProfile, reviewer_obj: UserProfile, hr_object: UserProfile, is_accepted_by_appraiser_reviewer: bool=False)->Appraisal:
        try:
            is_changed = False
            
            if appraisal_object.appraiser != appraiser_object:
                appraisal_object.appraiser = appraiser_object
                is_changed = True
            
            if appraisal_object.reviewer != reviewer_obj:
                appraisal_object.reviewer = reviewer_obj
                is_changed = True
                
            if appraisal_object.hr != hr_object:
                appraisal_object.hr = hr_object
                is_changed = True
                
            if appraisal_object.is_accepted != is_accepted_by_appraiser_reviewer:
                appraisal_object.is_accepted = is_accepted_by_appraiser_reviewer
                is_changed = True
                
            if is_changed:
                appraisal_object.save()
                
            return appraisal_object
        except Exception as e:
            raise Exception(f"Appraisal update Repo with appraisal pk: {appraisal_object.id}, failed with error: {e}")


class PersonalAttributeRepository:
    def create(self, name: str)->PersonalAttribute:
        try:
            return PersonalAttribute.objects.create(name=name)
        except Exception as e:
            raise Exception(f"PersonalAttributeRepository create Repo failed with error: {e}")

    def bulk_create(self, personal_attr_list: List[PersonalAttribute])->bool:
        try:
            PersonalAttribute.objects.bulk_create(objs=personal_attr_list, ignore_conflicts=True)
            return True
        except Exception as e:
            raise Exception(f"PersonalAttributeRepository bulk_create Repo failed with error: {e}")


    def fetch_all(self):
        try:
            return PersonalAttribute.objects.all()
        except Exception as e:
            raise Exception(f"PersonalAttributeRepository fetch all Repo failed with error: {e}")

class AppraiseePersonalAttributeRepository:
    def create(self, appraisal_obj: Appraisal, quarter_obj: YearQuarter, personal_attr_object: PersonalAttribute)->AppraiseePersonalAttribute:
        try:
            return AppraiseePersonalAttribute.objects.create(appraisal=appraisal_obj, quarter=quarter_obj, personal_attribute=personal_attr_object)
        except Exception as e:
            raise Exception(f"AppraiseePersonalAttributeRepository create Repo failed with error: {e}")

    def bulk_update(self, updated_objects_list: List[AppraiseePersonalAttribute])->bool:
        try:
            AppraiseePersonalAttribute.objects.bulk_update(
                updated_objects_list,
                fields=["excellent", "very_good", "satisfactory", "requires_improvement", "unsatisfactory"]
            )            
            return True
        except Exception as e:
            raise Exception(f"AppraiseePersonalAttributeRepository bulk_update Repo failed with error: {e}")

    def bulk_create(self, appraisee_personal_attr_list: List[AppraiseePersonalAttribute])->bool:
        try:
            AppraiseePersonalAttribute.objects.bulk_create(objs=appraisee_personal_attr_list, ignore_conflicts=True)
            return True
        except Exception as e:
            raise Exception(f"AppraiseePersonalAttributeRepository bulk_create Repo failed with error: {e}")

    
    def fetch_appraisal_id(self, appraisal_id)->List[AppraiseePersonalAttribute]:
        try:
            return AppraiseePersonalAttribute.objects.filter(appraisal__id=appraisal_id).select_related("quarter", "personal_attribute", "appraisal")
        except Exception as e:
            raise Exception(f"AppraiseePersonalAttributeRepository fetch by appraisal pk: {appraisal_id} Repo failed with error: {e}")
    
    def fetch_appraisal_id_quarter_id(self, appraisal_id: int, quarter_id: int)->List[AppraiseePersonalAttribute]:
        try:
            return AppraiseePersonalAttribute.objects.filter(appraisal__id=appraisal_id, quarter__id=quarter_id).select_related("personal_attribute")
        except Exception as e:
            raise Exception(f"AppraiseePersonalAttributeRepository fetch by appraisal and quarter pk: appraisa - {appraisal_id} and quarter id - {quarter_id} Repo failed with error: {e}")
    
    def fetch_appraisal_id_quarter_num(self, appraisal_id: int, quarter_num: int)->List[AppraiseePersonalAttribute]:
        try:
            return AppraiseePersonalAttribute.objects.filter(appraisal__id=appraisal_id, quarter__quarter=quarter_num).select_related("personal_attribute")
        except Exception as e:
            raise Exception(f"AppraiseePersonalAttributeRepository fetch_appraisal_id_quarter_num pk: appraisal - {appraisal_id} and quarter num - {quarter_num} Repo failed with error: {e}")

class AppraisalOverallCommentsRepository:
    def bulk_create(self, appraisal_overall_comm_list: List[AppraisalOverallComments])->bool:
        try:
            AppraisalOverallComments.objects.bulk_create(objs=appraisal_overall_comm_list)
            return True
        except Exception as e:
            raise Exception(f"[AppraisalOverallCommentsRepository] bulk_create Repo failed with error: {e}")

    def update(self, appraisal_overall_comm_obj: AppraisalOverallComments, comment: str)->AppraisalOverallComments:
        try:
            is_changed = False
            
            if appraisal_overall_comm_obj.appraiser_comment != comment:
                appraisal_overall_comm_obj.appraiser_comment = comment
                is_changed = True
            if is_changed:
                appraisal_overall_comm_obj.save()
            return appraisal_overall_comm_obj
        except Exception as e:
            raise Exception(f"[AppraisalOverallCommentsRepository] update Repo for appraisal_overall_comm_id: {appraisal_overall_comm_obj.id} failed with error: {e}")

    def get_by_appraisal_id_quarter_id(self, appraisal_id: int, quarter_number: int)->AppraisalOverallComments:
        try:
            qr = AppraisalOverallComments.objects.filter(appraisal__id=appraisal_id, quarter__quarter=quarter_number)
            return qr.first()
        except Exception as e:
            raise Exception(f"[AppraisalOverallCommentsRepository] get_by_appraisal_id_quarter_id Repo for appraisal_id: {appraisal_id}, quarter num: {quarter_number}, failed with error: {e}")

    def get_by_appraisal_id_quarter_num(self, appraisal_id: int, quarter_number: int)->AppraisalOverallComments:
        try:
            qr = AppraisalOverallComments.objects.filter(appraisal__id=appraisal_id, quarter__quarter=quarter_number)
            return qr.first()
        except Exception as e:
            raise Exception(f"[AppraisalOverallCommentsRepository] get_by_appraisal_id_quarter_id Repo for appraisal_id: {appraisal_id}, quarter num: {quarter_number}, failed with error: {e}")

    def fetch_by_appraisal_id(self, appraisal_id: int)->List[AppraisalOverallComments]:
        try:
            qr = AppraisalOverallComments.objects.filter(appraisal__id=appraisal_id).select_related("quarter")
            return qr
        except Exception as e:
            raise Exception(f"[AppraisalOverallCommentsRepository] fetch_by_appraisal_id Repo for appraisal_id: {appraisal_id}, failed with error: {e}")
