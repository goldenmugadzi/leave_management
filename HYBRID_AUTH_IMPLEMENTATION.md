# Hybrid Authentication Implementation Summary

## Overview
Implemented hybrid authentication to enable seamless session sharing between Django admin and React frontend. Users can log in via Django admin and automatically access the React frontend without re-entering credentials.

## Backend Changes

### 1. GraphQL Schema (`it/users/schema.py`)

Added JWT token generation from Django session:

```python
# New Type
class TokenFromSessionType(graphene.ObjectType):
    """Type for JWT token generated from Django session"""
    token = graphene.String()
    refresh_token = graphene.String()
    user = graphene.Field(UserProfileType)

# New Query Field
token_from_session = graphene.Field(TokenFromSessionType)

# New Resolver
def resolve_token_from_session(self, info):
    """
    Check if user has active Django session and return JWT token
    This enables hybrid authentication between Django admin and React frontend
    """
    user = info.context.user
    
    if user and user.is_authenticated:
        token = get_token(user)
        # Optional refresh token
        try:
            from graphql_jwt.shortcuts import create_refresh_token
            refresh_token = create_refresh_token(user)
        except ImportError:
            refresh_token = None
        
        return TokenFromSessionType(
            token=token,
            refresh_token=refresh_token,
            user=user
        )
    
    return None
```

### 2. Settings Configuration (`beii_v1/settings.py`)

Added SameSite cookie settings for session sharing:

```python
# Cookie SameSite settings for cross-origin session sharing
SESSION_COOKIE_SAMESITE = 'Lax'  # Allow session cookies for same-site and top-level navigation
CSRF_COOKIE_SAMESITE = 'Lax'  # Allow CSRF cookies for same-site and top-level navigation
```

**Existing CORS settings (already configured):**
- `CORS_ALLOW_CREDENTIALS = True` ✓
- `CORS_ALLOWED_ORIGINS` includes frontend URLs ✓
- `SESSION_COOKIE_SECURE = False` (development) ✓
- `CSRF_COOKIE_HTTPONLY = False` (for React) ✓

## How It Works

1. **User logs into Django admin** → Django creates session cookie
2. **React app loads** → `checkAndRestoreSession()` runs on startup
3. **Frontend queries `tokenFromSession`** with session cookie included (credentials: 'include')
4. **Backend checks Django session**, generates JWT if valid
5. **Frontend stores JWT** and uses it for all subsequent API calls
6. **Logging out** of frontend clears JWT but keeps Django session (admin still accessible)

## Testing

### Test the Implementation:

1. **Login to Django Admin**:
   ```
   http://172.16.29.32:5300/admin/
   ```

2. **Open React Frontend**:
   ```
   http://172.16.29.32:5300/eseal/
   ```

3. **Check Browser Console** - Should see:
   ```
   "Auto-authenticated from Django session"
   ```

4. **Verify JWT Token** - Check localStorage:
   ```javascript
   localStorage.getItem('authToken')
   ```

### GraphQL Query (Test in GraphiQL):

```graphql
query {
  tokenFromSession {
    token
    refreshToken
    user {
      id
      username
      email
      firstName
      lastName
    }
  }
}
```

**Expected Response (if logged in via Django session):**
```json
{
  "data": {
    "tokenFromSession": {
      "token": "eyJ0eXAiOiJKV1QiLCJhbGciOi...",
      "refreshToken": "eyJ0eXAiOiJKV1QiLCJhbGciOi...",
      "user": {
        "id": "1",
        "username": "admin",
        "email": "admin@example.com",
        "firstName": "Admin",
        "lastName": "User"
      }
    }
  }
}
```

**Expected Response (if not logged in):**
```json
{
  "data": {
    "tokenFromSession": null
  }
}
```

## Troubleshooting

### Check Session Cookie:
1. Open browser DevTools → Application → Cookies
2. Look for `sessionid` cookie from `172.16.29.32`
3. Verify it's being sent with GraphQL requests (Network tab → Request Headers)

### Common Issues:

**Issue**: "tokenFromSession returns null"
- **Solution**: Verify user is logged into Django admin first
- Check if session cookie exists and is valid

**Issue**: "CORS error when calling tokenFromSession"
- **Solution**: Verify `CORS_ALLOW_CREDENTIALS = True` in settings
- Ensure frontend uses `credentials: 'include'` in fetch requests

**Issue**: "JWT token not working after generation"
- **Solution**: Check JWT middleware is configured in GraphQL schema
- Verify `graphql_jwt` is installed: `pip install django-graphql-jwt`

### Enable Debug Logging:

Add to `settings.py`:
```python
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'it.users.schema': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Security Considerations

- Session cookies are `Lax` (allows same-site navigation)
- Session timeout: 600 seconds (10 minutes)
- JWT tokens stored in localStorage (consider httpOnly cookies for production)
- CSRF protection enabled for state-changing operations
- Session limit: 2 concurrent sessions per user

## Dependencies

Required packages (should already be installed):
- `django-graphql-jwt` or `djangorestframework-simplejwt`
- `django-cors-headers`
- `graphene-django`

Verify installation:
```bash
pip list | grep -E "jwt|cors|graphene"
```

## Next Steps

1. **Test in production** with HTTPS enabled
2. **Set secure cookies** in production:
   ```python
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   ```
3. **Monitor session activity** in Django admin
4. **Consider refresh token rotation** for enhanced security
