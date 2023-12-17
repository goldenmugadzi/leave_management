from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import *

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username
        token['firstname'] = user.first_name
        token['lastname'] = user.last_name
        
        # Get user's groups
        groups = user.groups.all()
        group_names = [group.name for group in groups]
        token['groups'] = group_names        
        
        # Add other profile data
        try:
            
            user_profile = UserProfile.objects.get(user_id=user.id)
            district = Districts.objects.get(code=user_profile.district) if user_profile.district else ""
            section = Sections.objects.get(code=user_profile.section) if user_profile.section else ""
            depot  = Depots.objects.get(code=user_profile.depot) if user_profile.depot else ""
            region = Regions.objects.get(id=user_profile.region) if user_profile.region else ""

            token['district'] = district.district if district else ""
            token['section'] = section.section if section else ""
            token['depot'] = depot.depot if depot else ""
            token['region'] = region.region if region else ""
            
        except Exception as ex:
            print("Error in getting the details of user",ex,"for token")

        return token