from typing import List
from dataclasses import dataclass
from django.core.files.uploadedfile import UploadedFile
from ..repository import UserQualificationRepository
from ..repository.users import UserProfileRepository
from ..helpers.getters.file_handlers import FileHandlerStrategyContext, UserQualificationStrategy
from it.users.models import UserQualification, UserProfile
import pandas as pd
class UserQualificationServiceError(Exception):
    pass

@dataclass
class UserQualificationService:
    user_qualification_repo: UserQualificationRepository
    
    def create_use_case(self, user_object: UserProfile, name: str, file: UploadedFile)->UserQualification:
        try:
            return self.user_qualification_repo.create(user_object=user_object, name=name, file=file)
        except Exception as e:
            raise UserQualificationServiceError(f"Failed to create user qualification with error: {e}")
    
    def update_use_case(self, qualification_object_id: int, name: str, file: UploadedFile)->UserQualification:
        try:
            return self.user_qualification_repo.update(qualification_object_id=qualification_object_id, name=name, file=file)
        except Exception as e:
            raise UserQualificationServiceError(f"Failed to update user qualification with error: {e}")
    
    
    def get_by_user_object_use_case(self, user_object: UserQualification)->List[UserQualification]:
        try:
           return self.user_qualification_repo.get_by_user(user_object=user_object)
        except Exception as e:
            raise UserQualificationServiceError(f"Failed to retrieve user qualification by user with error: {e}")
    
    def get_by_pk_use_case(self, qualification_id: int)->UserQualification:
        try:
           return self.user_qualification_repo.get_by_id(qualification_id=qualification_id)
        except Exception as e:
            raise UserQualificationServiceError(f"Failed to retrieve user qualification by pk with error: {e}")
    
    def create_in_bulk_use_case(self, file: UploadedFile, user_repo: UserProfileRepository)->bool:
        try:
            context = FileHandlerStrategyContext(strategy=UserQualificationStrategy())
            df = context.data(file=file)
            
            ec_no_col = next(
                (col for col in df.columns if "ec no" in str(col).lower().replace(".", "").strip()),
                None
            )

            if ec_no_col is None:
                raise ValueError(
                    f"Could not find 'EC No.' column in the merged table. Available columns: {list(df.columns)}"
                )

            # Get all qualification sub-columns
            qualification_cols = [
                col for col in df.columns
                if str(col).lower().startswith("qualifications")
            ]

            num = 0
            for _, row in df.iterrows():
                ec_no = row[ec_no_col]
                if pd.isna(ec_no):
                    continue

                if isinstance(ec_no, float):
                    ec_no = int(ec_no)
                print(f"EC No.: {ec_no}")

                for col in qualification_cols:
                    val = row[col]

                    if isinstance(val, str) and val.strip().lower() == "nil":
                        continue

                    if pd.notna(val):
                        print(f"{col}: {val}")

                num += 1
                print("---------------")
            print("============>>>>>>>> Total: ", num)
        except Exception as e:
            raise UserQualificationServiceError(f"[UserQualificationService] create_in_bulk_use_case failed with error: {e}")
    