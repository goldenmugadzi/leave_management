# ACE API Documentation

This document provides details about the Asset and Capital Expenditure (ACE) system API endpoints, including authentication, data retrieval, and approval actions.

## Table of Contents
- [Authentication](#authentication)
- [ACE Management](#ace-management)
- [Budget Management](#budget-management)
- [Transactions](#transactions)
- [Viraments (Budget Transfers)](#viraments)
- [Reference Data](#reference-data)
- [User Actions](#user-actions)

## Authentication

### Login

Authenticates a user and returns a token for subsequent API calls.

- **URL**: `/api/auth/login/`
- **Method**: `POST`
- **Content Type**: `application/json`

**Request Body**:
```json
{
  "username": "john.smith",
  "password": "your_password"
}
```

**Success Response**:
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "user": {
    "id": 1,
    "username": "john.smith",
    "first_name": "John",
    "last_name": "Smith",
    "email": "john.smith@example.com",
    "section": 5,
    "region": 2,
    "roles": {
      "ace": "create",
      "pettycash": "approve"
    }
  }
}
```

### Logout

Invalidates the user's authentication token.

- **URL**: `/api/auth/logout/`
- **Method**: `POST`
- **Headers**:
  - `Authorization: Token <your_token>`

**Success Response**:
```json
{
  "message": "Successfully logged out"
}
```

**Error Response**:
```json
{
  "error": "You are not logged in"
}
```

### Current User

Returns details of the currently authenticated user.

- **URL**: `/api/auth/user/`
- **Method**: `GET`
- **Headers**:
  - `Authorization: Token <your_token>`

**Success Response**:
```json
{
  "id": 1,
  "username": "john.smith",
  "first_name": "John",
  "last_name": "Smith",
  "email": "john.smith@example.com",
  "section": 5,
  "region": 2,
  "roles": {
    "ace": "create",
    "pettycash": "approve"
  }
}
```

## ACE Management

### List All ACEs

Returns a list of ACEs based on the user's role and permissions.

- **URL**: `/api/aces/`
- **Method**: `GET`
- **Headers**:
  - `Authorization: Token <your_token>`
- **Query Parameters**:
  - `section`: Filter by section ID
  - `region`: Filter by region ID
  - `budget_id`: Filter by budget ID
  - `classification`: Filter by classification
  - `search`: Search in ACE ID and description
  - `ordering`: Order results (e.g., `-date_created` for newest first)

**Success Response**:
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "Ace_id2": "ACE202405021234",
      "details_of_expenditure": "Purchase of laptops",
      "amount": 5000.00,
      "requested_by": 1,
      "requested_by_name": "John Smith",
      "section": 5,
      "section_name": "IT Department",
      "region_name": "Eastern Region",
      "date_created": "2024-05-02T10:30:00Z",
      "budget_id": 123,
      "budget_name": "IT Department Capital Equipment",
      "classification": "Equipment",
      "approval_status": "Pending",
      "quotations": [
        {
          "id": 1,
          "quotation_file": "quotations/laptops_quote.pdf",
          "file_url": "http://example.com/media/quotations/laptops_quote.pdf"
        }
      ],
      "approvals": []
    },
    {
      "Ace_id2": "ACE202405013789",
      "details_of_expenditure": "Office furniture",
      "amount": 3200.00,
      "requested_by": 2,
      "requested_by_name": "Jane Doe",
      "section": 6,
      "section_name": "Admin Department",
      "region_name": "Eastern Region",
      "date_created": "2024-05-01T09:15:00Z",
      "budget_id": 145,
      "budget_name": "Admin Office Equipment",
      "classification": "Furniture",
      "approval_status": "Approved",
      "quotations": [
        {
          "id": 3,
          "quotation_file": "quotations/furniture_quote.pdf",
          "file_url": "http://example.com/media/quotations/furniture_quote.pdf"
        }
      ],
      "approvals": [
        {
          "id": 5,
          "step": 1,
          "step_name": "Section Head Approval",
          "user": 3,
          "user_name": "Robert Johnson",
          "approved": "Approved",
          "approved_at": "2024-05-01T14:30:00Z",
          "comment": "Within budget allocations"
        }
      ]
    }
  ]
}
```

### Retrieve Single ACE

Returns details for a specific ACE.

- **URL**: `/api/aces/{ace_id2}/`
- **Method**: `GET`
- **Headers**:
  - `Authorization: Token <your_token>`

**Success Response**:
```json
{
  "Ace_id2": "ACE202405021234",
  "details_of_expenditure": "Purchase of laptops",
  "amount": 5000.00,
  "requested_by": 1,
  "requested_by_name": "John Smith",
  "section": 5,
  "section_name": "IT Department",
  "region_name": "Eastern Region",
  "date_created": "2024-05-02T10:30:00Z",
  "budget_id": 123,
  "budget_name": "IT Department Capital Equipment",
  "classification": "Equipment",
  "approval_status": "Pending",
  "quotations": [
    {
      "id": 1,
      "quotation_file": "quotations/laptops_quote.pdf",
      "file_url": "http://example.com/media/quotations/laptops_quote.pdf"
    }
  ],
  "approvals": [],
  "asset_number": "ASSET123,ASSET124",
  "currency": "USD",
  "quantity": 2
}
```

### Create ACE

Creates a new ACE request.

- **URL**: `/api/aces/`
- **Method**: `POST`
- **Headers**:
  - `Authorization: Token <your_token>`
  - `Content-Type: multipart/form-data` (for file uploads)

**Request Body**:
```
details_of_expenditure: Purchase of laptops
amount: 5000.00
section: 5
budget_id: 123
classification: Equipment
currency: USD
quantity: 2
quotation_files: [file1, file2]
```

**Success Response**:
```json
{
  "Ace_id2": "ACE202405021235",
  "details_of_expenditure": "Purchase of laptops",
  "amount": 5000.00,
  "requested_by": 1,
  "requested_by_name": "John Smith",
  "section": 5,
  "section_name": "IT Department",
  "region_name": "Eastern Region",
  "date_created": "2024-05-02T11:45:00Z",
  "budget_id": 123,
  "budget_name": "IT Department Capital Equipment",
  "classification": "Equipment",
  "approval_status": "Pending",
  "quotations": [
    {
      "id": 2,
      "quotation_file": "quotations/laptops_quote1.pdf",
      "file_url": "http://example.com/media/quotations/laptops_quote1.pdf"
    },
    {
      "id": 3,
      "quotation_file": "quotations/laptops_quote2.pdf",
      "file_url": "http://example.com/media/quotations/laptops_quote2.pdf"
    }
  ],
  "approvals": []
}
```

### Update ACE

Updates an existing ACE request (only allowed for certain fields and if not yet approved).

- **URL**: `/api/aces/{ace_id2}/`
- **Method**: `PATCH`
- **Headers**:
  - `Authorization: Token <your_token>`
  - `Content-Type: application/json`

**Request Body**:
```json
{
  "details_of_expenditure": "Purchase of high-performance laptops",
  "quantity": 3
}
```

**Success Response**:
```json
{
  "Ace_id2": "ACE202405021234",
  "details_of_expenditure": "Purchase of high-performance laptops",
  "amount": 5000.00,
  "requested_by": 1,
  "requested_by_name": "John Smith",
  "section": 5,
  "section_name": "IT Department",
  "region_name": "Eastern Region",
  "date_created": "2024-05-02T10:30:00Z",
  "budget_id": 123,
  "budget_name": "IT Department Capital Equipment",
  "classification": "Equipment",
  "approval_status": "Pending",
  "quotations": [
    {
      "id": 1,
      "quotation_file": "quotations/laptops_quote.pdf",
      "file_url": "http://example.com/media/quotations/laptops_quote.pdf"
    }
  ],
  "approvals": [],
  "asset_number": "ASSET123,ASSET124",
  "currency": "USD",
  "quantity": 3
}
```

### Approve ACE

Approves an ACE request.

- **URL**: `/api/aces/{ace_id2}/approve/`
- **Method**: `POST`
- **Headers**:
  - `Authorization: Token <your_token>`
  - `Content-Type: application/json`

**Request Body**:
```json
{
  "comment": "Approved as per budget allocation"
}
```

**Success Response**:
```json
{
  "status": "ACE request approved"
}
```

**Error Response**:
```json
{
  "error": "You are not authorized to approve this request"
}
```

### Reject ACE

Rejects an ACE request.

- **URL**: `/api/aces/{ace_id2}/reject/`
- **Method**: `POST`
- **Headers**:
  - `Authorization: Token <your_token>`
  - `Content-Type: application/json`

**Request Body**:
```json
{
  "comment": "Rejected due to insufficient budget justification"
}
```

**Success Response**:
```json
{
  "status": "ACE request rejected"
}
```

## Budget Management

### List All Budgets

Returns a list of budgets available to the user.

- **URL**: `/api/budgets/`
- **Method**: `GET`
- **Headers**:
  - `Authorization: Token <your_token>`
- **Query Parameters**:
  - `section`: Filter by section ID
  - `region`: Filter by region ID
  - `period`: Filter by budget period (year)
  - `search`: Search in budget name

**Success Response**:
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "budget_id": 123,
      "section_code": "IT01",
      "section_name": "IT Department",
      "budget_name": "IT Department Capital Equipment",
      "allocated": 50000.00,
      "withdrawn": 15000.00,
      "balance": 35000.00,
      "awaiting_sanctioning": 5000.00,
      "period": 2024,
      "region_name": "Eastern Region"
    },
    {
      "budget_id": 124,
      "section_code": "IT01",
      "section_name": "IT Department",
      "budget_name": "IT Department Software",
      "allocated": 25000.00,
      "withdrawn": 8000.00,
      "balance": 17000.00,
      "awaiting_sanctioning": 2000.00,
      "period": 2024,
      "region_name": "Eastern Region"
    }
  ]
}
```

### Retrieve Single Budget

Returns details for a specific budget.

- **URL**: `/api/budgets/{budget_id}/`
- **Method**: `GET`
- **Headers**:
  - `Authorization: Token <your_token>`

**Success Response**:
```json
{
  "budget_id": 123,
  "section_code": "IT01",
  "section_name": "IT Department",
  "budget_name": "IT Department Capital Equipment",
  "allocated": 50000.00,
  "withdrawn": 15000.00,
  "balance": 35000.00,
  "awaiting_sanctioning": 5000.00,
  "period": 2024,
  "region_name": "Eastern Region"
}
```

### Budget Transactions

Returns all transactions for a specific budget.

- **URL**: `/api/budgets/{budget_id}/transactions/`
- **Method**: `GET`
- **Headers**:
  - `Authorization: Token <your_token>`

**Success Response**:
```json
[
  {
    "id": 1,
    "Ace_id2": 5,
    "ace_id": "ACE202405021234",
    "details_of_expenditure": "Purchase of laptops",
    "approval_status": "approved by General Manager",
    "region": 2,
    "region_name": "Eastern Region",
    "amount": 5000.00,
    "budget": 123,
    "budget_name": "IT Department Capital Equipment",
    "section": 5,
    "section_name": "IT Department"
  },
  {
    "id": 3,
    "Ace_id2": 8,
    "ace_id": "ACE202404150987",
    "details_of_expenditure": "Server hardware",
    "approval_status": "approved by General Manager",
    "region": 2,
    "region_name": "Eastern Region",
    "amount": 10000.00,
    "budget": 123,
    "budget_name": "IT Department Capital Equipment",
    "section": 5,
    "section_name": "IT Department"
  }
]
```

## Transactions

### List All Transactions

Returns a list of transactions based on user's permissions.

- **URL**: `/api/transactions/`
- **Method**: `GET`
- **Headers**:
  - `Authorization: Token <your_token>`
- **Query Parameters**:
  - `budget`: Filter by budget ID
  - `section`: Filter by section ID
  - `region`: Filter by region ID
  - `approval_status`: Filter by approval status

**Success Response**:
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "Ace_id2": 5,
      "ace_id": "ACE202405021234",
      "details_of_expenditure": "Purchase of laptops",
      "approval_status": "approved by General Manager",
      "region": 2,
      "region_name": "Eastern Region",
      "amount": 5000.00,
      "budget": 123,
      "budget_name": "IT Department Capital Equipment",
      "section": 5,
      "section_name": "IT Department"
    },
    {
      "id": 2,
      "Ace_id2": null,
      "ace_id": "",
      "details_of_expenditure": "virement of IT Department Capital Equipment to IT Department Software",
      "approval_status": "approved by General Manager",
      "region": 2,
      "region_name": "Eastern Region",
      "amount": 2000.00,
      "budget": 123,
      "budget_name": "IT Department Capital Equipment",
      "section": 5,
      "section_name": "IT Department"
    }
  ]
}
```

### Retrieve Single Transaction

Returns details for a specific transaction.

- **URL**: `/api/transactions/{transaction_id}/`
- **Method**: `GET`
- **Headers**:
  - `Authorization: Token <your_token>`

**Success Response**:
```json
{
  "id": 1,
  "Ace_id2": 5,
  "ace_id": "ACE202405021234",
  "details_of_expenditure": "Purchase of laptops",
  "approval_status": "approved by General Manager",
  "region": 2,
  "region_name": "Eastern Region",
  "amount": 5000.00,
  "budget": 123,
  "budget_name": "IT Department Capital Equipment",
  "section": 5,
  "section_name": "IT Department"
}
```

## Viraments

### List All Viraments

Returns a list of budget viraments (transfers).

- **URL**: `/api/viraments/`
- **Method**: `GET`
- **Headers**:
  - `Authorization: Token <your_token>`
- **Query Parameters**:
  - `section`: Filter by section ID
  - `from_budget`: Filter by source budget ID
  - `to_budget`: Filter by destination budget ID

**Success Response**:
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "virament_id": "VIR202405021234",
      "from_budget": 123,
      "from_budget_name": "IT Department Capital Equipment",
      "to_budget": 124,
      "to_budget_name": "IT Department Software",
      "amount": 2000.00,
      "reason": "Reallocating funds for urgent software purchase",
      "date_created": "2024-05-02T14:30:00Z",
      "requested_by": 1,
      "requested_by_name": "John Smith",
      "section": 5,
      "section_name": "IT Department",
      "approval_status": "Pending"
    }
  ]
}
```

### Retrieve Single Virament

Returns details for a specific virament.

- **URL**: `/api/viraments/{virament_id}/`
- **Method**: `GET`
- **Headers**:
  - `Authorization: Token <your_token>`

**Success Response**:
```json
{
  "virament_id": "VIR202405021234",
  "from_budget": 123,
  "from_budget_name": "IT Department Capital Equipment",
  "to_budget": 124,
  "to_budget_name": "IT Department Software",
  "amount": 2000.00,
  "reason": "Reallocating funds for urgent software purchase",
  "date_created": "2024-05-02T14:30:00Z",
  "requested_by": 1,
  "requested_by_name": "John Smith",
  "section": 5,
  "section_name": "IT Department",
  "approval_status": "Pending"
}
```

### Create Virament

Creates a new budget virament request.

- **URL**: `/api/viraments/`
- **Method**: `POST`
- **Headers**:
  - `Authorization: Token <your_token>`
  - `Content-Type: multipart/form-data` (for file uploads)

**Request Body**:
```
from_budget: 123
to_budget: 124
amount: 2000.00
reason: Reallocating funds for urgent software purchase
section: 5
quotation_files: [file1]
```

**Success Response**:
```json
{
  "virament_id": "VIR202405021235",
  "from_budget": 123,
  "from_budget_name": "IT Department Capital Equipment",
  "to_budget": 124,
  "to_budget_name": "IT Department Software",
  "amount": 2000.00,
  "reason": "Reallocating funds for urgent software purchase",
  "date_created": "2024-05-02T15:00:00Z",
  "requested_by": 1,
  "requested_by_name": "John Smith",
  "section": 5,
  "section_name": "IT Department",
  "approval_status": "Pending"
}
```

### Approve Virament

Approves a virament request.

- **URL**: `/api/viraments/{virament_id}/approve/`
- **Method**: `POST`
- **Headers**:
  - `Authorization: Token <your_token>`
  - `Content-Type: application/json`

**Request Body**:
```json
{
  "comment": "Approved budget transfer"
}
```

**Success Response**:
```json
{
  "status": "Virament approved"
}
```

## Reference Data

### List Sections

Returns a list of all sections.

- **URL**: `/api/sections/`
- **Method**: `GET`
- **Headers**:
  - `Authorization: Token <your_token>`

**Success Response**:
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 5,
      "section": "IT Department",
      "code": "IT01"
    },
    {
      "id": 6,
      "section": "Finance Department",
      "code": "FIN01"
    }
  ]
}
```

### Retrieve Single Section

Returns details for a specific section.

- **URL**: `/api/sections/{section_id}/`
- **Method**: `GET`
- **Headers**:
  - `Authorization: Token <your_token>`

**Success Response**:
```json
{
  "id": 5,
  "section": "IT Department",
  "code": "IT01"
}
```

### List Regions

Returns a list of all regions.

- **URL**: `/api/regions/`
- **Method**: `GET`
- **Headers**:
  - `Authorization: Token <your_token>`

**Success Response**:
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "region": "Western Region",
      "code": "WR"
    },
    {
      "id": 2,
      "region": "Eastern Region",
      "code": "ER"
    }
  ]
}
```

### Retrieve Single Region

Returns details for a specific region.

- **URL**: `/api/regions/{region_id}/`
- **Method**: `GET`
- **Headers**:
  - `Authorization: Token <your_token>`

**Success Response**:
```json
{
  "id": 2,
  "region": "Eastern Region",
  "code": "ER"
}
```

## User Actions

### My Actioned Items

Returns a list of ACEs that the current user has approved or rejected.

- **URL**: `/api/my-actioned-items/`
- **Method**: `GET`
- **Headers**:
  - `Authorization: Token <your_token>`

**Success Response**:
```json
[
  {
    "Ace_id2": "ACE202405021234",
    "details_of_expenditure": "Purchase of laptops",
    "amount": 5000.00,
    "requested_by": 2,
    "requested_by_name": "Jane Doe",
    "section": 5,
    "section_name": "IT Department",
    "region_name": "Eastern Region",
    "date_created": "2024-05-01T10:30:00Z",
    "budget_id": 123,
    "budget_name": "IT Department Capital Equipment",
    "classification": "Equipment",
    "approval_status": "Approved",
    "quotations": [
      {
        "id": 1,
        "quotation_file": "quotations/laptops_quote.pdf",
        "file_url": "http://example.com/media/quotations/laptops_quote.pdf"
      }
    ],
    "approvals": [
      {
        "id": 1,
        "step": 1,
        "step_name": "Section Head Approval",
        "user": 1,
        "user_name": "John Smith",
        "approved": "Approved",
        "approved_at": "2024-05-02T09:15:00Z",
        "comment": "Approved as per budget allocation"
      }
    ]
  }
]
```

## Error Responses

### Authentication Error

```json
{
  "detail": "Invalid username/password."
}
```

### Permission Error

```json
{
  "error": "You are not authorized to approve this request"
}
```

### Not Found Error

```json
{
  "detail": "Not found."
}
```

### Validation Error

```json
{
  "amount": ["This field is required."],
  "budget_id": ["This field is required."]
}
```

## Importing into Postman

To import this API documentation into Postman:

1. Create a new Postman collection
2. Click on the "Import" button in the top left
3. Select "Raw text" and paste the JSON examples from this documentation
4. Create environment variables for:
   - `base_url`: Your API base URL (e.g., "http://localhost:8000/api")
   - `token`: Your authentication token after login

For each request:
1. Set the URL to `{{base_url}}/endpoint-path/`
2. Add the Authorization header: `Authorization: Token {{token}}`
3. Configure the appropriate method, headers, and body

You can also use Postman's environment variables to store IDs for resources you frequently access.