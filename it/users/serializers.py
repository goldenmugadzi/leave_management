from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework import status
from .models import *
import logging
import traceback

logger = logging.getLogger(__name__)


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        logger.info(f"🔐 [AUTH] Getting token for user: {user.username} (ID: {user.id})")
        
        try:
            token = super().get_token(user)
            logger.info(f"✅ [AUTH] Base token created successfully for {user.username}")
        except Exception as e:
            logger.error(f"❌ [AUTH] Failed to create base token for {user.username}: {str(e)}")
            raise

        # Add custom claims
        try:
            token['username'] = user.username
            token['firstname'] = user.first_name
            token['lastname'] = user.last_name
            logger.debug(f"✅ [AUTH] Added basic user info to token for {user.username}")
        except Exception as e:
            logger.error(f"❌ [AUTH] Failed to add basic user info: {str(e)}")
            raise

        # Get user's groups
        try:
            groups = user.groups.all()
            group_names = [group.name for group in groups]
            token['groups'] = group_names
            logger.info(f"✅ [AUTH] User {user.username} groups: {group_names}")
        except Exception as e:
            logger.error(f"❌ [AUTH] Failed to get user groups: {str(e)}")
            token['groups'] = []

        # Add other profile data
        try:
            logger.debug(f"🔍 [AUTH] Fetching UserProfile for user id={user.id}")
            # user is already a UserProfile instance (UserProfile extends AbstractUser)
            user_profile = user
            logger.info(f"✅ [AUTH] Found UserProfile for {user.username}")
            
            # Get district (ForeignKey field - access directly)
            try:
                token['district'] = user_profile.district.district if user_profile.district else ""
                logger.debug(f"✅ [AUTH] District: {token['district']}")
            except Exception as e:
                logger.error(f"❌ [AUTH] Error fetching district: {str(e)}")
                token['district'] = ""
            
            # Get section (ForeignKey field - access directly)
            try:
                token['section'] = user_profile.section.section if user_profile.section else ""
                logger.debug(f"✅ [AUTH] Section: {token['section']}")
            except Exception as e:
                logger.error(f"❌ [AUTH] Error fetching section: {str(e)}")
                token['section'] = ""
            
            # Get depot (ForeignKey field - access directly)
            try:
                token['depot'] = user_profile.depot.depot if user_profile.depot else ""
                logger.debug(f"✅ [AUTH] Depot: {token['depot']}")
            except Exception as e:
                logger.error(f"❌ [AUTH] Error fetching depot: {str(e)}")
                token['depot'] = ""
            
            # Get region (ForeignKey field - access directly)
            try:
                token['region'] = user_profile.region.region if user_profile.region else ""
                logger.debug(f"✅ [AUTH] Region: {token['region']}")
            except Exception as e:
                logger.error(f"❌ [AUTH] Error fetching region: {str(e)}")
                token['region'] = ""
                
            logger.info(f"✅ [AUTH] Successfully added all profile data to token for {user.username}")

        except UserProfile.DoesNotExist:
            logger.warning(f"⚠️  [AUTH] No UserProfile found for user {user.username} (ID: {user.id})")
            token['district'] = ""
            token['section'] = ""
            token['depot'] = ""
            token['region'] = ""
        except Exception as ex:
            logger.error(f"❌ [AUTH] Unexpected error getting user profile details: {str(ex)}", exc_info=True)
            token['district'] = ""
            token['section'] = ""
            token['depot'] = ""
            token['region'] = ""

        logger.info(f"🎉 [AUTH] Token generation completed successfully for {user.username}")
        return token


class MyTokenObtainPairView(TokenObtainPairView):
    """
    Custom Token Obtain Pair View with detailed logging for debugging authentication issues
    """
    serializer_class = MyTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        logger.info("=" * 80)
        logger.info(f"🔐 [AUTH REQUEST] New authentication attempt from IP: {self.get_client_ip(request)}")
        logger.info(f"📋 [AUTH REQUEST] Request headers: {dict(request.headers)}")
        logger.info(f"📋 [AUTH REQUEST] Content-Type: {request.content_type}")
        
        # Log the username being attempted (without logging password)
        username = request.data.get('username', 'NOT_PROVIDED')
        password = request.data.get('password', 'NOT_PROVIDED')
        
        logger.info(f"👤 [AUTH REQUEST] Username: '{username}'")
        logger.info(f"👤 [AUTH REQUEST] Username length: {len(username) if username != 'NOT_PROVIDED' else 0}")
        logger.info(f"👤 [AUTH REQUEST] Username type: {type(username)}")
        logger.info(f"👤 [AUTH REQUEST] Username repr: {repr(username)}")
        logger.info(f"🔑 [AUTH REQUEST] Password provided: {'YES' if password != 'NOT_PROVIDED' else 'NO'}")
        logger.info(f"🔑 [AUTH REQUEST] Password length: {len(password) if password != 'NOT_PROVIDED' else 0}")
        logger.info(f"📦 [AUTH REQUEST] All request.data keys: {list(request.data.keys())}")
        logger.info(f"📦 [AUTH REQUEST] Request body (sanitized): {self.sanitize_body(request.data)}")
        
        # Check if user exists in database
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user_exists = User.objects.filter(username=username).exists()
            logger.info(f"🔍 [AUTH CHECK] User '{username}' exists in database: {user_exists}")
            
            if user_exists:
                user = User.objects.get(username=username)
                logger.info(f"✅ [AUTH CHECK] User found - ID: {user.id}, Active: {user.is_active}, Email: {user.email}")
                logger.info(f"📊 [AUTH CHECK] User groups: {[g.name for g in user.groups.all()]}")
                
                # Try to authenticate with the provided credentials
                from django.contrib.auth import authenticate
                auth_result = authenticate(username=username, password=password)
                if auth_result:
                    logger.info(f"✅ [AUTH CHECK] Django authenticate() succeeded for {username}")
                else:
                    logger.error(f"❌ [AUTH CHECK] Django authenticate() FAILED for {username} - Password is incorrect!")
            else:
                logger.error(f"❌ [AUTH CHECK] User '{username}' does NOT exist in database")
                
                # Show similar usernames to help debug
                similar_users = User.objects.filter(username__icontains=username[:5])[:5]
                if similar_users:
                    logger.info(f"🔍 [AUTH CHECK] Similar usernames found: {[u.username for u in similar_users]}")
                    
        except Exception as check_error:
            logger.error(f"⚠️  [AUTH CHECK] Error checking user existence: {str(check_error)}")
        
        try:
            # Call the parent class method
            logger.info(f"⏳ [AUTH] Starting authentication process for {username}...")
            response = super().post(request, *args, **kwargs)
            
            # Log successful authentication
            if response.status_code == 200:
                logger.info(f"✅ [AUTH SUCCESS] User {username} authenticated successfully")
                logger.info(f"🎫 [AUTH SUCCESS] Response status: {response.status_code}")
                logger.debug(f"📦 [AUTH SUCCESS] Response data keys: {list(response.data.keys()) if hasattr(response, 'data') else 'N/A'}")
            else:
                logger.warning(f"⚠️  [AUTH FAILED] Authentication failed for {username} with status {response.status_code}")
                logger.warning(f"📦 [AUTH FAILED] Response data: {response.data if hasattr(response, 'data') else 'N/A'}")
            
            logger.info("=" * 80)
            return response
            
        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"❌ [AUTH ERROR] Exception during authentication for {username}")
            logger.error(f"❌ [AUTH ERROR] Error type: {type(e).__name__}")
            logger.error(f"❌ [AUTH ERROR] Error message: {str(e)}")
            logger.error(f"❌ [AUTH ERROR] Full traceback:")
            logger.error(traceback.format_exc())
            logger.error("=" * 80)
            
            # Re-raise to let Django handle it
            raise
    
    def get_client_ip(self, request):
        """Get the client's IP address from the request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def sanitize_body(self, data):
        """Return request body with password masked"""
        sanitized = dict(data)
        if 'password' in sanitized:
            sanitized['password'] = '***REDACTED***'
        return sanitized


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
