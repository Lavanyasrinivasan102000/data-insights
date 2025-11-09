# RAG Application Implementation Plan

## Project Overview
A data ingestion and querying system that allows users to upload CSV/JSON files, automatically catalog them using Gemini API, and query the data through a chat interface with SQL execution and visualization.

---

## Technology Stack

### Frontend
- **React** (with TypeScript)
- **Tailwind CSS** for styling
- **React Query / SWR** for data fetching
- **Recharts / Chart.js** for visualizations
- **Axios** for API calls

### Backend
- **Python FastAPI** for REST API
- **SQLite / PostgreSQL** for data storage
- **Pandas** for data processing
- **Google Gemini API** for catalog generation
- **SQLAlchemy** for ORM (optional)

### AI/ML
- **Google Gemini API** for:
  - Data cataloging and summarization
  - SQL query generation
  - Natural language understanding

---

## Project Structure

```
rag/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat/
│   │   │   │   ├── ChatInterface.tsx
│   │   │   │   ├── MessageList.tsx
│   │   │   │   └── MessageBubble.tsx
│   │   │   ├── Upload/
│   │   │   │   ├── FileUpload.tsx
│   │   │   │   └── FileList.tsx
│   │   │   ├── Visualization/
│   │   │   │   ├── BarChart.tsx
│   │   │   │   ├── LineChart.tsx
│   │   │   │   ├── KPICard.tsx
│   │   │   │   └── DataTable.tsx
│   │   │   └── Layout/
│   │   │       ├── Header.tsx
│   │   │       └── Sidebar.tsx
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   └── websocket.ts (optional)
│   │   ├── hooks/
│   │   │   ├── useChat.ts
│   │   │   └── useFileUpload.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── utils/
│   │   │   └── formatters.ts
│   │   └── App.tsx
│   ├── package.json
│   └── tailwind.config.js
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── catalog.py
│   │   │   └── chat.py
│   │   ├── services/
│   │   │   ├── gemini_service.py
│   │   │   ├── data_processor.py
│   │   │   ├── catalog_generator.py
│   │   │   └── sql_executor.py
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── upload.py
│   │   │   ├── catalog.py
│   │   │   └── chat.py
│   │   ├── database/
│   │   │   ├── connection.py
│   │   │   └── schemas.sql
│   │   └── utils/
│   │       ├── file_handler.py
│   │       └── validators.py
│   ├── catalog/          # Data storage directory
│   ├── requirements.txt
│   └── .env.example
│
└── README.md
```

---

## Phase 1: Backend Foundation

### 1.1 Project Setup
- [ ] Initialize FastAPI project
- [ ] Set up virtual environment
- [ ] Install dependencies:
  - `fastapi`
  - `uvicorn`
  - `pandas`
  - `google-generativeai` (Gemini SDK)
  - `python-multipart` (file uploads)
  - `sqlalchemy` (database ORM)
  - `python-dotenv` (environment variables)
  - `pydantic` (data validation)

### 1.2 Configuration
- [ ] Create `config.py` with:
  - Gemini API key management
  - Database connection settings
  - File upload limits
  - Catalog directory path
- [ ] Set up `.env` file structure
- [ ] Create `.env.example` template

### 1.3 Database Schema
- [ ] Design tables:
  - `users` (user_id, created_at, updated_at)
  - `files` (file_id, user_id, original_filename, file_type, file_path, created_at)
  - `catalogs` (catalog_id, file_id, summary_text, metadata_json, created_at)
  - `chat_sessions` (session_id, user_id, created_at)
  - `chat_messages` (message_id, session_id, role, content, tool_calls, created_at)

### 1.4 Core Services

#### `data_processor.py`
- [ ] `load_csv(file_path)` → pandas DataFrame
- [ ] `load_json(file_path)` → pandas DataFrame (with flattening)
- [ ] `normalize_json_data(json_data)` → tabular format
- [ ] `get_sample_rows(df, n=20)` → sample data
- [ ] `infer_types(df)` → type information

#### `catalog_generator.py`
- [ ] `generate_catalog_summary(schema, sample_rows, row_count)` → catalog text
- [ ] `prepare_gemini_prompt(schema, samples, count)` → prompt string
- [ ] `parse_catalog_response(gemini_response)` → structured catalog
- [ ] `save_catalog(file_id, catalog_text)` → save to `catalog/{file_id}.txt`

#### `gemini_service.py`
- [ ] `initialize_gemini_client(api_key)` → client instance
- [ ] `generate_catalog(schema, samples, count)` → catalog summary
- [ ] `generate_sql_query(user_question, catalog_summaries)` → SQL query
- [ ] `chat_completion(messages, tools)` → response with tool calls

#### `sql_executor.py`
- [ ] `create_table_from_dataframe(df, table_name)` → create SQL table
- [ ] `execute_query(table_name, sql_query)` → execute and return results
- [ ] `validate_sql_query(sql_query)` → security validation
- [ ] `get_table_schema(table_name)` → schema info

### 1.5 API Routes

#### `/api/auth`
- [ ] `POST /api/auth/signin` → generate/fetch user_id
- [ ] `GET /api/auth/me` → get current user info

#### `/api/upload`
- [ ] `POST /api/upload` → accept file(s), return file_id(s)
- [ ] `GET /api/upload/{file_id}` → get file metadata

#### `/api/catalog`
- [ ] `POST /api/catalog/generate/{file_id}` → generate catalog for file
- [ ] `GET /api/catalog/{user_id}` → retrieve all catalogs for user
- [ ] `GET /api/catalog/file/{file_id}` → get specific catalog

#### `/api/chat`
- [ ] `POST /api/chat/message` → send message, get response
- [ ] `GET /api/chat/sessions/{user_id}` → get chat history
- [ ] `POST /api/chat/sql/execute` → execute SQL query

---

## Phase 2: Frontend Foundation

### 2.1 Project Setup
- [ ] Initialize React app with TypeScript
- [ ] Install Tailwind CSS
- [ ] Set up project structure
- [ ] Configure API base URL

### 2.2 Core Components

#### File Upload Component
- [ ] `FileUpload.tsx`:
  - Drag & drop interface
  - Multiple file selection
  - File type validation (CSV, JSON)
  - Upload progress indicator
  - Error handling

#### Chat Interface
- [ ] `ChatInterface.tsx`:
  - Message input field
  - Send button
  - Message history display
  - Loading states
  - Error messages

#### Visualization Components
- [ ] `BarChart.tsx` → Recharts bar chart
- [ ] `LineChart.tsx` → Recharts line chart
- [ ] `KPICard.tsx` → Single number display
- [ ] `DataTable.tsx` → Table for small results

### 2.3 State Management
- [ ] Set up React Query for API calls
- [ ] Create custom hooks:
  - `useChat()` → chat message handling
  - `useFileUpload()` → file upload logic
  - `useCatalog()` → catalog retrieval

### 2.4 API Service Layer
- [ ] `api.ts`:
  - `signIn()` → get user_id
  - `uploadFile(file)` → upload and get file_id
  - `getCatalog(userId)` → retrieve catalogs
  - `sendMessage(userId, message)` → chat API
  - `executeSQL(table, sql)` → SQL execution

---

## Phase 3: Data Ingestion Flow

### 3.1 Upload Endpoint Implementation
- [ ] Accept multipart/form-data
- [ ] Validate file types (CSV, JSON)
- [ ] Generate `file_id` using naming convention
- [ ] Save file to `catalog/{file_id}.{ext}`
- [ ] Return file metadata

### 3.2 Data Processing Pipeline
- [ ] Load CSV → DataFrame
- [ ] Load JSON → normalize → DataFrame
- [ ] Extract sample rows (10-20)
- [ ] Get schema information
- [ ] Prepare Gemini prompt

### 3.3 Catalog Generation
- [ ] Call Gemini API with:
  - Column/keys list
  - Sample rows
  - Row count
  - Type information
- [ ] Parse Gemini response
- [ ] Save catalog to `catalog/{file_id}.txt`
- [ ] Store catalog in database
- [ ] Create SQL table: `base.{file_id}`

### 3.4 Catalog Storage
- [ ] Implement `retrieve_catalog(user_id)` function
- [ ] Return list of `{file_id, summary}` objects
- [ ] Cache catalog summaries

---

## Phase 4: Chat & Query System

### 4.1 Message Handling
- [ ] Detect small talk (no tool calls needed)
- [ ] Route to appropriate handler:
  - Small talk → direct Gemini response
  - Data query → tool call flow

### 4.2 Tool Call Flow
- [ ] `retrieve_catalog(user_id)`:
  - Query database for user's catalogs
  - Return formatted list
- [ ] Data source selection:
  - Use Gemini to analyze question + catalogs
  - Select most relevant file_id
- [ ] SQL generation:
  - Use Gemini to generate SQL from question + catalog
  - Validate SQL query
  - Execute via `sql_executor`

### 4.3 Visualization Logic
- [ ] Analyze query results:
  - Detect categorical + numeric → bar chart
  - Detect time series → line chart
  - Single number → KPI card
  - Small table → data table
- [ ] Format data for visualization components
- [ ] Return visualization config in API response

### 4.4 Response Format
```json
{
  "message": "Here are the sales by region for Q1 2024",
  "data": {
    "rows": [...],
    "visualization": {
      "type": "bar_chart",
      "show_bar_chart": true,
      "input_data": [
        {"label": "West", "value": 152340},
        {"label": "East", "value": 139880}
      ]
    }
  }
}
```

---

## Phase 5: Frontend Integration

### 5.1 Chat UI Enhancement
- [ ] Display tool call results
- [ ] Show SQL queries (optional toggle)
- [ ] Render visualizations inline
- [ ] Handle streaming responses (if implemented)

### 5.2 Visualization Rendering
- [ ] Conditional rendering based on visualization type
- [ ] Responsive chart sizing
- [ ] Export chart as image (optional)
- [ ] Table pagination for large results

### 5.3 User Experience
- [ ] Loading states during:
  - File upload
  - Catalog generation
  - SQL execution
  - Gemini API calls
- [ ] Error handling and user-friendly messages
- [ ] File list display with catalog status
- [ ] Session persistence

---

## Phase 6: Security & Optimization

### 6.1 Security
- [ ] SQL injection prevention (parameterized queries)
- [ ] File upload validation (size, type, content)
- [ ] User isolation (data access control)
- [ ] API rate limiting
- [ ] Input sanitization

### 6.2 Performance
- [ ] Large file handling (streaming, chunking)
- [ ] Catalog caching
- [ ] Database indexing
- [ ] Query optimization
- [ ] Frontend code splitting

### 6.3 Error Handling
- [ ] Graceful degradation
- [ ] Retry logic for API calls
- [ ] Comprehensive error logging
- [ ] User-friendly error messages

---

## Phase 7: Testing & Documentation

### 7.1 Testing
- [ ] Unit tests for data processing
- [ ] Unit tests for SQL executor
- [ ] Integration tests for API endpoints
- [ ] Frontend component tests
- [ ] E2E tests for full flow

### 7.2 Documentation
- [ ] API documentation (FastAPI auto-docs)
- [ ] Component documentation
- [ ] Setup instructions
- [ ] Deployment guide
- [ ] Example use cases

---

## API Endpoints Summary

### Authentication
- `POST /api/auth/signin` → `{user_id: string}`

### File Upload
- `POST /api/upload` → `{file_id: string, filename: string, status: string}`
- `GET /api/upload/{file_id}` → file metadata

### Catalog
- `POST /api/catalog/generate/{file_id}` → `{catalog_id: string, status: string}`
- `GET /api/catalog/{user_id}` → `[{file_id, summary}, ...]`
- `GET /api/catalog/file/{file_id}` → full catalog details

### Chat
- `POST /api/chat/message` → `{message: string, data?: {...}, visualization?: {...}}`
- `POST /api/chat/sql/execute` → `{rows: [...], columns: [...]}`
- `GET /api/chat/sessions/{user_id}` → chat history

---

## Data Models

### File Model
```python
{
  "file_id": "user_id_input_file_1_csv",
  "user_id": "uuid-string",
  "original_filename": "sales_2024.csv",
  "file_type": "csv",
  "file_path": "catalog/user_id_input_file_1_csv.csv",
  "row_count": 1000,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Catalog Model
```python
{
  "catalog_id": "uuid",
  "file_id": "user_id_input_file_1_csv",
  "summary": "Markdown catalog text...",
  "metadata": {
    "columns": [...],
    "types": {...},
    "stats": {...}
  },
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Chat Message Model
```python
{
  "message_id": "uuid",
  "session_id": "uuid",
  "user_id": "uuid",
  "role": "user|assistant",
  "content": "I want to know the sales",
  "tool_calls": [...],
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

## Gemini Prompts

### Catalog Generation Prompt
```
You are a data cataloging assistant. Analyze the following data schema and samples:

Schema: {columns/keys}
Sample Rows: {10-20 rows}
Total Rows: {count}

Generate a concise catalog summary (250-400 words) including:
1. Column/keys list with inferred types
2. Null rates and sample values
3. Basic statistics (numeric: min/max/mean; categorical: cardinality)
4. Time columns and grain
5. Potential join keys
6. Quality notes (duplicates, missingness, anomalies)

Format as markdown.
```

### SQL Generation Prompt
```
Given the user question: "{question}"

And available data catalogs:
{catalog_summaries}

Generate a SQL query to answer the question. Use table name: base.{file_id}

Return only the SQL query, no explanation.
```

---

## Implementation Priority

1. **Week 1**: Backend foundation (Phases 1-2)
2. **Week 2**: Data ingestion (Phase 3)
3. **Week 3**: Chat system (Phase 4)
4. **Week 4**: Frontend integration (Phase 5)
5. **Week 5**: Polish, security, testing (Phases 6-7)

---

## Next Steps

1. Review and approve this plan
2. Set up development environment
3. Initialize both frontend and backend projects
4. Begin Phase 1 implementation
5. Set up Gemini API credentials
6. Create initial database schema

