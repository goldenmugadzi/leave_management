# Inspection Sync API Quick Reference

## Base URL
```
/inspections/api/sync/
```

## Authentication
All endpoints require JWT Bearer token:
```
Authorization: Bearer <your-jwt-token>
```

## Endpoints

### 1. Download E117 Inspections
```http
GET /inspections/api/sync/download-inspection-batch/
```

**Query Parameters:**
- `modified_after` (optional) - ISO timestamp for incremental sync
- `cursor` (optional) - Pagination cursor
- `limit` (optional) - Records per page (default: 50)

**Example:**
```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://server/inspections/api/sync/download-inspection-batch/?limit=20"
```

**Response:**
```json
{
  "success": true,
  "inspections": [...],
  "next_cursor": "uuid-or-null",
  "server_time": "2025-10-28T12:00:00Z",
  "count": 20
}
```

---

### 2. Download E1 Defect Reports
```http
GET /inspections/api/sync/defects/e1/
```

**Query Parameters:**
- `inspection_ids` (optional) - Comma-separated UUIDs
- `limit` (optional) - Records per page (default: 50)

**Example:**
```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://server/inspections/api/sync/defects/e1/?limit=20"
```

**Response:**
```json
{
  "success": true,
  "defect_reports": [...],
  "count": 20
}
```

---

### 3. Download E6 Certificates
```http
GET /inspections/api/sync/certificates/e6/
```

**Query Parameters:**
- `inspection_ids` (optional) - Comma-separated UUIDs
- `limit` (optional) - Records per page (default: 50)

**Example:**
```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://server/inspections/api/sync/certificates/e6/?limit=20"
```

**Response:**
```json
{
  "success": true,
  "certificates": [...],
  "count": 20
}
```

---

### 4. Download Inspection Photos
```http
GET /inspections/api/sync/inspections/<uuid:id>/photos/
```

**URL Parameters:**
- `id` - Inspection UUID

**Example:**
```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://server/inspections/api/sync/inspections/UUID-HERE/photos/"
```

**Response:**
```json
{
  "success": true,
  "photos": [
    {
      "id": "photo-uuid",
      "filename": "photo1.jpg",
      "url": "https://server/media/.../photo1.jpg",
      "caption": "Main panel",
      "timestamp": "2025-10-28T10:00:00Z",
      "gps_coordinates": {
        "latitude": -17.8252,
        "longitude": 31.0335
      },
      "content_type": "image/jpeg",
      "file_size": 1024000
    }
  ],
  "count": 1
}
```

---

### 5. Download General Defects
```http
GET /inspections/api/sync/defects/
```

**Query Parameters:**
- `inspection_ids` (optional) - Comma-separated UUIDs
- `limit` (optional) - Records per page (default: 100)

**Example:**
```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://server/inspections/api/sync/defects/?limit=50"
```

**Response:**
```json
{
  "success": true,
  "defects": [...],
  "count": 50
}
```

---

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "success": false,
  "error": {
    "message": "You do not have access to this inspection",
    "code": "FORBIDDEN"
  }
}
```

### 404 Not Found
```json
{
  "success": false,
  "error": {
    "message": "Inspection not found",
    "code": "NOT_FOUND"
  }
}
```

### 429 Too Many Requests
```json
{
  "success": false,
  "error": {
    "message": "Rate limit exceeded. Please try again later.",
    "code": "RATE_LIMIT_EXCEEDED"
  }
}
```

### 500 Internal Server Error
```json
{
  "success": false,
  "error": {
    "message": "Internal server error",
    "code": "SERVER_ERROR",
    "details": "Error description"
  }
}
```

---

## Rate Limits

- **Download endpoints:** 100 requests per minute per user
- **Upload endpoints:** 50 requests per minute per user

---

## CORS

The API supports Cross-Origin Resource Sharing (CORS) with the following headers:
- `Access-Control-Allow-Origin: *` (configure for production)
- `Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS`
- `Access-Control-Allow-Headers: Authorization, Content-Type, Accept, Origin`

---

## Getting a JWT Token

```bash
curl -X POST http://server/api/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

Use the `access` token as your Bearer token.

---

## Testing

Use the provided test script:
```bash
./test_sync_endpoints.sh http://your-server YOUR_JWT_TOKEN
```

---

## Notes

1. All timestamps use ISO 8601 format
2. UUIDs are strings (no dashes)
3. Users only see inspections from their assigned applications
4. Pagination cursors are opaque strings
5. GPS coordinates use decimal degrees format

