from typing import List
from dataclasses import dataclass
from django.core.files.uploadedfile import UploadedFile
from ..repository import UserQualificationRepository
from ..repository.users import UserProfileRepository
from ..helpers.getters.file_handlers import FileHandlerStrategyContext, UserQualificationStrategy
from it.users.models import UserQualification, UserProfile
from django.db.models import Q
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
    
    def get_user(self, username: str) -> UserProfile:
        try:
            # Normalize input (remove prefix if present)
            username_normalized = username.strip().lower()
            
            # Query: match with or without "ze" prefix, case-insensitive
            qr = UserProfile.objects.filter(
                Q(username__iexact=username_normalized) | 
                Q(username__iexact=f"ze{username_normalized}")
            )
            return qr.first()
        except Exception as e:
            raise UserQualificationServiceError(
                f"Failed to retrieve user by username '{username}' with error: {e}"
            )

    
    def create_in_bulk_use_case(self, file: UploadedFile) -> bool:
        try:
            context = FileHandlerStrategyContext(strategy=UserQualificationStrategy())
            df = context.data(file=file)   # merged DataFrame

            # Detect EC No. column
            ec_no_col = next(
                (col for col in df.columns if "ec no" in str(col).lower().replace(".", "").strip()),
                None
            )
            if ec_no_col is None:
                raise ValueError(
                    f"Could not find 'EC No.' column in the merged table. Available columns: {list(df.columns)}"
                )

            # Get all qualification sub-columns (under QUALIFICATIONS multi-header)
            qualification_cols = [
                col for col in df.columns
                if any(key in str(col).lower() for key in [
                    "o' levels", "a levels", "certificate", "diploma",
                    "hnd", "prof membership", "degree", "masters", "phd"
                ])
            ]

            objs_to_create = []
            num = 0

            for _, row in df.iterrows():
                ec_no = row[ec_no_col]
                if pd.isna(ec_no):
                    continue

                # Convert EC No. from float to int if needed
                # Normalize EC No.
                ec_no_str = str(int(ec_no)) if isinstance(ec_no, float) else str(ec_no).strip()

                # Find user
                user = self.get_user(username=ec_no_str)
                if not user:
                    print(f"[WARN] No user found with EC No.: {ec_no_str}, skipping qualifications")
                    continue


                # Loop through all qualification sub-columns
                for col in qualification_cols:
                    val = row[col]

                    # Skip nil/empty
                    if isinstance(val, str) and val.strip().lower() == "nil":
                        continue
                    if pd.isna(val):
                        continue

                    # Default classification
                    q_name = "Other"

                    col_clean = str(col).lower()
                    val_clean = str(val).lower()

                    # Map sub-column to qualification type
                    if "o' levels" in col_clean or "o levels" in col_clean:
                        if self.user_qualification_repo.get_by_user(user_object=user).name == "Ordinary Levels":
                            print(f"============>>>>>>>> User with pk: {user.id}, O levels already exists...")
                            continue
                        if "level" in val_clean:
                            q_name = "Ordinary Levels"
                    elif "a' levels" in col_clean:
                        if self.user_qualification_repo.get_by_user(user_object=user).name == "Advanced Levels":
                            print(f"============>>>>>>>> User with pk: {user.id}, Advanced Levels already exists...")
                            continue
                        if "level" in val_clean:
                            q_name = "Advanced Levels"
                    elif "certificate" in col_clean:
                        if self.user_qualification_repo.get_by_user(user_object=user).name == "Certificate" and (self.user_qualification_repo.get_by_user(user_object=user).description.strip().lower() == val.strip().lower()):
                            print(f"============>>>>>>>> User with pk: {user.id}, Certificate - {val} already exists...")
                            continue
                        q_name = "Certificate"
                    elif "diploma" in col_clean:
                        if self.user_qualification_repo.get_by_user(user_object=user).name == "Diploma" and (self.user_qualification_repo.get_by_user(user_object=user).description.strip().lower() == val.strip().lower()):
                            print(f"============>>>>>>>> User with pk: {user.id}, Diploma - {val} already exists...")
                            continue
                        q_name = "Diploma"
                    elif "hnd" in col_clean:
                        if self.user_qualification_repo.get_by_user(user_object=user).name == "Higher National Diploma" and (self.user_qualification_repo.get_by_user(user_object=user).description.strip().lower() == val.strip().lower()):
                            print(f"============>>>>>>>> User with pk: {user.id}, Higher National Diploma - {val} already exists...")
                            continue
                        q_name = "Higher National Diploma"
                    elif "prof membership" in col_clean:
                        if self.user_qualification_repo.get_by_user(user_object=user).name == "Professional Membership" and (self.user_qualification_repo.get_by_user(user_object=user).description.strip().lower() == val.strip().lower()):
                            print(f"============>>>>>>>> User with pk: {user.id}, Professional Membership - {val} already exists...")
                            continue
                        q_name = "Professional Membership"
                    elif "degree" in col_clean:
                        if self.user_qualification_repo.get_by_user(user_object=user).name == "Degree" and (self.user_qualification_repo.get_by_user(user_object=user).description.strip().lower() == val.strip().lower()):
                            print(f"============>>>>>>>> User with pk: {user.id}, Degree - {val} already exists...")
                            continue
                        q_name = "Degree"
                    elif "masters" in col_clean:
                        if self.user_qualification_repo.get_by_user(user_object=user).name == "Masters" and (self.user_qualification_repo.get_by_user(user_object=user).description.strip().lower() == val.strip().lower()):
                            print(f"============>>>>>>>> User with pk: {user.id}, Masters - {val} already exists...")
                            continue
                        q_name = "Masters"
                    elif "phd" in col_clean:
                        if self.user_qualification_repo.get_by_user(user_object=user).name == "PHD" and (self.user_qualification_repo.get_by_user(user_object=user).description.strip().lower() == val.strip().lower()):
                            print(f"============>>>>>>>> User with pk: {user.id}, PHD - {val} already exists...")
                            continue
                        q_name = "PHD"

                    # Create qualification object
                    objs_to_create.append(
                        UserQualification(
                            user=user,
                            name=q_name,
                            description=str(val),
                            file=None
                        )
                    )

                num += 1
                print(f"Processed EC No.: {ec_no}")
                print("---------------------")

            # Bulk insert into DB
            if objs_to_create:
                self.user_qualification_repo.create_in_bulk(objs=objs_to_create)

            print(f"============>>>>>>>> Total Users Processed: {num}")
            print(f"============>>>>>>>> Total Qualifications Created: {len(objs_to_create)}")

            return True

        except Exception as e:
            raise UserQualificationServiceError(
                f"[UserQualificationService] create_in_bulk_use_case failed with error: {e}"
            )