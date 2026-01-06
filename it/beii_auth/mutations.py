import graphene
import graphql_jwt
from graphql_jwt.decorators import login_required


class TokenAuth(graphene.Mutation):
    """Custom JWT authentication mutation that wraps graphql_jwt.ObtainJSONWebToken"""
    
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
    
    success = graphene.Boolean()
    token = graphene.String()
    refreshToken = graphene.String()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, username, password):
        print(f"=== TokenAuth Mutation Called ===")
        print(f"Username: {username}")
        print(f"Password: {'*' * len(password)}")
        
        try:
            # Use the standard JWT token generation
            from graphql_jwt.shortcuts import get_token
            from django.contrib.auth import authenticate
            
            print(f"Attempting authentication...")
            user = authenticate(username=username, password=password)
            print(f"Authentication result: {user}")
            
            if user is None:
                print("Authentication failed: Invalid credentials")
                return TokenAuth(
                    success=False,
                    token=None,
                    refreshToken=None,
                    errors=["Invalid credentials"]
                )
            
            if not user.is_active:
                print("Authentication failed: User inactive")
                return TokenAuth(
                    success=False,
                    token=None,
                    refreshToken=None,
                    errors=["User account is disabled"]
                )
            
            print(f"Generating token for user: {user.username}")
            token = get_token(user)
            print(f"Token generated: {token[:20]}...")
            
            # Generate refresh token if configured
            refresh_token = None
            try:
                from graphql_jwt.refresh_token.shortcuts import create_refresh_token
                refresh_token = create_refresh_token(user)
                print(f"Refresh token generated")
            except ImportError:
                print("Refresh token not available (not configured)")
                pass
            except Exception as e:
                print(f"Refresh token error: {e}")
            
            result = TokenAuth(
                success=True,
                token=token,
                refreshToken=refresh_token,
                errors=None
            )
            print(f"=== TokenAuth Success ===")
            return result
            
        except Exception as e:
            print(f"=== TokenAuth Exception ===")
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return TokenAuth(
                success=False,
                token=None,
                refreshToken=None,
                errors=[str(e)]
            )
