# Leave Management System API

A comprehensive Django REST API for managing employee leave requests with role-based access control and workflow management.

## Features

- **User Management**: Role-based access control (Employee, Manager, HR)
- **Leave Requests**: Create, submit, approve, reject, and cancel leave requests
- **Workflow**: Multi-level approval process (Manager → HR)
- **Audit Trail**: Complete history of all leave request transitions
- **Authentication**: JWT-based authentication system
- **API Documentation**: Complete Swagger/OpenAPI documentation

## API Documentation

The API is fully documented using Swagger/OpenAPI 3.0. You can access the documentation at:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## Quick Start

### 1. Install Dependencies

```bash
pip install -r reuirements.txt
```

### 2. Run Migrations

```bash
python manage.py migrate
```

### 3. Create Superuser

```bash
python manage.py createsuperuser
```

### 4. Run the Server

```bash
python manage.py runserver
```

### 5. Access API Documentation

Open your browser and navigate to:
- http://localhost:8000/api/docs/ (Swagger UI)
- http://localhost:8000/api/redoc/ (ReDoc)

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/token/` | Obtain JWT access and refresh tokens |
| POST | `/api/auth/token/refresh/` | Refresh JWT access token |

### Users

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/users/` | List all users | Authenticated |
| GET | `/api/users/{id}/` | Get user details | Authenticated |

### Leave Requests

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/leaves/` | List leave requests | Role-based |
| POST | `/api/leaves/` | Create leave request | Employee |
| GET | `/api/leaves/{id}/` | Get leave request details | Role-based |
| PUT | `/api/leaves/{id}/` | Update leave request | Owner |
| PATCH | `/api/leaves/{id}/` | Partially update leave request | Owner |
| DELETE | `/api/leaves/{id}/` | Delete leave request | Owner |
| POST | `/api/leaves/{id}/submit/` | Submit leave request | Owner |
| POST | `/api/leaves/{id}/approve/` | Approve leave request | Manager/HR |
| POST | `/api/leaves/{id}/reject/` | Reject leave request | Manager/HR |
| POST | `/api/leaves/{id}/cancel/` | Cancel leave request | Owner |

### Audit Log

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/audit-log/` | List leave transitions | HR only |
| GET | `/api/audit-log/{id}/` | Get transition details | HR only |

## User Roles

### Employee
- Create, edit, and cancel their own leave requests
- Submit draft requests for approval
- View their own request history

### Manager
- Approve/reject requests from team members
- View team members' requests
- Cannot approve their own requests

### HR
- Approve/reject any request
- View all requests and audit logs
- Final approval authority

## Leave Types

- **CL**: Casual Leave
- **SL**: Sick Leave
- **PL**: Privilege Leave

## Request Status Flow

1. **Draft** → **Submitted** (by employee)
2. **Submitted** → **Approved by Manager** (by manager)
3. **Approved by Manager** → **Approved by HR** (by HR)
4. **Rejected** (by manager or HR at any stage)
5. **Cancelled** (by employee before final approval)

## Authentication

The API uses JWT (JSON Web Tokens) for authentication:

1. **Login**: POST `/api/auth/token/` with username and password
2. **Use Token**: Include `Authorization: Bearer <token>` in request headers
3. **Refresh**: POST `/api/auth/token/refresh/` with refresh token

### Example Authentication Flow

```bash
# 1. Login to get tokens
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# Response:
# {
#   "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
#   "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
# }

# 2. Use access token for authenticated requests
curl -X GET http://localhost:8000/api/leaves/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

## API Examples

### Create Leave Request

```bash
curl -X POST http://localhost:8000/api/leaves/ \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-15",
    "end_date": "2024-01-16",
    "leave_type": "CL",
    "reason": "Personal appointment"
  }'
```

### Submit Leave Request

```bash
curl -X POST http://localhost:8000/api/leaves/1/submit/ \
  -H "Authorization: Bearer <your_token>"
```

### Approve Leave Request

```bash
curl -X POST http://localhost:8000/api/leaves/1/approve/ \
  -H "Authorization: Bearer <manager_token>"
```

## Filtering and Pagination

### Leave Requests Filtering

You can filter leave requests using query parameters:

- `status`: Filter by status (draft, submitted, approved_manager, approved_hr, rejected, cancelled)
- `leave_type`: Filter by leave type (CL, SL, PL)
- `start_date`: Filter by start date (YYYY-MM-DD)
- `end_date`: Filter by end date (YYYY-MM-DD)

Example:
```bash
GET /api/leaves/?status=submitted&leave_type=CL&start_date=2024-01-01
```

### Pagination

All list endpoints support pagination:

- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 10)

Example:
```bash
GET /api/leaves/?page=2&page_size=20
```

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- `400 Bad Request`: Validation errors
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Leave Request Creation**: Limited to prevent spam
- **General API**: 1000 requests per day per user

## Development

### Running Tests

```bash
python manage.py test
```

### Code Style

The project follows PEP 8 style guidelines. Use a linter like `flake8` or `black` for code formatting.

### Adding New Endpoints

When adding new endpoints, make sure to:

1. Add proper Swagger documentation using `@extend_schema` decorators
2. Include appropriate tags for organization
3. Add request/response examples
4. Document error cases
5. Update this README if needed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Update documentation
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 