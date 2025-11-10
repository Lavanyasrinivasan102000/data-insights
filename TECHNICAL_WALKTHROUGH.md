# Technical Walkthrough: AI-Powered Data Query System

## Table of Contents
1. [Project Overview](#project-overview)
2. [Folder Structure Overview](#folder-structure-overview)
3. [Frontend Explanation (React/TypeScript)](#frontend-explanation-reacttypescript)
4. [Backend Explanation (FastAPI/Python)](#backend-explanation-fastapipython)
5. [Database Layer](#database-layer)
6. [Tech Stack & Dependencies](#tech-stack--dependencies)
7. [End-to-End Flow](#end-to-end-flow)
8. [Design Choices & Trade-offs](#design-choices--trade-offs)

---

## Project Overview

This is a **full-stack data analytics application** that enables users to upload CSV/JSON files and interact with their data using natural language queries. The system leverages **Google Gemini AI** to automatically catalog uploaded data and generate SQL queries from natural language, making data analysis accessible to non-technical users.

**Key Capabilities:**
- Automatic data cataloging using AI
- Natural language to SQL conversion
- Interactive data visualization
- Data editing through natural language
- Multi-file support with intelligent file selection

---

## Folder Structure Overview

### Root Directory Structure

```
rag/
├── backend/              # FastAPI Python backend
│   ├── app/             # Main application code
│   ├── catalog/         # Uploaded files storage (runtime)
│   ├── rag.db           # SQLite database (runtime)
│   ├── venv/            # Python virtual environment
│   └── requirements.txt # Python dependencies
│
├── frontend/            # React TypeScript frontend
│   ├── src/             # Source code
│   ├── public/          # Static assets
│   ├── node_modules/    # Node dependencies
│   └── package.json     # Node dependencies config
│
└── Documentation/       # Project documentation
    ├── README.md
    ├── ARCHITECTURE.md
    └── ...
```

### Backend Structure (`backend/app/`)

```
app/
├── main.py                    # FastAPI application entry point
├── config.py                  # Configuration management (Pydantic Settings)
│
├── database/                   # Database layer
│   └── connection.py         # SQLAlchemy engine, session factory, DB initialization
│
├── models/                     # SQLAlchemy ORM models
│   ├── user.py               # User model (user_id, timestamps)
│   ├── catalog.py            # File and Catalog models
│   └── chat.py               # ChatSession and ChatMessage models
│
├── routers/                    # API route handlers (FastAPI routers)
│   ├── auth.py               # Authentication endpoints (/api/auth/signin)
│   ├── upload.py             # File upload endpoint (/api/upload/)
│   ├── catalog.py            # Catalog retrieval (/api/catalog/{user_id})
│   ├── chat.py               # Chat interface (/api/chat/message)
│   ├── data.py               # Data table API (/api/data/table/{table_name})
│   └── data_edit.py          # Data editing endpoints (/api/data/update-row, etc.)
│
├── services/                    # Business logic layer
│   ├── gemini_service.py     # Google Gemini API integration
│   ├── catalog_generator.py   # Catalog generation orchestration
│   ├── data_processor.py     # CSV/JSON loading, normalization, statistics
│   ├── sql_executor.py        # SQL query execution with validation
│   ├── statistics_analyzer.py # Statistical analysis and anomaly detection
│   └── data_editor.py         # Natural language data editing
│
└── utils/                      # Utility functions
    ├── file_handler.py        # File ID generation, path management
    └── validators.py          # File type validation, input sanitization
```

### Frontend Structure (`frontend/src/`)

```
src/
├── App.tsx                     # Main application component (routing, user initialization)
├── index.tsx                   # React entry point
├── index.css                   # Global styles (Tailwind imports, custom CSS)
│
├── components/                 # React components
│   ├── Layout/
│   │   └── Header.tsx         # Navigation header (Upload/Chat tabs)
│   │
│   ├── Upload/
│   │   ├── FileUpload.tsx     # Drag-and-drop file upload component
│   │   └── FileList.tsx       # List of uploaded files with catalog summaries
│   │
│   ├── Chat/
│   │   ├── ChatInterface.tsx  # Main chat UI (message list, input, visualization)
│   │   ├── MessageBubble.tsx  # Individual message display component
│   │   └── ToolCallDisplay.tsx # SQL query display component
│   │
│   ├── DataTable/
│   │   ├── InteractiveDataTable.tsx # Paginated, filterable data table
│   │   └── index.ts           # Export barrel
│   │
│   └── Visualization/
│       ├── BarChart.tsx       # Bar chart component (Recharts)
│       ├── LineChart.tsx      # Line chart component (Recharts)
│       ├── KPICard.tsx        # Single number KPI display
│       ├── DataTable.tsx      # Simple table visualization
│       └── InsightsPanel.tsx  # AI-generated insights display
│
├── services/
│   └── api.ts                 # Axios-based API client (all HTTP requests)
│
├── hooks/
│   └── useDebounce.ts         # Custom hook for debouncing search input
│
└── types/
    └── index.ts               # TypeScript type definitions
```

---

## Frontend Explanation (React/TypeScript)

### Component Architecture

#### 1. **App.tsx** - Application Root
**Purpose**: Main application orchestrator

**Key Responsibilities:**
- User initialization (checks localStorage, calls `/api/auth/signin`)
- Tab navigation state management (`upload` vs `chat`)
- React Query client provider setup
- Conditional rendering based on active tab

**Code Flow:**
```typescript
// On mount: Check localStorage for userId
// If not found: Call signIn() API → Store in localStorage
// Render Header + conditional content (FileUpload/FileList or ChatInterface)
```

#### 2. **FileUpload.tsx** - File Upload Component
**Purpose**: Handle file uploads with drag-and-drop

**Key Features:**
- Uses `react-dropzone` for drag-and-drop functionality
- File validation (type, size)
- Upload progress indication
- Automatic data table display after upload
- `localStorage` persistence for uploaded file ID

**State Management:**
- `uploading`: Boolean for loading state
- `uploadStatus`: Success/error messages
- `uploadedFileId`: Currently displayed file ID
- `uploadedRowCount`: Row count for display

**Integration:**
- Calls `uploadFile()` API → Receives `file_id` and `row_count`
- Renders `InteractiveDataTable` component after successful upload
- Uses React Query to invalidate catalog cache on upload

#### 3. **FileList.tsx** - File Management
**Purpose**: Display list of uploaded files with catalog summaries

**Key Features:**
- Fetches catalogs using React Query (`getCatalogs()`)
- Expandable catalog summaries
- File deletion with confirmation
- Auto-refresh every 5 seconds

**Data Flow:**
```typescript
useQuery(['catalogs', userId], getCatalogs) 
  → Displays list of files
  → User clicks "Show Full Summary" 
  → Fetches full catalog via getFileCatalog()
```

#### 4. **ChatInterface.tsx** - Chat UI
**Purpose**: Natural language query interface

**Key Features:**
- Message history management (local state)
- Real-time message sending
- Visualization rendering based on response type
- Auto-scroll to latest message
- Session management (session_id)

**Visualization Logic:**
```typescript
// Determines which component to render based on visualization.type:
if (visualization.type === 'bar_chart') → <BarChart />
if (visualization.type === 'line_chart') → <LineChart />
if (visualization.type === 'kpi') → <KPICard />
if (visualization.type === 'table') → <DataTable />
if (visualization.type === 'insights') → <InsightsPanel />
```

#### 5. **InteractiveDataTable.tsx** - Data Preview Table
**Purpose**: Paginated, filterable, sortable data table

**Key Features:**
- Pagination (page, page_size)
- Global search across all columns
- Column sorting (asc/desc)
- Debounced search input (300ms delay)
- Error handling for deleted files

**State Management:**
- Uses React Query for data fetching
- `useDebounce` hook for search input
- Local state for pagination and sorting

**API Integration:**
```typescript
getTableData(tableName, { page, page_size, search, sort_by, sort_order })
  → Returns paginated data + metadata
```

### State Management Strategy

**React Query (Server State):**
- Catalog data (`['catalogs', userId]`)
- Table data (`['tableData', tableName, ...]`)
- Automatic caching, background refetching
- Query invalidation on mutations

**React useState (Local State):**
- UI state (active tab, input values, loading states)
- Message history in chat
- Form inputs

**localStorage (Persistence):**
- `userId`: User identification across sessions
- `lastUploadedFile_{userId}`: Last uploaded file ID
- `lastUploadedRowCount_{userId}`: Row count for display

### Routing & Navigation

**No React Router**: Simple tab-based navigation
- `activeTab` state in `App.tsx`
- Conditional rendering: `{activeTab === 'upload' ? <UploadView /> : <ChatView />}`

### API Communication

**Centralized API Client** (`services/api.ts`):
- Axios instance with base URL configuration
- Request/response interceptors for error handling
- TypeScript interfaces for all request/response types
- 60-second timeout for file uploads

**Example API Call:**
```typescript
export const sendMessage = async (request: ChatMessageRequest) => {
  const response = await api.post<ChatMessageResponse>('/api/chat/message', request);
  return response.data;
};
```

### External UI Libraries

1. **Tailwind CSS**: Utility-first CSS framework
   - Custom design system (primary/accent colors, animations)
   - Responsive design utilities
   - Custom gradients and shadows

2. **Recharts**: Charting library
   - `BarChart`, `LineChart` components
   - Responsive charts with tooltips

3. **React Dropzone**: File upload
   - Drag-and-drop functionality
   - File validation

4. **React Query**: Server state management
   - Data fetching, caching, synchronization

---

## Backend Explanation (FastAPI/Python)

### Application Entry Point

#### **main.py** - FastAPI Application
**Purpose**: Application initialization and configuration

**Key Components:**
```python
app = FastAPI(
    title="RAG Application API",
    description="Data ingestion and querying system with Gemini AI",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(catalog.router)
app.include_router(chat.router)
app.include_router(data_edit.router)
app.include_router(data.router)
```

**Startup Event:**
- Initializes database tables on application startup
- Creates tables if they don't exist

### Router Breakdown

#### 1. **auth.py** - Authentication Router
**Endpoints:**
- `POST /api/auth/signin` - Create/get user ID

**Functionality:**
- Generates UUID for `user_id`
- Creates user record in database if doesn't exist
- Returns `user_id` to frontend

**No Real Authentication**: Simplified for demo (no passwords, JWT tokens)

#### 2. **upload.py** - File Upload Router
**Endpoints:**
- `POST /api/upload/` - Upload and process file

**Process Flow:**
```python
1. Validate file type (CSV/JSON) and size (max 10MB)
2. Generate unique file_id (user_id + index + extension)
3. Save file to disk (catalog/{file_id}.{ext})
4. Load into pandas DataFrame
5. Extract sample rows and schema
6. Call Gemini API to generate catalog summary
7. Create SQL table from DataFrame (table name = file_id)
8. Store metadata in database (File and Catalog models)
9. Return file_id and row_count to frontend
```

**Key Features:**
- Conflict resolution for duplicate `file_id`
- Orphaned catalog cleanup
- Database rollback on errors
- Comprehensive logging

#### 3. **catalog.py** - Catalog Router
**Endpoints:**
- `GET /api/catalog/{user_id}` - Get all catalogs for user
- `GET /api/catalog/file/{file_id}` - Get full catalog for specific file

**Functionality:**
- Queries `Catalog` table joined with `File` table
- Returns catalog summaries with file metadata

#### 4. **chat.py** - Chat Router
**Endpoints:**
- `POST /api/chat/message` - Process natural language query

**Complex Request Flow:**
```python
1. Detect request type:
   - Small talk? → Direct Gemini response
   - Edit request? → Route to data_editor
   - Stats request? → Route to statistics_analyzer
   - Visualization customization? → Return predefined message
   - Chart type change? → Re-execute last query with new visualization
   - Metadata question? → Query Catalog table
   - Data query? → Continue to SQL generation

2. For data queries:
   a. Retrieve user's catalogs
   b. Select relevant file (intelligent file selection)
   c. Generate SQL using Gemini (with conversation history)
   d. Execute SQL query (with validation)
   e. Determine visualization type
   f. Format response with data and visualization config

3. Save message to database (ChatMessage model)
```

**Intelligent Features:**
- File selection based on keywords, file numbers, or file_id
- Ambiguous query detection (prompts user for file selection)
- Conversation context preservation
- SQL query auto-fixing (missing WHERE clauses, incomplete GROUP BY, etc.)

#### 5. **data.py** - Data Table Router
**Endpoints:**
- `GET /api/data/table/{table_name}` - Get paginated, filterable data
- `GET /api/data/table/{table_name}/columns` - Get column names and types

**Functionality:**
- Pagination (page, page_size)
- Global search (LIKE across all columns)
- Column sorting (ORDER BY)
- SQL injection prevention (column name validation, search term escaping)
- Default ordering by `rowid` for consistent pagination

#### 6. **data_edit.py** - Data Editing Router
**Endpoints:**
- `POST /api/data/update-row` - Update specific row
- `POST /api/data/insert-row` - Insert new row
- `POST /api/data/delete-row` - Delete row
- `POST /api/data/ai-batch-edit` - AI-powered batch editing

**AI Batch Edit:**
- Uses Gemini to generate UPDATE SQL from natural language
- Example: "Increase all sales by 10%" → `UPDATE table SET sales = sales * 1.1`

### Service Layer

#### 1. **gemini_service.py** - AI Integration
**Purpose**: Interface with Google Gemini API

**Key Methods:**
- `generate_catalog()`: Creates data catalog summary
- `generate_sql_query()`: Converts natural language to SQL

**SQL Generation Process:**
```python
1. Prepare prompt with:
   - User question
   - Catalog summaries (column names, types, sample values)
   - Conversation history (previous SQL queries)
   - Table name
   - Explicit examples and patterns

2. Call Gemini API

3. Extract SQL from response:
   - Remove markdown code blocks
   - Find SELECT statement
   - Trim explanatory text

4. Post-process SQL:
   - Fix truncated table names
   - Add missing GROUP BY clauses
   - Add missing WHERE clauses (for filtered counts)
   - Fix incomplete ORDER BY clauses
   - Add LIMIT for "last N rows" queries

5. Auto-fix missing WHERE clauses:
   - Extract value from user question
   - Find matching column in database
   - Construct WHERE clause
```

**Prompt Engineering:**
- Pattern-based examples (not hardcoded column names)
- Critical rules for SQL generation
- Real examples from actual data
- Step-by-step instructions for complex queries

#### 2. **catalog_generator.py** - Catalog Orchestration
**Purpose**: Coordinate catalog generation

**Process:**
```python
1. Load data (CSV/JSON) into pandas DataFrame
2. Extract sample rows (first 20)
3. Infer data types
4. Get basic statistics
5. Extract categorical values (distinct values for categorical columns)
6. Call Gemini API with schema + samples
7. Parse and store catalog summary
```

#### 3. **data_processor.py** - Data Processing
**Purpose**: File loading and data manipulation

**Functions:**
- `load_csv()`: Load CSV into DataFrame
- `load_json()`: Load and normalize JSON into DataFrame
- `normalize_json_data()`: Handle various JSON structures (arrays, objects, primitives)
- `get_sample_rows()`: Extract sample for cataloging
- `infer_types()`: Map pandas dtypes to SQL types
- `get_basic_stats()`: Calculate row count, column count, null counts

#### 4. **sql_executor.py** - SQL Execution
**Purpose**: Safe SQL query execution

**Key Features:**
- SQL injection prevention:
  - Table name validation (whitelist-based)
  - Column name validation
  - Query type validation (SELECT only)
  - Pattern matching for dangerous operations
- Error handling and logging
- Result formatting

**Validation Process:**
```python
1. Check query type (must be SELECT)
2. Validate table name (must match expected file_id)
3. Check for dangerous keywords (DROP, DELETE, INSERT, UPDATE, etc.)
4. Validate column names exist in table schema
5. Execute query
6. Return results as list of dictionaries
```

#### 5. **statistics_analyzer.py** - Statistical Analysis
**Purpose**: Perform statistical analysis and anomaly detection

**Features:**
- Outlier detection (IQR method, Z-score)
- Trend analysis
- Data quality checks (missing values, duplicates)
- Correlation analysis
- Summary statistics

**Process:**
```python
1. Load data from SQL table
2. Detect numeric columns
3. Calculate statistics (mean, median, std dev, etc.)
4. Identify outliers
5. Generate insights using Gemini
6. Return formatted results
```

#### 6. **data_editor.py** - Data Editing
**Purpose**: Natural language data editing

**Features:**
- Single row updates
- Batch updates via AI
- Row insertion
- Row deletion

**AI Batch Edit:**
- Uses Gemini to generate UPDATE SQL from instructions
- Example: "Set all status to 'active' where type is 'email'"
- Validates generated SQL before execution

### Configuration Management

#### **config.py** - Settings
**Purpose**: Centralized configuration using Pydantic Settings

**Configuration Sources:**
- Environment variables (`.env` file)
- Default values

**Key Settings:**
```python
GEMINI_API_KEY: str          # Google Gemini API key
DATABASE_URL: str            # SQLite or PostgreSQL connection string
CATALOG_DIR: str             # Directory for uploaded files
MAX_FILE_SIZE: int          # 10MB default
ALLOWED_FILE_TYPES: str      # "csv,json"
CORS_ORIGINS: str           # Comma-separated allowed origins
```

### CORS Configuration

**CORS Middleware** in `main.py`:
- Allows requests from frontend (localhost:3000)
- Configurable via `CORS_ORIGINS` environment variable
- Supports credentials

### Environment Variables

**Backend `.env` file:**
```env
GEMINI_API_KEY=your_key_here
DATABASE_URL=sqlite:///./rag.db
CATALOG_DIR=./catalog
MAX_FILE_SIZE=10485760
CORS_ORIGINS=http://localhost:3000
```

**Frontend `.env` file:**
```env
REACT_APP_API_URL=http://localhost:8000
```

---

## Database Layer

### Database Choice: SQLite (Default)

**Why SQLite:**
- Zero configuration (no separate server)
- Perfect for development and small-scale deployments
- File-based (easy backup/portability)
- Supports PostgreSQL via `DATABASE_URL` for production

### Database Schema

#### 1. **users** Table
```sql
user_id (PK, String/UUID)  -- Unique user identifier
created_at (DateTime)       -- Account creation timestamp
updated_at (DateTime)      -- Last update timestamp
```

#### 2. **files** Table
```sql
file_id (PK, String)           -- Format: {user_id}_input_file_{index}_{ext}
user_id (FK → users.user_id)    -- Owner of the file
original_filename (String)      -- Original uploaded filename
file_type (String)              -- "csv" or "json"
file_path (String)              -- Path to file on disk
row_count (Integer)             -- Number of rows in file
created_at (DateTime)           -- Upload timestamp
```

#### 3. **catalogs** Table
```sql
catalog_id (PK, UUID)           -- Unique catalog identifier
file_id (FK → files.file_id)    -- One-to-one with File
summary (Text)                  -- AI-generated catalog summary
metadata_json (JSON)            -- Additional metadata (schema, stats)
created_at (DateTime)           -- Catalog generation timestamp
```

#### 4. **chat_sessions** Table
```sql
session_id (PK, UUID)           -- Unique session identifier
user_id (FK → users.user_id)    -- Owner of session
created_at (DateTime)           -- Session creation timestamp
```

#### 5. **chat_messages** Table
```sql
message_id (PK, UUID)           -- Unique message identifier
session_id (FK → chat_sessions.session_id)
role (String)                   -- "user" or "assistant"
content (Text)                  -- Message content
tool_calls (JSON, nullable)      -- SQL queries, file IDs, etc.
created_at (DateTime)           -- Message timestamp
```

#### 6. **Dynamic SQL Tables** (Created per file)
**Table Name**: `{file_id}` (e.g., `c325b621_dc15_4ffb_ab45_82984f2f8a18_input_file_1_csv`)

**Schema**: Matches uploaded CSV/JSON columns
- Column names preserved (with quotes if spaces)
- Data types inferred from pandas
- `rowid` column (SQLite auto-increment)

**Example:**
```sql
CREATE TABLE "c325b621_dc15_4ffb_ab45_82984f2f8a18_input_file_1_csv" (
  "Date" TEXT,
  "Lead Owner" TEXT,
  "Source" TEXT,
  "Deal Stage" TEXT,
  "Account Id" TEXT,
  "First Name" TEXT,
  "Last Name" TEXT,
  "Company" TEXT,
  rowid INTEGER PRIMARY KEY
);
```

### Data Storage Strategy

**Hybrid Approach:**
1. **Files on Disk** (`catalog/` directory):
   - Original CSV/JSON files
   - Catalog text files (`.txt`)

2. **Metadata in Database**:
   - File records (`files` table)
   - Catalog summaries (`catalogs` table)

3. **Data in Database**:
   - SQL tables with actual data
   - Enables fast querying and filtering

**Benefits:**
- Fast queries (indexed SQL tables)
- Easy file management (disk storage)
- Relational integrity (database metadata)

### Database Connection

**SQLAlchemy ORM:**
- Engine creation in `database/connection.py`
- Session factory for dependency injection
- Automatic table creation on startup

**Session Management:**
```python
# Dependency injection in FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Usage in routes
@router.post("/endpoint")
async def endpoint(db: Session = Depends(get_db)):
    # Use db session
    pass
```

---

## Tech Stack & Dependencies

### Backend Dependencies (`requirements.txt`)

#### Core Framework
- **fastapi (0.104.1)**: Modern Python web framework
  - Async support, automatic API documentation
  - Type validation with Pydantic

- **uvicorn (0.24.0)**: ASGI server
  - Runs FastAPI application
  - Hot reload in development

#### Data Processing
- **pandas (2.1.3)**: Data manipulation library
  - CSV/JSON loading
  - DataFrame operations
  - Data normalization

- **numpy (1.26.2)**: Numerical computing
  - Used by pandas for calculations

#### AI/ML
- **google-generativeai (0.3.1)**: Google Gemini API client
  - Catalog generation
  - SQL query generation

#### Database
- **sqlalchemy (2.0.23)**: SQL toolkit and ORM
  - Database abstraction
  - Model definitions
  - Query building

- **alembic (1.12.1)**: Database migration tool
  - (Not actively used, but available)

#### Configuration
- **python-dotenv (1.0.0)**: Environment variable loading
  - Reads `.env` files

- **pydantic (2.5.0)**: Data validation
  - Request/response models
  - Settings management

- **pydantic-settings (2.1.0)**: Settings management
  - Environment variable parsing

#### Utilities
- **python-jose (3.3.0)**: JWT handling
  - (Available for future authentication)

- **passlib (1.7.4)**: Password hashing
  - (Available for future authentication)

#### Development
- **pytest (7.4.3)**: Testing framework
- **pytest-asyncio (0.21.1)**: Async test support
- **httpx (0.25.2)**: HTTP client for testing

### Frontend Dependencies (`package.json`)

#### Core Framework
- **react (18.2.0)**: UI library
- **react-dom (18.2.0)**: React DOM renderer
- **typescript (4.9.5)**: Type-safe JavaScript

#### Build Tools
- **react-scripts (5.0.1)**: Create React App build tool
  - Webpack, Babel, ESLint configuration

#### Styling
- **tailwindcss (3.3.6)**: Utility-first CSS framework
- **autoprefixer (10.4.16)**: CSS vendor prefixing
- **postcss (8.4.32)**: CSS processing

#### Data Fetching
- **react-query (3.39.3)**: Server state management
  - Data fetching, caching, synchronization

- **axios (1.6.2)**: HTTP client
  - API requests

#### UI Components
- **react-dropzone (14.2.3)**: File upload component
  - Drag-and-drop functionality

- **recharts (2.10.3)**: Charting library
  - Bar charts, line charts

- **react-markdown (10.1.0)**: Markdown rendering
  - For insights panel

#### Type Definitions
- **@types/react (18.2.37)**: React TypeScript types
- **@types/react-dom (18.2.15)**: React DOM TypeScript types
- **@types/node (20.10.0)**: Node.js TypeScript types

---

## End-to-End Flow

### Flow 1: File Upload & Catalog Generation

```
1. User drags CSV file into FileUpload component
   ↓
2. Frontend validates file (type, size)
   ↓
3. Frontend calls POST /api/upload/ with FormData
   ↓
4. Backend (upload.py):
   a. Validates file type and size
   b. Generates unique file_id
   c. Saves file to disk (catalog/{file_id}.csv)
   ↓
5. Backend loads file into pandas DataFrame
   ↓
6. Backend extracts:
   - Sample rows (first 20)
   - Column names and types
   - Basic statistics
   - Categorical values
   ↓
7. Backend calls Gemini API (catalog_generator.py):
   - Sends schema + samples
   - Receives catalog summary
   ↓
8. Backend creates SQL table:
   - Table name = file_id
   - Columns match CSV columns
   - Data inserted from DataFrame
   ↓
9. Backend stores metadata:
   - File record in `files` table
   - Catalog record in `catalogs` table
   ↓
10. Backend returns {file_id, row_count} to frontend
   ↓
11. Frontend:
    - Displays success message
    - Renders InteractiveDataTable component
    - Invalidates catalog cache
    - Stores file_id in localStorage
```

### Flow 2: Natural Language Query

```
1. User types: "What are the sources and their counts?"
   ↓
2. Frontend (ChatInterface.tsx):
   - Adds user message to state
   - Calls POST /api/chat/message
   ↓
3. Backend (chat.py):
   a. Detects request type (data query, not small talk)
   b. Retrieves user's catalogs from database
   c. Selects relevant file (or prompts if ambiguous)
   ↓
4. Backend calls Gemini API (gemini_service.py):
   - Sends: user question + catalog summaries + conversation history
   - Receives: SQL query
   ↓
5. Backend post-processes SQL:
   - Removes markdown
   - Fixes incomplete clauses
   - Validates table name
   ↓
6. Backend executes SQL (sql_executor.py):
   - Validates query (SELECT only, table name check)
   - Executes against SQLite
   - Returns results
   ↓
7. Backend determines visualization:
   - Analyzes result structure
   - Selects chart type (bar, line, table, KPI)
   ↓
8. Backend formats response:
   {
     "message": "Here are the sources and their counts:",
     "data": {
       "rows": [...],
       "columns": ["Source", "count"],
       "sql_query": "SELECT ..."
     },
     "visualization": {
       "type": "bar_chart",
       "input_data": [...]
     }
   }
   ↓
9. Backend saves message to database (ChatMessage model)
   ↓
10. Frontend receives response:
    - Adds assistant message to state
    - Renders appropriate visualization component
    - Displays SQL query in ToolCallDisplay
```

### Flow 3: Interactive Data Table

```
1. User uploads file → InteractiveDataTable renders
   ↓
2. Component fetches columns:
   GET /api/data/table/{file_id}/columns
   ↓
3. Component fetches first page:
   GET /api/data/table/{file_id}?page=1&page_size=10
   ↓
4. User types in search box:
   - Input debounced (300ms)
   - Triggers new query with search parameter
   ↓
5. User clicks column header:
   - Toggles sort order (asc/desc)
   - Triggers new query with sort_by parameter
   ↓
6. User changes page:
   - Updates page state
   - Triggers new query with page parameter
   ↓
7. Backend (data.py):
   - Builds WHERE clause for search (LIKE across all columns)
   - Builds ORDER BY clause for sorting
   - Calculates pagination (OFFSET, LIMIT)
   - Returns paginated results + metadata
```

### Communication Patterns

**Request Format:**
```typescript
// File Upload
POST /api/upload/
Content-Type: multipart/form-data
Body: { file: File, user_id: string }

// Chat Message
POST /api/chat/message
Content-Type: application/json
Body: { user_id: string, message: string, session_id?: string }

// Data Table
GET /api/data/table/{table_name}?page=1&page_size=10&search=term&sort_by=column&sort_order=asc
```

**Response Format:**
```typescript
// Upload Response
{ file_id: string, filename: string, status: string, row_count: number }

// Chat Response
{
  message: string,
  data?: { rows: Array, columns: string[], sql_query?: string },
  visualization?: { type: string, input_data?: Array },
  session_id: string
}

// Data Table Response
{
  data: Array<Record<string, any>>,
  columns: string[],
  pagination: { page, page_size, total_rows, total_pages, has_next, has_previous }
}
```

---

## Design Choices & Trade-offs

### 1. **FastAPI for Backend**

**Why FastAPI:**
- ✅ **High Performance**: One of the fastest Python frameworks (comparable to Node.js)
- ✅ **Async Support**: Native async/await for I/O-bound operations
- ✅ **Automatic Documentation**: Swagger UI and ReDoc out of the box
- ✅ **Type Safety**: Pydantic models for request/response validation
- ✅ **Modern Python**: Uses Python 3.9+ features

**Trade-offs:**
- ❌ **Learning Curve**: Async patterns can be complex
- ❌ **Ecosystem**: Smaller than Django/Flask (but growing)

**Decision**: Chose FastAPI for performance and developer experience. The async support is beneficial for AI API calls and database operations.

### 2. **React with TypeScript**

**Why React + TypeScript:**
- ✅ **Component Reusability**: Modular, composable UI components
- ✅ **Type Safety**: Catch errors at compile time
- ✅ **Large Ecosystem**: Rich library ecosystem
- ✅ **Developer Experience**: Great tooling (VS Code, React DevTools)

**Trade-offs:**
- ❌ **Build Complexity**: TypeScript compilation adds build step
- ❌ **Bundle Size**: Larger than vanilla JS (mitigated by code splitting)

**Decision**: TypeScript's type safety prevents runtime errors and improves maintainability. React's component model fits well with the modular UI requirements.

### 3. **SQLite for Development**

**Why SQLite:**
- ✅ **Zero Configuration**: No separate database server
- ✅ **Perfect for Development**: Fast iteration, easy setup
- ✅ **Portable**: Single file, easy backup
- ✅ **PostgreSQL Compatible**: Can switch via `DATABASE_URL`

**Trade-offs:**
- ❌ **Limited Concurrency**: Single writer limitation
- ❌ **Not for Production Scale**: Not ideal for high-traffic applications

**Decision**: SQLite for development simplicity, with PostgreSQL support for production. This allows easy local development while maintaining production scalability.

### 4. **AI-Powered SQL Generation**

**Why Gemini API:**
- ✅ **Flexibility**: Handles diverse query patterns without hardcoding
- ✅ **Natural Language**: Users can ask questions in plain English
- ✅ **Context Awareness**: Understands conversation history
- ✅ **Generalization**: Works with any dataset structure

**Trade-offs:**
- ❌ **API Dependency**: Requires internet connection and API key
- ❌ **Cost**: API calls incur costs (though Gemini is affordable)
- ❌ **Latency**: Network calls add ~1-2 seconds to query time
- ❌ **Error Handling**: AI can generate incorrect SQL (mitigated by validation and auto-fixing)

**Decision**: Accept API dependency for flexibility. The ability to handle any dataset structure without hardcoding outweighs the latency and cost concerns. Implemented robust error handling and SQL validation to catch AI mistakes.

### 5. **File Storage: Hybrid Approach**

**Why Hybrid (Disk + Database):**
- ✅ **Performance**: Fast queries via SQL tables
- ✅ **Efficiency**: Large files don't bloat database
- ✅ **Relational Integrity**: Metadata in database enables joins
- ✅ **Easy Management**: Files on disk are easy to backup/delete

**Trade-offs:**
- ❌ **Complexity**: Two storage locations to manage
- ❌ **Synchronization**: Must keep files and database in sync
- ❌ **Backup Strategy**: Need to backup both files and database

**Decision**: Hybrid approach balances performance and maintainability. SQL tables enable fast querying, while disk storage keeps the database lean.

### 6. **React Query for State Management**

**Why React Query:**
- ✅ **Automatic Caching**: Reduces unnecessary API calls
- ✅ **Background Refetching**: Keeps data fresh
- ✅ **Optimistic Updates**: Better UX for mutations
- ✅ **Loading/Error States**: Built-in state management

**Trade-offs:**
- ❌ **Additional Dependency**: Adds to bundle size
- ❌ **Learning Curve**: Different from Redux/Context patterns

**Decision**: React Query handles server state excellently, reducing boilerplate and improving UX. The caching and background refetching features are valuable for this application.

### 7. **No React Router**

**Why Tab-Based Navigation:**
- ✅ **Simplicity**: No routing configuration needed
- ✅ **State Management**: Easier to manage with useState
- ✅ **No URL Complexity**: No need for URL parameters

**Trade-offs:**
- ❌ **No Deep Linking**: Can't bookmark specific views
- ❌ **No Browser History**: Back button doesn't work as expected

**Decision**: For a simple two-tab application, tab-based navigation is sufficient. Could add React Router in the future if deep linking becomes important.

### 8. **Synchronous Catalog Generation**

**Why Synchronous:**
- ✅ **Immediate Feedback**: User sees results right away
- ✅ **Simplicity**: No polling or websockets needed
- ✅ **Error Handling**: Easier to handle errors synchronously

**Trade-offs:**
- ❌ **Latency**: Upload takes longer (depends on Gemini API)
- ❌ **Blocking**: User must wait for catalog generation

**Decision**: Synchronous generation for simplicity and immediate feedback. Could be moved to background jobs in production for better UX.

### 9. **Multi-Layer SQL Validation**

**Why Multiple Validation Layers:**
- ✅ **Security**: Reduces SQL injection risk
- ✅ **Error Prevention**: Catches issues before execution
- ✅ **Defense in Depth**: Multiple checks provide redundancy

**Trade-offs:**
- ❌ **Complexity**: More code to maintain
- ❌ **False Positives**: May reject valid queries in edge cases

**Decision**: Prioritize security with multiple validation layers. The complexity is worth the security benefits, especially when dealing with AI-generated SQL.

### 10. **Visualization Auto-Detection**

**Why Auto-Detection:**
- ✅ **User Experience**: No need to specify chart type
- ✅ **Intelligence**: System picks best visualization
- ✅ **Accessibility**: Works for non-technical users

**Trade-offs:**
- ❌ **Limitations**: May not always match user intent
- ❌ **Complexity**: Requires heuristics and pattern matching

**Decision**: Auto-detection with user override capability. Balance automation with user control. Users can still request specific chart types.

---

## Limitations & Areas for Improvement

### Current Limitations

1. **File Size**: Limited to 10MB (configurable but not optimized for large files)
2. **Concurrency**: SQLite limits concurrent writes
3. **Authentication**: No real authentication (just user_id generation)
4. **Error Recovery**: Some errors may require manual intervention
5. **Visualization Customization**: Limited color/style customization
6. **Query Complexity**: Very complex queries may require refinement

### Potential Improvements

1. **Background Processing**:
   - Move catalog generation to background jobs
   - Use Celery or similar for async tasks
   - Implement websockets for real-time updates

2. **Caching**:
   - Cache frequently used queries
   - Cache catalog summaries
   - Use Redis for session management

3. **Authentication & Authorization**:
   - Implement JWT-based authentication
   - Add role-based access control
   - Support multiple users per organization

4. **Scalability**:
   - Switch to PostgreSQL for production
   - Implement connection pooling
   - Add database indexing for performance

5. **UI/UX Enhancements**:
   - Add loading skeletons
   - Implement dark mode
   - Better mobile responsiveness
   - Query suggestions/autocomplete

6. **Advanced Features**:
   - Export visualizations as images/PDFs
   - Multiple chat sessions per user
   - Query history and favorites
   - Data export functionality
   - Real-time collaboration

7. **Testing**:
   - Unit tests for services
   - Integration tests for API endpoints
   - E2E tests for critical flows

8. **Monitoring & Logging**:
   - Structured logging
   - Error tracking (Sentry)
   - Performance monitoring
   - Usage analytics

---

## Conclusion

This project demonstrates a **modern full-stack application** with:
- **AI integration** for intelligent data processing
- **Type-safe** frontend and backend
- **Scalable architecture** with clear separation of concerns
- **Security-first** approach with multi-layer validation
- **User-friendly** interface with automatic visualization

The architecture balances **simplicity** (SQLite, tab-based navigation) with **sophistication** (AI-powered SQL generation, intelligent file selection), making it suitable for both development and production use with appropriate modifications.

---

**Key Takeaways for Interview:**
1. **End-to-end understanding**: Can explain entire flow from upload to visualization
2. **Architecture decisions**: Understands trade-offs and can justify choices
3. **Security awareness**: Multi-layer SQL injection prevention
4. **AI integration**: Leverages Gemini API effectively with error handling
5. **Modern stack**: FastAPI, React, TypeScript, React Query
6. **Scalability thinking**: Identifies limitations and improvement areas

