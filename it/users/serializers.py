from django.contrib.auth.models import User
from rest_framework import serializers
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
            user_profile = UserProfile.objects.get(user=user)
            
            # Access ForeignKey fields properly
            token['district'] = user_profile.district.district if user_profile.district else ""
            token['section'] = user_profile.section.section if user_profile.section else ""
            token['depot'] = user_profile.depot.depot if user_profile.depot else ""
            token['region'] = user_profile.region.region if user_profile.region else ""

        except Exception as ex:
            print("Error in getting the details of user", ex, "for token")

        return token

    # class UserSerializer(serializers.Serializer):
    #     username
    #     Designation
    #     centre
    #     descr
    #     surname
    #     firstname
    #     initials
    #     status
    #     section
    #     email
    #     phone
    #     extension
    #     section_code
    #     createdon
    #     region
    #
    #     def create(self, validated_data):
    #         return User(**validated_data)
