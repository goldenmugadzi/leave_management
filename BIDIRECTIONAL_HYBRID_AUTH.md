# Bidirectional Hybrid Authentication

## Overview
Complete hybrid authentication system that synchronizes login/logout state between Django Admin and React Frontend in **both directions**.

## Features

✅ **Login from Django Admin** → Auto-login to React  
✅ **Login from React** → Auto-login to Django Admin  
✅ **Logout from React** → Auto-logout from Django Admin  
✅ **Logout from Django Admin** → Auto-logout from React (via session check)

## Architecture

```
┌──────────────────┐         ┌──────────────────┐
│  Django Admin    │◄───────►│  React Frontend  │
│  (Session Auth)  │         │  (JWT + Session) │
└──────────────────┘         └──────────────────┘
        ↓                            ↓
   Session Cookie              JWT Token
   (Server-side)              (Client-side)
        ↓                            ↓
   ┌────────────────────────────────┐
   │    Synchronized Auth State     │
   └────────────────────────────────┘
```

## Implementation Details

### 1. Login Flow (React → Django)

When user logs in via React frontend:

```graphql
mutation HybridLogin($username: String!, $password: String!) {
  hybridLogin(username: $username, password: $password) {
    success
    message
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

**What happens:**
1. Backend authenticates credentials
2. Creates Django session (cookie set)
3. Generates JWT token
4. Returns both to frontend
5. Frontend stores JWT in localStorage
6. Frontend now has both JWT and session cookie

**Result:** User is logged into both React app (JWT) and Django admin (session)

#### Frontend Usage:
```javascript
import { useMutation } from '@apollo/client';
import { HYBRID_LOGIN } from './graphql/mutations';

function LoginForm() {
  const [hybridLogin, { loading, error }] = useMutation(HYBRID_LOGIN);
  
  const handleLogin = async (username, password) => {
    try {
      const { data } = await hybridLogin({
        variables: { username, password }
      });
      
      if (data.hybridLogin.success) {
        // Store JWT token
        localStorage.setItem('authToken', data.hybridLogin.token);
        localStorage.setItem('user', JSON.stringify(data.hybridLogin.user));
        
        // Session cookie automatically stored by browser
        console.log('✓ Logged into both React and Django admin');
        
        // Redirect to app
        window.location.href = '/dashboard';
      } else {
        alert(data.hybridLogin.message);
      }
    } catch (err) {
      console.error('Login failed:', err);
    }
  };
  
  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      handleLogin(e.target.username.value, e.target.password.value);
    }}>
      <input name="username" placeholder="Username" />
      <input name="password" type="password" placeholder="Password" />
      <button type="submit" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}
```

### 2. Logout Flow (React → Django)

When user logs out via React frontend:

```graphql
mutation HybridLogout {
  hybridLogout {
    success
    message
  }
}
```

**What happens:**
1. Backend destroys Django session
2. Session cookie invalidated
3. Frontend removes JWT from localStorage
4. User logged out of both systems

**Result:** User is logged out of both React app and Django admin

#### Frontend Usage:
```javascript
import { useMutation } from '@apollo/client';
import { HYBRID_LOGOUT } from './graphql/mutations';

function LogoutButton() {
  const [hybridLogout] = useMutation(HYBRID_LOGOUT);
  
  const handleLogout = async () => {
    try {
      // 1. Call backend to destroy session
      const { data } = await hybridLogout();
      
      if (data.hybridLogout.success) {
        // 2. Remove JWT from localStorage
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
        
        console.log('✓ Logged out from both React and Django admin');
        
        // 3. Redirect to login
        window.location.href = '/login';
      }
    } catch (err) {
      console.error('Logout failed:', err);
      // Force logout on error
      localStorage.clear();
      window.location.href = '/login';
    }
  };
  
  return (
    <button onClick={handleLogout}>
      Logout
    </button>
  );
}
```

### 3. Auto-Login Flow (Django → React)

When user logs into Django Admin first:

**Process:**
1. User logs into Django admin → Session created
2. User opens React app → `checkAndRestoreSession()` runs
3. React queries `tokenFromSession` with session cookie
4. Backend generates JWT from active session
5. React stores JWT and authenticates user

**Result:** No re-login needed!

### 4. Auto-Logout Flow (Django → React)

When Django session expires or user logs out of admin:

**Process:**
1. Django session destroyed/expired
2. User uses React app → API calls with JWT work (JWT still valid)
3. User refreshes React app → `checkAndRestoreSession()` runs
4. `tokenFromSession` query returns null (no session)
5. React detects session lost → redirects to login

**Result:** User sees login screen on next refresh

## Complete GraphQL Schema

### Mutations

```graphql
type Mutation {
  # Login to both Django and React
  hybridLogin(username: String!, password: String!): HybridLoginType
  
  # Logout from both Django and React
  hybridLogout: HybridLogoutType
}

type HybridLoginType {
  success: Boolean!
  message: String!
  token: String          # JWT token for API calls
  refreshToken: String   # Optional refresh token
  user: UserProfileType  # User details
}

type HybridLogoutType {
  success: Boolean!
  message: String!
}
```

### Queries

```graphql
type Query {
  # Check for existing Django session and get JWT
  tokenFromSession: TokenFromSessionType
}

type TokenFromSessionType {
  token: String
  refreshToken: String
  user: UserProfileType
}
```

## Backend Logging

The system provides detailed logging for debugging:

### Login Logs:
```
============================================================
HYBRID LOGIN ATTEMPT
Username: ze9077765
============================================================
✓ Django session created for: ze9077765
Session key: 48qmgrnevq95qq9weebrhnytn1fg5s25
✓ JWT token generated (length: 164)
✓ Hybrid login successful for: ze9077765
============================================================
```

### Logout Logs:
```
============================================================
HYBRID LOGOUT
User: ze9077765
✓ Django session destroyed for: ze9077765
✓ Hybrid logout successful for: ze9077765
============================================================
```

### Session Check Logs:
```
============================================================
TOKEN_FROM_SESSION QUERY CALLED
============================================================
Request type: <class 'django.core.handlers.wsgi.WSGIRequest'>
User object: Chinaka Perseverance
User authenticated: True
Session exists: True
Session key: 48qmgrnevq95qq9weebrhnytn1fg5s25
✓ User authenticated! Generating JWT token for: ze9077765
✓ JWT token generated successfully (length: 164)
============================================================
```

## Frontend Integration

### Apollo Client Setup

```javascript
import { ApolloClient, InMemoryCache, createHttpLink, ApolloLink } from '@apollo/client';

// Auth link adds JWT to requests
const authLink = new ApolloLink((operation, forward) => {
  const token = localStorage.getItem('authToken');
  
  operation.setContext({
    headers: {
      authorization: token ? `JWT ${token}` : '',
    }
  });
  
  return forward(operation);
});

// HTTP link with credentials for session cookies
const httpLink = createHttpLink({
  uri: 'http://172.16.29.32:5300/gql/',
  credentials: 'include',  // Important: sends cookies!
});

const client = new ApolloClient({
  link: authLink.concat(httpLink),
  cache: new InMemoryCache(),
});
```

### GraphQL Queries/Mutations

```javascript
// mutations.js
import { gql } from '@apollo/client';

export const HYBRID_LOGIN = gql`
  mutation HybridLogin($username: String!, $password: String!) {
    hybridLogin(username: $username, password: $password) {
      success
      message
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
`;

export const HYBRID_LOGOUT = gql`
  mutation HybridLogout {
    hybridLogout {
      success
      message
    }
  }
`;

export const TOKEN_FROM_SESSION = gql`
  query TokenFromSession {
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
`;
```

### Session Check on App Load

```javascript
// App.js
import React, { Component } from 'react';
import { checkAndRestoreSession } from './utils/sessionCheck';

class App extends Component {
  state = {
    sessionChecked: false,
    isAuthenticated: false,
  };
  
  componentDidMount() {
    this.checkSession();
  }
  
  async checkSession() {
    console.log('[App] Checking session...');
    
    const isAuthenticated = await checkAndRestoreSession();
    
    this.setState({
      sessionChecked: true,
      isAuthenticated: isAuthenticated
    });
    
    console.log('[App] Session check complete:', isAuthenticated);
  }
  
  render() {
    const { sessionChecked, isAuthenticated } = this.state;
    
    if (!sessionChecked) {
      return <div>Loading...</div>;
    }
    
    return (
      <Router>
        {isAuthenticated ? (
          <AuthenticatedRoutes />
        ) : (
          <Route path="/login" component={LoginPage} />
        )}
      </Router>
    );
  }
}
```

## Security Considerations

### Session Security
- ✅ Session timeout: 10 minutes
- ✅ Session cookie: HttpOnly, SameSite=Lax
- ✅ Password hash validation on every request
- ✅ CSRF protection enabled

### JWT Security
- ✅ Signed with Django SECRET_KEY
- ✅ Expiration timestamp enforced
- ✅ Signature verification on every API call
- ⚠️ Stored in localStorage (consider httpOnly cookie)

### Logout Security
- ✅ Session destroyed server-side
- ✅ Frontend clears JWT
- ⚠️ JWT still valid until expiration (stateless design)
- 💡 Can implement token blacklist for immediate revocation

## Testing

### Test Login Flow

```bash
# 1. Login via GraphQL
curl -X POST http://172.16.29.32:5300/gql/ \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "query": "mutation { hybridLogin(username: \"admin\", password: \"password\") { success token user { username } } }"
  }'

# 2. Check that session cookie was set
cat cookies.txt
# Should see: sessionid=...

# 3. Verify can access Django admin with cookie
curl http://172.16.29.32:5300/admin/ \
  -b cookies.txt

# 4. Verify JWT token works
curl -X POST http://172.16.29.32:5300/gql/ \
  -H "Authorization: JWT <token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "query { me { username } }"}'
```

### Test Logout Flow

```bash
# 1. Logout via GraphQL
curl -X POST http://172.16.29.32:5300/gql/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "query": "mutation { hybridLogout { success message } }"
  }'

# 2. Verify session destroyed
curl http://172.16.29.32:5300/admin/ \
  -b cookies.txt
# Should redirect to login
```

### Test Auto-Login Flow

```bash
# 1. Login to Django admin manually
# Visit http://172.16.29.32:5300/admin/

# 2. Get JWT from session
curl -X POST http://172.16.29.32:5300/gql/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "query": "query { tokenFromSession { token user { username } } }"
  }'

# Should return JWT token
```

## Benefits

### 1. **Seamless User Experience**
- Login once, access both systems
- No repeated authentication
- Automatic session restoration

### 2. **Synchronized State**
- Logout affects both systems
- Session expiration handled consistently
- No desynchronization issues

### 3. **Flexibility**
- Users can login via either interface
- Works for web, mobile, and API clients
- Supports both traditional and modern workflows

### 4. **Security**
- Server-side session validation
- Stateless JWT for scalability
- Both methods industry-standard

### 5. **Developer Experience**
- Clear separation of concerns
- Standard authentication patterns
- Comprehensive logging for debugging

## Troubleshooting

### Issue: Login works but React doesn't get session

**Check:**
```javascript
// Ensure credentials: 'include' in Apollo
const httpLink = createHttpLink({
  uri: 'http://172.16.29.32:5300/gql/',
  credentials: 'include',  // ← Must be present!
});
```

### Issue: Logout doesn't work from React

**Check:**
```python
# Ensure logout mutation is called with session cookie
# Check Django logs for "HYBRID LOGOUT" message
```

### Issue: Auto-login not working

**Check:**
```javascript
// Ensure checkAndRestoreSession runs on app mount
componentDidMount() {
  checkAndRestoreSession();
}
```

## Summary

This bidirectional hybrid authentication system provides:

✅ **Complete synchronization** between Django Admin and React Frontend  
✅ **Login from either system** works seamlessly  
✅ **Logout from either system** affects both  
✅ **Automatic session restoration** on page load  
✅ **Industry-standard security** with sessions and JWT  
✅ **Comprehensive logging** for debugging  
✅ **Developer-friendly** with clear APIs  

The system combines the best of both worlds: traditional session-based auth for Django and modern JWT-based auth for React, with seamless synchronization between them.
