# Data Insights - AI-Powered Data Query System

A full-stack application that allows users to upload CSV/JSON files, automatically catalog them using Google Gemini API, and query the data through a natural language chat interface with SQL execution and visualization.

## 🚀 Features

- **File Upload**: Support for CSV and JSON files with drag-and-drop interface
- **Automatic Cataloging**: AI-powered data summarization using Google Gemini API
- **Natural Language Queries**: Ask questions about your data in plain English
- **Intelligent SQL Generation**: Automatic SQL query generation from natural language
- **Data Visualizations**: Automatic chart generation (bar charts, line charts, KPI cards, tables)
- **Interactive Data Tables**: Paginated, filterable, and sortable data preview
- **Multi-file Support**: Handle multiple datasets per user with file selection
- **Statistical Analysis**: Anomaly detection, trend analysis, and data insights
- **Data Editing**: Natural language-based data editing capabilities

## 📋 Tech Stack

### Frontend
- **React 18** with **TypeScript** - Type-safe UI development
- **Tailwind CSS** - Utility-first styling with custom design system
- **Recharts** - Data visualization library
- **React Query** - Server state management and caching
- **React Dropzone** - File upload handling

### Backend
- **FastAPI** - Modern Python web framework
- **SQLite** (default) / **PostgreSQL** (production-ready)
- **SQLAlchemy** - ORM for database operations
- **Pandas** - Data processing and analysis
- **Google Gemini API** - AI-powered catalog generation and SQL query generation

## 🏗️ Architecture

### System Overview

```
┌─────────────────┐
│   React Frontend │  ← User Interface (TypeScript + Tailwind)
│  (Port 3000)     │
└────────┬─────────┘
         │ HTTP/REST API
         │
┌────────▼─────────┐
│  FastAPI Backend │  ← API Server (Python)
│   (Port 8000)    │
└────────┬─────────┘
         │
    ┌────┴────┬──────────┬─────────────┐
    │         │          │             │
┌───▼───┐ ┌─▼────┐ ┌───▼──┐ ┌────────▼────┐
│SQLite │ │Gemini│ │Catalog│ │ File System │
│  DB   │ │ API  │ │ Files │ │  (catalog/) │
└───────┘ └──────┘ └───────┘ └─────────────┘
```

### Key Components

**Backend Services:**
- `gemini_service.py` - AI integration for catalog generation and SQL query generation
- `sql_executor.py` - Safe SQL execution with validation and injection prevention
- `catalog_generator.py` - Automatic data cataloging from uploaded files
- `data_processor.py` - CSV/JSON loading and data normalization
- `statistics_analyzer.py` - Statistical analysis and anomaly detection
- `data_editor.py` - Natural language-based data editing

**Frontend Components:**
- `FileUpload` - Drag-and-drop file upload with preview
- `FileList` - Display uploaded files with catalog summaries
- `ChatInterface` - Natural language query interface
- `InteractiveDataTable` - Paginated, filterable data preview
- Visualization components (BarChart, LineChart, KPICard, DataTable)

### Data Flow

1. **File Upload**: User uploads CSV/JSON → Backend processes → Creates SQL table → Generates catalog → Stores metadata
2. **Query Processing**: User asks question → Backend selects relevant file → Generates SQL → Executes query → Determines visualization → Returns results
3. **Visualization**: Results analyzed → Chart type selected → Data formatted → Rendered in frontend

## 🏃 Running Locally

### Prerequisites

- **Python 3.9+** (tested with 3.11)
- **Node.js 18+** (tested with 18.x)
- **Google Gemini API Key** ([Get one here](https://makersuite.google.com/app/apikey))
- **npm** or **yarn**

### Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd rag
```

### Step 2: Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
# Copy the example below and add your GEMINI_API_KEY
```

**Backend `.env` file:**
```env
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=sqlite:///./rag.db
CATALOG_DIR=./catalog
MAX_FILE_SIZE=10485760
ALLOWED_FILE_TYPES=csv,json
HOST=0.0.0.0
PORT=8000
DEBUG=True
CORS_ORIGINS=http://localhost:3000
```

**Start the backend server:**
```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

### Step 3: Frontend Setup

```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install dependencies
npm install

# Create .env file
# Add the following:
```

**Frontend `.env` file:**
```env
REACT_APP_API_URL=http://localhost:8000
```

**Start the frontend server:**
```bash
npm start
```

The app will open at `http://localhost:3000`

### Step 4: Test the Application

1. **Upload a file**: Go to the "Upload Files" tab and drag & drop a CSV or JSON file
2. **Wait for catalog**: The system will automatically generate a catalog summary
3. **Query your data**: Switch to the "Chat" tab and ask questions like:
   - "What are the total sales?"
   - "Show me sales by region"
   - "How many records are there?"
   - "Show me the last 10 rows"
   - "What are the sources and their counts?"

## 🎨 Design Trade-offs

### 1. **SQLite vs PostgreSQL**

**Choice**: SQLite for development, PostgreSQL for production

**Trade-offs**:
- ✅ **SQLite**: Zero configuration, perfect for development and small datasets
- ❌ **SQLite**: Limited concurrency, not ideal for production with multiple users
- ✅ **PostgreSQL**: Production-ready, better concurrency, advanced features
- ❌ **PostgreSQL**: Requires setup and configuration

**Decision**: Use SQLite by default for easy local development, but support PostgreSQL via `DATABASE_URL` for production deployments.

### 2. **AI-Powered SQL Generation**

**Choice**: Use Google Gemini API to generate SQL from natural language

**Trade-offs**:
- ✅ **Flexibility**: Handles diverse query patterns without hardcoding
- ✅ **Natural Language**: Users can ask questions in plain English
- ❌ **API Dependency**: Requires internet connection and API key
- ❌ **Cost**: API calls incur costs (though Gemini is relatively affordable)
- ❌ **Latency**: Network calls add ~1-2 seconds to query time

**Decision**: Accept API dependency for the flexibility and user experience benefits. Implement caching and error handling to mitigate issues.

### 3. **File Storage: Database vs File System**

**Choice**: Store files on disk, metadata in database

**Trade-offs**:
- ✅ **File System**: Simple, efficient for large files, easy to manage
- ✅ **Database**: Fast metadata queries, relational integrity
- ❌ **File System**: Requires backup strategy, not as portable
- ❌ **Database**: Would bloat database with binary data

**Decision**: Hybrid approach - files on disk (`catalog/` directory), metadata in database. This balances performance and maintainability.

### 4. **Client-Side State Management**

**Choice**: React Query for server state, React useState for local state

**Trade-offs**:
- ✅ **React Query**: Automatic caching, background refetching, optimistic updates
- ✅ **Simple State**: useState sufficient for UI state
- ❌ **React Query**: Additional dependency, learning curve
- ❌ **No Global State**: Context/Redux might be needed for complex apps

**Decision**: React Query handles server state well, useState for UI state. Avoids over-engineering while providing good UX.

### 5. **SQL Injection Prevention**

**Choice**: Multi-layer validation (whitelist, pattern matching, parameterized queries)

**Trade-offs**:
- ✅ **Security**: Multiple layers reduce attack surface
- ✅ **Validation**: Catches issues before execution
- ❌ **Complexity**: More code to maintain
- ❌ **False Positives**: May reject valid queries in edge cases

**Decision**: Prioritize security with multiple validation layers. Accept some complexity for safety.

### 6. **Catalog Generation: Real-time vs Background**

**Choice**: Generate catalog synchronously during upload

**Trade-offs**:
- ✅ **Real-time**: User sees results immediately, better UX
- ❌ **Latency**: Upload takes longer (depends on Gemini API)
- ✅ **Background**: Faster upload, but requires polling/websockets
- ❌ **Background**: More complex implementation

**Decision**: Synchronous generation for simplicity and immediate feedback. Can be moved to background jobs in production.

### 7. **Visualization Auto-Detection**

**Choice**: Automatically determine chart type from data structure

**Trade-offs**:
- ✅ **User Experience**: No need to specify chart type
- ✅ **Intelligence**: System picks best visualization
- ❌ **Limitations**: May not always match user intent
- ❌ **Complexity**: Requires heuristics and pattern matching

**Decision**: Auto-detection with user override capability. Balance automation with user control.

## 📁 Project Structure

```
rag/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── config.py            # Configuration management
│   │   ├── database/            # Database connection and models
│   │   │   └── connection.py
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── catalog.py
│   │   │   └── chat.py
│   │   ├── routers/             # API endpoints
│   │   │   ├── auth.py          # Authentication
│   │   │   ├── upload.py        # File upload
│   │   │   ├── catalog.py       # Catalog retrieval
│   │   │   ├── chat.py          # Chat interface
│   │   │   ├── data.py          # Data table API
│   │   │   └── data_edit.py     # Data editing
│   │   ├── services/            # Business logic
│   │   │   ├── gemini_service.py      # Gemini API integration
│   │   │   ├── catalog_generator.py    # Catalog generation
│   │   │   ├── data_processor.py       # Data processing
│   │   │   ├── sql_executor.py         # SQL execution
│   │   │   ├── statistics_analyzer.py   # Statistical analysis
│   │   │   └── data_editor.py          # Data editing
│   │   └── utils/               # Utilities
│   │       ├── file_handler.py
│   │       └── validators.py
│   ├── catalog/                 # Uploaded files (created at runtime)
│   ├── rag.db                   # SQLite database (created at runtime)
│   ├── requirements.txt         # Python dependencies
│   └── .env                     # Environment variables (not in git)
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat/            # Chat interface components
│   │   │   ├── DataTable/      # Interactive data table
│   │   │   ├── Layout/         # Layout components
│   │   │   ├── Upload/         # File upload components
│   │   │   └── Visualization/  # Chart components
│   │   ├── hooks/              # Custom React hooks
│   │   ├── services/           # API client
│   │   ├── types/              # TypeScript types
│   │   ├── App.tsx             # Main application component
│   │   └── index.tsx             # Entry point
│   ├── public/                 # Static assets
│   ├── package.json            # Node dependencies
│   └── .env                    # Environment variables (not in git)
│
└── Documentation/
    ├── README.md               # This file
    ├── ARCHITECTURE.md         # Detailed architecture
    ├── QUICK_START.md          # Quick setup guide
    ├── SETUP.md                # Detailed setup instructions
    ├── CONFIGURATION.md        # Configuration guide
    ├── DATABASE_EXPLANATION.md # Database schema details
    └── VISUALIZATION_GUIDE.md  # Visualization types guide
```

## 🔄 Workflow

1. **User Initialization**: User opens app → Auto-generates/fetches `user_id` → Stored in localStorage
2. **File Upload**: User uploads CSV/JSON → Backend processes → Creates SQL table → Generates catalog using Gemini → Stores metadata
3. **Data Query**: User asks question → Backend selects relevant file → Generates SQL using Gemini → Executes query → Analyzes results → Determines visualization → Returns formatted response
4. **Visualization**: Frontend receives data → Renders appropriate chart/table → User can interact with results

## 🔒 Security Considerations

- **SQL Injection Prevention**: Multi-layer validation, parameterized queries, whitelist-based approach
- **File Upload Security**: File type validation, size limits, content scanning
- **User Isolation**: All queries scoped to `user_id`, file access control
- **API Security**: Input validation, error message sanitization, CORS configuration

## 📖 Documentation

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Detailed system architecture and component interactions
- **[QUICK_START.md](./QUICK_START.md)** - Quick setup and getting started guide
- **[SETUP.md](./SETUP.md)** - Detailed setup instructions with troubleshooting
- **[CONFIGURATION.md](./CONFIGURATION.md)** - Configuration options and environment variables
- **[DATABASE_EXPLANATION.md](./DATABASE_EXPLANATION.md)** - Database schema and data storage details
- **[VISUALIZATION_GUIDE.md](./VISUALIZATION_GUIDE.md)** - Visualization types and use cases

## 🛠️ Development

### Running in Development Mode

**Backend:**
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm start
```

### API Documentation

Once the backend is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🧪 Example Queries

Try asking:
- "What are the total sales?"
- "Show me sales by region in a bar chart"
- "How many records are there?"
- "What are the sources and their counts?"
- "Show me the last 10 rows"
- "How many deal stage is on hold?"
- "Show anomalies in the data"
- "Can you show stats for this file?"

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## ⚠️ Known Limitations

- File size limited to 10MB by default (configurable)
- Requires Google Gemini API key (free tier available)
- SQLite database may not scale for very large datasets
- Some complex queries may require refinement
- Visualization customization is limited (colors, styles)

## 🚀 Future Enhancements

- Background catalog generation for faster uploads
- Query result caching for improved performance
- Export visualizations as images/PDFs
- Multiple chat sessions per user
- Advanced data editing with undo/redo
- Real-time collaboration features

