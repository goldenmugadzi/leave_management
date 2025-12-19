from ..helpers.data.roles import APPRAISAL_ROLES
from .users import UserProfileRepository
from it.users.models import Roles, Application

class AppraisalRoleRepository:
    def get_appraisal_roles(self):
        try:
            app_obj = Application.objects.filter(name__iexact="Appraisal").first()
            if app_obj is None:
                raise Exception(f"appraisal application not found")
            return Roles.objects.filter(app_id=app_obj)
        except Exception as e:
            raise Exception(f"[AppraisalRoleRepository] get_appraisal_roles repo, failed with error: {e}")
    
    def is_section_head(self, user_id: int):
        try:
            user_repo = UserProfileRepository()
            user_obj = user_repo.get_by_pk(user_id=user_id)
            if user_obj is None:
                raise Exception(f"user not found")
            
            appraisal_roles = self.get_appraisal_roles()
            section_head_role_obj = appraisal_roles.filter(role__iexact=APPRAISAL_ROLES[0]).first()
            
            user_roles = user_obj.roles.all()
            
            for user_role in user_roles.filter(role__iexact=APPRAISAL_ROLES[0]):
                if user_role == section_head_role_obj:
                    return True
            return False
        except Exception as e:
            raise Exception(f"[AppraisalRoleRepository] is_section_head repo with user pk: {user_id}, failed with error: {e}")
    
    def is_kra_creator(self, user_id: int):
        try:
            user_repo = UserProfileRepository()
            user_obj = user_repo.get_by_pk(user_id=user_id)
            if user_obj is None:
                raise Exception(f"user not found")
            
            appraisal_roles = self.get_appraisal_roles()
            kra_creator_role_obj = appraisal_roles.filter(role__iexact=APPRAISAL_ROLES[1]).first()
            
            user_roles = user_obj.roles.all()
            
            for user_role in user_roles.filter(role__iexact=APPRAISAL_ROLES[1]):
                if user_role == kra_creator_role_obj:
                    return True
            return False
        except Exception as e:
            raise Exception(f"[AppraisalRoleRepository] is_kra_creator repo with user pk: {user_id}, failed with error: {e}")