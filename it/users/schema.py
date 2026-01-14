from django.db.models import Q
import graphene
from .types import (
    UserProfileType, RegionsType, DistrictsType, SectionsType, DepotsType,
    ApplicationType, RolesType, DesignationsType, CostCenterType,
    NotificationType, SupplierType, ResponsibilitiesType
)
from .models import (
    UserProfile, Regions, Districts, Sections, Depots, Application, Roles,
    Designations, CostCenter, Notification, Supplier, Responsibilities
)

# Import JWT token generation for hybrid authentication
try:
    from graphql_jwt.shortcuts import get_token
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    import logging
    logging.warning("graphql_jwt not available - token_from_session query will not work")


class TokenFromSessionType(graphene.ObjectType):
    """Type for JWT token generated from Django session"""
    token = graphene.String()
    refresh_token = graphene.String()
    user = graphene.Field(UserProfileType)


class Query(graphene.ObjectType):
    me = graphene.Field(UserProfileType)
    users = graphene.List(UserProfileType, username_icontains=graphene.String())
    all_users = graphene.List(UserProfileType, search=graphene.String())
    user = graphene.Field(UserProfileType, id=graphene.ID(required=True))
    application = graphene.Field(ApplicationType, id=graphene.ID(required=True))
    role = graphene.Field(RolesType, id=graphene.ID(required=True))
    designation = graphene.Field(DesignationsType, id=graphene.ID(required=True))
    cost_center = graphene.Field(CostCenterType, id=graphene.ID(required=True))
    notification = graphene.Field(NotificationType, id=graphene.ID(required=True))
    supplier = graphene.Field(SupplierType, id=graphene.ID(required=True))
    responsibility = graphene.Field(ResponsibilitiesType, id=graphene.ID(required=True))
    my_cost_centers = graphene.List(CostCenterType)
    all_regions = graphene.List(RegionsType)
    all_districts = graphene.List(DistrictsType)
    all_sections = graphene.List(SectionsType)
    all_depots = graphene.List(DepotsType)
    all_applications = graphene.List(ApplicationType)
    all_roles = graphene.List(RolesType)
    all_designations = graphene.List(DesignationsType)
    all_cost_centers = graphene.List(CostCenterType)
    all_notifications = graphene.List(NotificationType)
    all_suppliers = graphene.List(SupplierType)
    all_responsibilities = graphene.List(ResponsibilitiesType)
    token_from_session = graphene.Field(TokenFromSessionType)

    def resolve_users(self, info, username_icontains=None):
        queryset = UserProfile.objects.all()
        if username_icontains:
            queryset = queryset.filter(username__icontains=username_icontains)
        return queryset

    def resolve_all_users(self, info, search=None):
        """Alias for resolve_users with 'search' parameter for frontend compatibility"""
        from django.db.models import Value
        from django.db.models.functions import Concat

        queryset = UserProfile.objects.all()
        if not search:
            return queryset

        s = str(search).strip()
        if not s:
            return queryset

        # annotate a full_name field so we can match 'John Doe' as a phrase
        queryset = queryset.annotate(full_name=Concat('first_name', Value(' '), 'last_name'))

        terms = s.split()
        q = Q()
        for t in terms:
            q |= (
                Q(username__icontains=t) |
                Q(email__icontains=t) |
                Q(first_name__icontains=t) |
                Q(last_name__icontains=t) |
                Q(full_name__icontains=t)
            )

        # also allow the whole search phrase to match the full name
        q |= Q(full_name__icontains=s)

        return queryset.filter(q).distinct()

    def resolve_user(self, info, id):
        return UserProfile.objects.get(pk=id)

    def resolve_me(self, info):
        user = info.context.user
        return UserProfile.objects.get(pk=user.id) if user.is_authenticated else None
   
    def resolve_region(self, info, id):
        return Regions.objects.get(pk=id)

    def resolve_district(self, info, id):
        return Districts.objects.get(pk=id)

    def resolve_section(self, info, id):
        return Sections.objects.get(pk=id)

    def resolve_depot(self, info, id):
        return Depots.objects.get(pk=id)

    def resolve_application(self, info, id):
        return Application.objects.get(pk=id)

    def resolve_role(self, info, id):
        return Roles.objects.get(pk=id)

    def resolve_designation(self, info, id):
        return Designations.objects.get(pk=id) 

    def resolve_cost_center(self, info, id):
        return CostCenter.objects.get(pk=id)
    
    def resolve_my_cost_centers(self, info):
        user = info.context.user
        if user.is_authenticated:
            application_names = ["temper", "reimbursement", "clear credit"]
            return user.cost_centers_for(application_names)
        return CostCenter.objects.none()

    def resolve_notification(self, info, id):
        return Notification.objects.get(pk=id)

    def resolve_supplier(self, info, id):
        return Supplier.objects.get(pk=id)

    def resolve_responsibility(self, info, id):
        return Responsibilities.objects.get(pk=id)

    def resolve_all_regions(self, info):
        return Regions.objects.all()

    def resolve_all_districts(self, info):
        return Districts.objects.all()

    def resolve_all_sections(self, info):
        return Sections.objects.all()

    def resolve_all_depots(self, info):
        return Depots.objects.all()

    def resolve_all_applications(self, info):
        return Application.objects.all()

    def resolve_all_roles(self, info):
        return Roles.objects.all()

    def resolve_all_designations(self, info):
        return Designations.objects.all()

    def resolve_all_cost_centers(self, info):
        return CostCenter.objects.all()

    def resolve_all_notifications(self, info):
        return Notification.objects.all()

    def resolve_all_suppliers(self, info):
        return Supplier.objects.all()

    def resolve_all_responsibilities(self, info):
        return Responsibilities.objects.all()
    
    def resolve_token_from_session(self, info):
        """
        Check if user has active Django session and return JWT token
        This enables hybrid authentication between Django admin and React frontend
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Enhanced debugging
        logger.info("=" * 60)
        logger.info("TOKEN_FROM_SESSION QUERY CALLED")
        logger.info("=" * 60)
        
        # Get user from context
        user = info.context.user
        
        # Detailed session debugging
        request = info.context
        logger.info(f"Request type: {type(request)}")
        logger.info(f"User object: {user}")
        logger.info(f"User type: {type(user)}")
        logger.info(f"User authenticated: {user.is_authenticated if hasattr(user, 'is_authenticated') else 'N/A'}")
        logger.info(f"User ID: {getattr(user, 'id', 'N/A')}")
        logger.info(f"Username: {getattr(user, 'username', 'N/A')}")
        
        # Check session
        if hasattr(request, 'session'):
            logger.info(f"Session exists: {bool(request.session)}")
            logger.info(f"Session key: {request.session.session_key}")
            logger.info(f"Session data: {dict(request.session)}")
        else:
            logger.warning("No session attribute on request")
        
        # Check cookies
        if hasattr(request, 'COOKIES'):
            logger.info(f"Cookies: {list(request.COOKIES.keys())}")
            if 'sessionid' in request.COOKIES:
                logger.info(f"Session cookie found: {request.COOKIES['sessionid'][:10]}...")
            else:
                logger.warning("No sessionid cookie found")
        
        # Check if JWT is available
        if not JWT_AVAILABLE:
            logger.error("JWT not available - install django-graphql-jwt or djangorestframework-simplejwt")
            return None
        
        # Check if user is authenticated via Django session
        if user and user.is_authenticated:
            try:
                logger.info(f"✓ User authenticated! Generating JWT token for: {user.username}")
                
                # Generate JWT token for the authenticated user
                token = get_token(user)
                logger.info(f"✓ JWT token generated successfully (length: {len(token)})")
                
                # Try to get refresh token if available
                refresh_token = None
                try:
                    from graphql_jwt.shortcuts import create_refresh_token
                    refresh_token = create_refresh_token(user)
                    logger.info("✓ Refresh token generated")
                except (ImportError, LookupError) as e:
                    # LookupError: refresh_token app not configured
                    # ImportError: graphql_jwt not available
                    logger.debug(f"Refresh token not available: {e}")
                    refresh_token = None
                
                logger.info("=" * 60)
                return TokenFromSessionType(
                    token=token,
                    refresh_token=refresh_token,
                    user=user
                )
            except Exception as e:
                logger.error(f"✗ Error generating JWT token from session: {e}")
                import traceback
                traceback.print_exc()
                logger.info("=" * 60)
                return None
        else:
            # No valid session - user not logged in
            logger.warning("✗ User not authenticated in session")
            logger.warning(f"User object type: {type(user)}")
            logger.warning(f"User is_authenticated: {getattr(user, 'is_authenticated', 'attribute missing')}")
            logger.info("=" * 60)
            return None


class HybridLoginType(graphene.ObjectType):
    """Response type for hybrid login"""
    success = graphene.Boolean()
    message = graphene.String()
    token = graphene.String()
    refresh_token = graphene.String()
    user = graphene.Field(UserProfileType)


class HybridLogoutType(graphene.ObjectType):
    """Response type for hybrid logout"""
    success = graphene.Boolean()
    message = graphene.String()


class HybridLogin(graphene.Mutation):
    """
    Hybrid login mutation that creates both Django session and JWT token
    Login from React → Get JWT token + Django session created
    """
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
    
    Output = HybridLoginType
    
    @staticmethod
    def mutate(root, info, username, password):
        import logging
        from django.contrib.auth import authenticate, login
        
        logger = logging.getLogger(__name__)
        logger.info("=" * 60)
        logger.info("HYBRID LOGIN ATTEMPT")
        logger.info(f"Username: {username}")
        logger.info("=" * 60)
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        
        if user is None:
            logger.warning(f"✗ Authentication failed for user: {username}")
            logger.info("=" * 60)
            return HybridLoginType(
                success=False,
                message="Invalid username or password",
                token=None,
                refresh_token=None,
                user=None
            )
        
        if not user.is_active:
            logger.warning(f"✗ User account is disabled: {username}")
            logger.info("=" * 60)
            return HybridLoginType(
                success=False,
                message="User account is disabled",
                token=None,
                refresh_token=None,
                user=None
            )
        
        try:
            # 1. Create Django session
            login(info.context, user)
            logger.info(f"✓ Django session created for: {username}")
            logger.info(f"Session key: {info.context.session.session_key}")
            
            # 2. Generate JWT token
            if JWT_AVAILABLE:
                token = get_token(user)
                logger.info(f"✓ JWT token generated (length: {len(token)})")
                
                # Try to get refresh token
                refresh_token = None
                try:
                    from graphql_jwt.shortcuts import create_refresh_token
                    refresh_token = create_refresh_token(user)
                    logger.info("✓ Refresh token generated")
                except (ImportError, LookupError) as e:
                    logger.debug(f"Refresh token not available: {e}")
            else:
                token = None
                refresh_token = None
                logger.warning("JWT not available")
            
            logger.info(f"✓ Hybrid login successful for: {username}")
            logger.info("=" * 60)
            
            return HybridLoginType(
                success=True,
                message="Login successful",
                token=token,
                refresh_token=refresh_token,
                user=user
            )
            
        except Exception as e:
            logger.error(f"✗ Error during hybrid login: {e}")
            import traceback
            traceback.print_exc()
            logger.info("=" * 60)
            return HybridLoginType(
                success=False,
                message=f"Login error: {str(e)}",
                token=None,
                refresh_token=None,
                user=None
            )


class HybridLogout(graphene.Mutation):
    """
    Hybrid logout mutation that destroys both Django session and invalidates JWT
    Logout from React → Django session destroyed + JWT invalidated
    """
    Output = HybridLogoutType
    
    @staticmethod
    def mutate(root, info):
        import logging
        from django.contrib.auth import logout
        
        logger = logging.getLogger(__name__)
        logger.info("=" * 60)
        logger.info("HYBRID LOGOUT")
        
        user = info.context.user
        
        if user and user.is_authenticated:
            # Capture user id before calling logout (request.user will be anonymous afterwards)
            user_id = str(user.id)
            username = user.username
            logger.info(f"User: {username}")

            try:
                # 1. Destroy Django session associated with the current request
                logout(info.context)
                logger.info(f"✓ Django session destroyed for: {username}")

                # 2. Destroy ALL other Django sessions for this user (logout across devices)
                try:
                    from django.contrib.sessions.models import Session
                    from django.utils import timezone

                    user_sessions = Session.objects.filter(expire_date__gte=timezone.now())
                    deleted = 0
                    for session in user_sessions:
                        try:
                            data = session.get_decoded()
                            if data.get('_auth_user_id') == user_id:
                                session.delete()
                                deleted += 1
                        except Exception:
                            continue

                    logger.info(f"✓ Deleted {deleted} session(s) for user {username}")
                except Exception as e:
                    logger.warning(f"Could not delete other sessions for user {username}: {e}")

                # 3. Note: JWT tokens are stateless, so we can't "destroy" them server-side
                # The frontend must remove the token from localStorage
                # Optional: Implement token blacklist for true server-side revocation

                logger.info(f"✓ Hybrid logout successful for: {username}")
                logger.info("=" * 60)

                return HybridLogoutType(
                    success=True,
                    message="Logout successful. Please remove JWT token from client."
                )

            except Exception as e:
                logger.error(f"✗ Error during hybrid logout: {e}")
                import traceback
                traceback.print_exc()
                logger.info("=" * 60)
                return HybridLogoutType(
                    success=False,
                    message=f"Logout error: {str(e)}"
                )
        else:
            logger.warning("✗ No authenticated user to logout")
            logger.info("=" * 60)
            return HybridLogoutType(
                success=False,
                message="No authenticated user"
            )


class Mutation(graphene.ObjectType):
    """User Mutations"""
    hybrid_login = HybridLogin.Field()
    hybrid_logout = HybridLogout.Field()

