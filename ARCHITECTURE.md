# System Architecture

## High-Level Architecture

```
┌─────────────────┐
│   React Frontend │
│  (Tailwind CSS)  │
└────────┬─────────┘
         │ HTTP/REST
         │
┌────────▼─────────┐
│  FastAPI Backend │
│   (Python)       │
└────────┬─────────┘
         │
    ┌────┴────┬──────────┬─────────────┐
    │         │          │             │
┌───▼───┐ ┌─▼────┐ ┌───▼──┐ ┌────────▼────┐
│SQLite/ │ │Gemini│ │Catalog│ │ File System │
│Postgres│ │ API  │ │ Files │ │  (catalog/) │
└────────┘ └──────┘ └───────┘ └─────────────┘
```

## Data Flow

### 1. File Upload Flow
```
User → Frontend → POST /api/upload
                ↓
         Backend receives file
                ↓
         Save to catalog/{file_id}.{ext}
                ↓
         Load into pandas DataFrame
                ↓
         Extract sample + schema
                ↓
         Call Gemini API for catalog
                ↓
         Save catalog/{file_id}.txt
                ↓
         Create SQL table: base.{file_id}
                ↓
         Store metadata in database
                ↓
         Return file_id to frontend
```

### 2. Chat Query Flow
```
User Question → Frontend → POST /api/chat/message
                              ↓
                       Backend receives
                              ↓
                    [Small Talk?]
                    /           \
                  Yes            No
                   │              │
            Direct Gemini    Tool Call Flow
            Response              │
                                  ↓
                    retrieve_catalog(user_id)
                                  ↓
                    Select relevant file_id
                                  ↓
                    Generate SQL (Gemini)
                                  ↓
                    Execute SQL query
                                  ↓
                    Analyze results
                                  ↓
                    Determine visualization
                                  ↓
                    Return response + data
```

## Component Interactions

### Backend Services

```
main.py (FastAPI App)
  ├── routers/
  │   ├── auth.py → User management
  │   ├── upload.py → File handling
  │   ├── catalog.py → Catalog operations
  │   └── chat.py → Chat & query
  │
  ├── services/
  │   ├── gemini_service.py → AI interactions
  │   ├── data_processor.py → Data loading
  │   ├── catalog_generator.py → Catalog creation
  │   └── sql_executor.py → Query execution
  │
  └── database/
      └── connection.py → DB management
```

### Frontend Components

```
App.tsx
  ├── FileUpload → Upload files
  ├── ChatInterface → Chat UI
  │   ├── MessageList → Display messages
  │   └── MessageInput → User input
  └── Visualization → Render charts/tables
      ├── BarChart
      ├── LineChart
      ├── KPICard
      └── DataTable
```

## Database Schema

### Tables

**users**
- user_id (PK, UUID)
- created_at
- updated_at

**files**
- file_id (PK, string)
- user_id (FK)
- original_filename
- file_type (csv/json)
- file_path
- row_count
- created_at

**catalogs**
- catalog_id (PK, UUID)
- file_id (FK)
- summary_text (text)
- metadata_json (JSON)
- created_at

**chat_sessions**
- session_id (PK, UUID)
- user_id (FK)
- created_at

**chat_messages**
- message_id (PK, UUID)
- session_id (FK)
- role (user/assistant)
- content (text)
- tool_calls (JSON, nullable)
- created_at

**sql_tables** (dynamic)
- Created per file: `base.{file_id}`
- Schema matches uploaded data

## API Contract

### Request/Response Examples

**Sign In**
```http
POST /api/auth/signin
Response: { "user_id": "uuid-string" }
```

**Upload File**
```http
POST /api/upload
Content-Type: multipart/form-data
Body: file=@data.csv

Response: {
  "file_id": "user_id_input_file_1_csv",
  "filename": "data.csv",
  "status": "uploaded"
}
```

**Get Catalog**
```http
GET /api/catalog/{user_id}

Response: [
  {
    "file_id": "user_id_input_file_1_csv",
    "summary": "Catalog text..."
  }
]
```

**Chat Message**
```http
POST /api/chat/message
Body: {
  "user_id": "uuid",
  "message": "What are the total sales?"
}

Response: {
  "message": "The total sales are $500,000",
  "data": {
    "rows": [...],
    "visualization": {
      "type": "kpi",
      "value": 500000
    }
  }
}
```

## Security Considerations

1. **SQL Injection Prevention
   - Parameterized queries only
   - SQL validation before execution
   - Whitelist allowed operations

2. **File Upload Security
   - File type validation
   - Size limits
   - Content scanning (optional)

3. **User Isolation
   - All queries scoped to user_id
   - File access control
   - Session management

4. **API Security
   - Rate limiting
   - Input validation
   - Error message sanitization

## Scalability Considerations

1. **Database**
   - Index on user_id, file_id
   - Partition large tables (if needed)
   - Connection pooling

2. **File Storage**
   - Consider object storage (S3) for production
   - Implement file cleanup policies

3. **Caching**
   - Cache catalog summaries
   - Cache frequently used queries
   - Redis for session management (optional)

4. **API Performance**
   - Async file processing
   - Background catalog generation
   - Query result pagination

