from typing import List
from dataclasses import dataclass
from django.core.files.uploadedfile import UploadedFile
from ..repository import UserQualificationRepository
from ..repository.users import UserProfileRepository
from ..helpers.getters.file_handlers import FileHandlerStrategyContext, UserQualificationStrategy
from it.users.models import UserQualification, UserProfile, QUALIFICATION_TYPE
from django.db.models import Q
import pandas as pd
from datetime import datetime
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
            df = context.data(file=file)

            # Detect EC No. column
            ec_no_col = next(
                (col for col in df.columns if "ec no" in str(col).lower().replace(".", "").strip()),
                None
            )
            if ec_no_col is None:
                raise ValueError(
                    f"Could not find 'EC No.' column in the uploaded file. Available columns: {list(df.columns)}"
                )

            # Detect qualification-related columns
            qualification_cols = [
                col for col in df.columns
                if any(key in str(col).lower() for key in [
                    "o' levels", "a levels", "certificate", "diploma",
                    "hnd", "prof membership", "degree", "masters", "phd"
                ])
            ]

            objs_to_create = []
            objs_to_update = []
            user_objs_to_update = []
            total_processed = 0

            for _, row in df.iterrows():
                ec_no = row[ec_no_col]
                if pd.isna(ec_no):
                    continue

                # Normalize EC number
                ec_no_str = str(int(ec_no)) if isinstance(ec_no, float) else str(ec_no).strip()

                # Fetch user
                user = self.get_user(username=ec_no_str)
                if user is None:
                    print(f"[WARN] No user found with EC No.: {ec_no_str}, skipping row.")
                    continue
                
                # Detect Date Of Engagement: 
                date_of_engagement_col = next(
                    (col for col in df.columns if "date of engagement" in str(col).lower().replace(".", "").strip()),
                    None
                )

                if date_of_engagement_col:
                    raw_date_value = row[date_of_engagement_col]

                    if pd.notna(raw_date_value):
                        parsed_date = None

                        # Try to parse depending on data type
                        if isinstance(raw_date_value, pd.Timestamp):
                            parsed_date = raw_date_value.date()
                        elif isinstance(raw_date_value, datetime):
                            parsed_date = raw_date_value.date()
                        elif isinstance(raw_date_value, str):
                            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"):
                                try:
                                    parsed_date = datetime.strptime(raw_date_value.strip(), fmt).date()
                                    break
                                except ValueError:
                                    continue
                        elif isinstance(raw_date_value, (int, float)):
                            # Excel-style numeric date (e.g. 45400)
                            try:
                                parsed_date = pd.to_datetime(raw_date_value, unit='D', origin='1899-12-30').date()
                            except Exception:
                                pass

                        # Only update if parsed successfully and user has no date yet
                        if parsed_date and user.date_of_engagement is None:
                            user.date_of_engagement = parsed_date
                            user_objs_to_update.append(user)
                    
                # Fetch user’s existing qualifications once
                existing_quals = {
                    (q.name.lower(), (q.description or "").strip().lower()): q
                    for q in self.user_qualification_repo.fetch_by_user(user_id=user.id)
                }

                for col in qualification_cols:
                    val = row[col]
                    if pd.isna(val):
                        continue

                    val_clean = str(val).strip()
                    if not val_clean or val_clean.lower() == "nil":
                        continue

                    col_clean = str(col).lower()

                    # Determine qualification type
                    q_name = "Other"

                    if "o" in col_clean and "level" in col_clean:
                        # Only O Level with a number is valid
                        if any(char.isdigit() for char in val_clean):
                            q_name = "Ordinary Levels"
                    elif "a" in col_clean and "level" in col_clean:
                        # Only A Level with a number is valid
                        if any(char.isdigit() for char in val_clean):
                            q_name = "Advanced Levels"
                    elif "certificate" in col_clean:
                        q_name = "Certificate"
                    elif "diploma" in col_clean and "hnd" not in col_clean:
                        q_name = "Diploma"
                    elif "hnd" in col_clean:
                        q_name = "Higher National Diploma"
                    elif "prof membership" in col_clean:
                        q_name = "Professional Membership"
                    elif "degree" in col_clean:
                        q_name = "Degree"
                    elif "masters" in col_clean:
                        q_name = "Masters"
                    elif "phd" in col_clean:
                        q_name = "PHD"

                    # Split by comma if not O/A Levels
                    values_to_process = [val_clean]
                    if q_name not in ["Ordinary Levels", "Advanced Levels"] and "," in val_clean:
                        values_to_process = [v.strip() for v in val_clean.split(",") if v.strip()]

                    for single_val in values_to_process:
                        key = (q_name.lower(), single_val.lower())

                        # Update existing qualification if exists
                        if key in existing_quals:
                            qual = existing_quals[key]
                            if qual.description.strip() != single_val:
                                qual.description = single_val
                                objs_to_update.append(qual)
                                print(f"[UPDATE] {user.username} - {q_name}: {single_val}")
                            else:
                                print(f"[SKIP] {user.username} already has {q_name} - {single_val}")
                            continue

                        # Otherwise → create new qualification
                        new_qual = UserQualification(
                            user=user,
                            name=q_name,
                            description=single_val,
                            file=None
                        )
                        objs_to_create.append(new_qual)
                        print(f"[CREATE] {user.username} - {q_name}: {single_val}")

                total_processed += 1

            # Perform DB operations
            if objs_to_create:
                self.user_qualification_repo.create_in_bulk(objs=objs_to_create)

            if objs_to_update:
                self.user_qualification_repo.bulk_update(objs_to_update, fields=["description"])
                
            if user_objs_to_update:
                user_repo = UserProfileRepository()
                user_repo.bulk_update(objs=user_objs_to_update, fields=["date_of_engagement"])

            print(f"✅ Total Users Processed: {total_processed}")
            print(f"✅ [User Qualification] Created: {len(objs_to_create)} | Updated: {len(objs_to_update)}")
            print(f"✅ [User Profile] Updated: {len(user_objs_to_update)}")

            return True

        except Exception as e:
            raise UserQualificationServiceError(
                f"[UserQualificationService] create_in_bulk_use_case failed: {e}"
            )
