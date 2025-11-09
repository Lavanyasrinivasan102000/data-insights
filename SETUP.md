# Setup Instructions

## Prerequisites

- Python 3.9 or higher
- Node.js 18 or higher
- npm or yarn
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

## Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment:**
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Create `.env` file:**
   ```bash
   # Copy the example (if you created one) or create manually
   ```
   
   Add the following to `.env`:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   DATABASE_URL=sqlite:///./rag.db
   CATALOG_DIR=./catalog
   MAX_FILE_SIZE=10485760
   ALLOWED_FILE_TYPES=csv,json
   HOST=0.0.0.0
   PORT=8000
   DEBUG=True
   CORS_ORIGINS=http://localhost:3000,http://localhost:3001
   SECRET_KEY=your-secret-key-change-in-production
   ALGORITHM=HS256
   ```

6. **Run the server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

   The API will be available at `http://localhost:8000`
   API documentation at `http://localhost:8000/docs`

## Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Create `.env` file:**
   ```env
   REACT_APP_API_URL=http://localhost:8000
   ```

4. **Start development server:**
   ```bash
   npm start
   ```

   The app will open at `http://localhost:3000`

## Testing the Application

1. **Start both servers:**
   - Backend: `uvicorn app.main:app --reload` (in backend directory)
   - Frontend: `npm start` (in frontend directory)

2. **Upload a file:**
   - Go to the "Upload Files" tab
   - Drag and drop a CSV or JSON file
   - Wait for the catalog to be generated

3. **Chat with your data:**
   - Go to the "Chat" tab
   - Ask questions like:
     - "What are the total sales?"
     - "Show me sales by region"
     - "What's the average value?"

## Troubleshooting

### Backend Issues

- **Import errors**: Make sure virtual environment is activated
- **Database errors**: Delete `rag.db` and restart (will recreate)
- **Gemini API errors**: Check your API key in `.env`

### Frontend Issues

- **API connection errors**: Ensure backend is running on port 8000
- **Build errors**: Delete `node_modules` and run `npm install` again
- **CORS errors**: Check `CORS_ORIGINS` in backend `.env`

## Project Structure

```
rag/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app
│   │   ├── config.py        # Configuration
│   │   ├── models/          # Database models
│   │   ├── routers/        # API routes
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utilities
│   ├── catalog/            # Uploaded files (created at runtime)
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── components/     # React components
    │   ├── services/       # API client
    │   └── App.tsx         # Main app
    └── package.json
```

## Next Steps

- Review the [Implementation Plan](./IMPLEMENTATION_PLAN.md) for detailed architecture
- Check [Architecture](./ARCHITECTURE.md) for system design
- See [Configuration](./CONFIGURATION.md) for advanced settings

