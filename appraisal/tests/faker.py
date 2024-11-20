from it.users.models import UserProfile
from approve.models import Process
from ..models import Appraisal, Experience
from ..helpers.types import AppraisalPayloadType, ExperienceType, QualificationsType
from datetime import datetime

USER_PROFILE_FAKER = UserProfile(
    id=1,
    first_name="John",
    last_name="Wick",
    username="ND22222",
    grade="A and B",
)

APPRAISAL_PAYLOAD_FAKER = AppraisalPayloadType(
    experiences=[
        ExperienceType(name="Golang", years_of_experience=3, months_of_experience=1),
        ExperienceType(name="Python", years_of_experience=3, months_of_experience=1),
    ],
    qualifications=[
        QualificationsType(name="Computer Science Degree", file=None)
    ]
)

PROCESS_FAKER = Process(
    id=1,
    created_at=datetime.now()
)

APPRAISAL_FAKER = Appraisal(
    id=1,
    user=USER_PROFILE_FAKER,
)

EXPERIENCE_FAKER =  Experience(
    id=1,
    name="Python"
)