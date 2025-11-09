# Configuration Guide

## Environment Variables

### Backend Configuration

Create a `.env` file in the `backend/` directory:

```env
# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Database Configuration
# For SQLite (development)
DATABASE_URL=sqlite:///./rag.db

# For PostgreSQL (production)
# DATABASE_URL=postgresql://user:password@localhost:5432/ragdb

# File Upload Configuration
CATALOG_DIR=./catalog
MAX_FILE_SIZE=10485760
ALLOWED_FILE_TYPES=csv,json

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
```

### Frontend Configuration

Create a `.env` file in the `frontend/` directory:

```env
# API Configuration
REACT_APP_API_URL=http://localhost:8000

# Optional: WebSocket URL (if implementing real-time features)
# REACT_APP_WS_URL=ws://localhost:8000/ws
```

## Getting a Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the API key and add it to your backend `.env` file

## Database Setup

### SQLite (Development - Default)
No additional setup required. The database file will be created automatically.

### PostgreSQL (Production)
1. Install PostgreSQL
2. Create a database:
   ```sql
   CREATE DATABASE ragdb;
   ```
3. Update `DATABASE_URL` in `.env`:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/ragdb
   ```

## File Upload Limits

- **MAX_FILE_SIZE**: Maximum file size in bytes (default: 10MB)
- **ALLOWED_FILE_TYPES**: Comma-separated list of allowed extensions

Adjust these based on your needs and server capacity.

## CORS Configuration

Update `CORS_ORIGINS` to include your frontend URLs. For production, use your actual domain:

```
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

