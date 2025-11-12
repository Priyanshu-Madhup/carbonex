# EcoSphere AI - Backend Setup

This is the FastAPI backend for the EcoSphere AI platform with SQLite-based authentication.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Running the Backend

Start the FastAPI server:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload
```

The backend will be available at: `http://localhost:8000`

## API Endpoints

- `POST /api/signup` - Register a new user
- `POST /api/login` - Login with email and password
- `GET /api/verify?token=<token>` - Verify authentication token
- `POST /api/logout` - Logout and invalidate token
- `GET /` - API health check

## Database

The application uses SQLite with a file named `users.db` that will be automatically created on first run.

### Database Schema

**users table:**
- id (INTEGER, PRIMARY KEY)
- email (TEXT, UNIQUE)
- password (TEXT, hashed with SHA-256)
- name (TEXT)
- created_at (TIMESTAMP)

**sessions table:**
- id (INTEGER, PRIMARY KEY)
- user_id (INTEGER, FOREIGN KEY)
- token (TEXT, UNIQUE)
- created_at (TIMESTAMP)
- expires_at (TIMESTAMP)

## Security Notes

This is a basic authentication system for demonstration purposes. For production use, consider:
- Using bcrypt or Argon2 for password hashing instead of SHA-256
- Implementing rate limiting
- Adding HTTPS/SSL
- Using environment variables for sensitive configuration
- Implementing CSRF protection
- Adding email verification
