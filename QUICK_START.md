# Quick Start Guide

## Prerequisites

- Python 3.9+
- Node.js 18+
- Google Gemini API key
- PostgreSQL or SQLite (for production/development)

## Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv\Scripts\activate 

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run database migrations (if using migrations)
# Initialize database
python -m app.database.init_db

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

## Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env

# Edit .env and set REACT_APP_API_URL=http://localhost:8000

# Start development server
npm start
```

## Environment Variables

### Backend (.env)
```
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=sqlite:///./rag.db
CATALOG_DIR=./catalog
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_FILE_TYPES=csv,json
```

### Frontend (.env)
```
REACT_APP_API_URL=http://localhost:8000
```

## Testing the Flow

1. **Start Backend**: `uvicorn app.main:app --reload`
2. **Start Frontend**: `npm start`
3. **Sign In**: Frontend will auto-generate/fetch user_id
4. **Upload File**: Drag & drop a CSV or JSON file
5. **Wait for Catalog**: System will generate catalog automatically
6. **Start Chatting**: Ask questions about your data!

## Example Queries

- "What are the total sales?"
- "Show me sales by region"
- "What's the average sales per month?"
- "List all unique products"

