# Database Structure & File Storage Explained

## Overview

When you upload a CSV file, the system stores it in **3 places**:

1. **Disk** - The actual CSV file (physical storage)
2. **Database - `files` table** - Metadata about the file (file record)
3. **Database - SQL table** - The actual data from the CSV (data table)

---

## Complete Database Structure

### 1. `users` Table
**Purpose**: Store user information

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | String (PK) | Unique user ID (UUID) |
| `created_at` | DateTime | When user was created |
| `updated_at` | DateTime | Last update time |

**Example Row**:
```
user_id: "c325b621-dc15-4ffb-ab45-82984f2f8a18"
created_at: "2024-01-15 10:30:00"
updated_at: "2024-01-15 10:30:00"
```

---

### 2. `files` Table (FILE RECORD)
**Purpose**: Store metadata about uploaded files

| Column | Type | Description |
|--------|------|-------------|
| `file_id` | String (PK) | Unique file ID (e.g., "c325b621_dc15_4ffb_ab45_82984f2f8a18_input_file_1_csv") |
| `user_id` | String (FK) | Links to `users.user_id` |
| `original_filename` | String | Original filename (e.g., "sales_data.csv") |
| `file_type` | String | File type ("csv" or "json") |
| `file_path` | String | Path to file on disk (e.g., "catalog/c325b621_dc15_4ffb_ab45_82984f2f8a18_input_file_1_csv.csv") |
| `row_count` | Integer | Number of rows in the file |
| `created_at` | DateTime | When file was uploaded |

**Example Row** (This is what we call a "FILE RECORD"):
```
file_id: "c325b621_dc15_4ffb_ab45_82984f2f8a18_input_file_1_csv"
user_id: "c325b621-dc15-4ffb-ab45-82984f2f8a18"
original_filename: "sales_data.csv"
file_type: "csv"
file_path: "catalog/c325b621_dc15_4ffb_ab45_82984f2f8a18_input_file_1_csv.csv"
row_count: 10000
created_at: "2024-01-15 10:35:00"
```

**What is a FILE RECORD?**
- A **file record** is a row in the `files` table
- It contains **metadata** about the file (filename, path, row count, etc.)
- It does **NOT** contain the actual data from the CSV
- It's like a "receipt" or "index card" that tells the system where to find the file

---

### 3. `catalogs` Table
**Purpose**: Store AI-generated catalog/summary of each file

| Column | Type | Description |
|--------|------|-------------|
| `catalog_id` | String (PK) | Unique catalog ID (UUID) |
| `file_id` | String (FK) | Links to `files.file_id` |
| `summary` | Text | AI-generated summary of the file (markdown text) |
| `metadata_json` | JSON | Structured metadata (columns, types, stats) |
| `created_at` | DateTime | When catalog was generated |

**Example Row**:
```
catalog_id: "abc123-def456-ghi789"
file_id: "c325b621_dc15_4ffb_ab45_82984f2f8a18_input_file_1_csv"
summary: "This dataset appears to track individual leads..."
metadata_json: {"columns": [...], "types": {...}, "stats": {...}}
created_at: "2024-01-15 10:36:00"
```

---

### 4. `chat_sessions` Table
**Purpose**: Store chat sessions

| Column | Type | Description |
|--------|------|-------------|
| `session_id` | String (PK) | Unique session ID (UUID) |
| `user_id` | String (FK) | Links to `users.user_id` |
| `created_at` | DateTime | When session was created |

---

### 5. `chat_messages` Table
**Purpose**: Store chat messages (conversation history)

| Column | Type | Description |
|--------|------|-------------|
| `message_id` | String (PK) | Unique message ID (UUID) |
| `session_id` | String (FK) | Links to `chat_sessions.session_id` |
| `role` | String | "user" or "assistant" |
| `content` | Text | Message content |
| `tool_calls` | JSON | SQL queries and tool calls (optional) |
| `created_at` | DateTime | When message was sent |

---

### 6. Dynamic SQL Tables (DATA TABLES)
**Purpose**: Store the actual CSV data

**Table Name**: Same as `file_id` (e.g., `c325b621_dc15_4ffb_ab45_82984f2f8a18_input_file_1_csv`)

**Structure**: Columns match the CSV columns

**Example Table**:
```sql
Table: c325b621_dc15_4ffb_ab45_82984f2f8a18_input_file_1_csv

| Date       | Lead Owner      | Source        | Deal Stage   | Account Id | First Name | Last Name | Company                |
|------------|-----------------|---------------|--------------|------------|------------|-----------|------------------------|
| 7/25/2025  | Francis Choi    | Chatbot       | Closed Lost  | e5FCF9404F | Eugene     | Graham    | Cherry Ltd             |
| 1/17/2025  | Elaine Christian| Cold Email    | Proposal Sent| F3dBcabcbe | Tina       | Hodge     | Alvarado-Yates         |
| ...        | ...             | ...           | ...          | ...        | ...        | ...       | ...                    |
```

**This is where the actual CSV data lives!**

---

## How CSV Files Are Stored

### Step-by-Step Process:

#### 1. User uploads `sales_data.csv`

```
Frontend: User selects "sales_data.csv"
    ↓
POST /api/upload
```

#### 2. Backend processes the file

```python
# 1. Generate file_id
file_id = "c325b621_dc15_4ffb_ab45_82984f2f8a18_input_file_1_csv"

# 2. Save CSV file to disk
file_path = "catalog/c325b621_dc15_4ffb_ab45_82984f2f8a18_input_file_1_csv.csv"
save_file(file_content, file_path)  # ← Physical file on disk

# 3. Load CSV into pandas DataFrame
df = pd.read_csv(file_path)  # ← Load from disk
# df contains: 10,000 rows of data

# 4. Create SQL table from DataFrame
sql_executor.create_table_from_dataframe(df, file_id)
# This creates a SQL table named: c325b621_dc15_4ffb_ab45_82984f2f8a18_input_file_1_csv
# The table contains ALL the CSV data (10,000 rows)

# 5. Create FILE RECORD in `files` table
file_record = FileModel(
    file_id=file_id,
    user_id=user_id,
    original_filename="sales_data.csv",
    file_type="csv",
    file_path="catalog/c325b621_dc15_4ffb_ab45_82984f2f8a18_input_file_1_csv.csv",
    row_count=10000
)
db.add(file_record)  # ← Save to `files` table

# 6. Generate catalog (AI summary)
catalog_summary = generate_catalog(df)  # ← AI generates summary

# 7. Create CATALOG RECORD in `catalogs` table
catalog_record = Catalog(
    file_id=file_id,
    summary=catalog_summary,
    metadata_json={...}
)
db.add(catalog_record)  # ← Save to `catalogs` table

# 8. Save catalog to disk (optional, for backup)
save_catalog(file_id, catalog_summary)  # ← Save to "catalog/file_id.txt"
```

---

## Visual Representation

### After uploading `sales_data.csv`:

```
┌─────────────────────────────────────────────────────────────┐
│ DISK (File System)                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ catalog/                                                    │
│   ├── c325b621_dc15_4ffb_ab45_82984f2f8a18_input_file_1_csv.csv  ← Physical CSV file
│   └── c325b621_dc15_4ffb_ab45_82984f2f8a18_input_file_1_csv.txt  ← Catalog text file
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ DATABASE (SQLite - rag.db)                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 1. users table                                              │
│    └── user_id: "c325b621-dc15-4ffb-ab45-82984f2f8a18"     │
│                                                             │
│ 2. files table (FILE RECORDS)                               │
│    └── file_id: "c325b621_dc15_4ffb_ab45_82984f2f8a18_input_file_1_csv"
│        user_id: "c325b621-dc15-4ffb-ab45-82984f2f8a18"     │
│        original_filename: "sales_data.csv"                  │
│        file_path: "catalog/...csv"                          │
│        row_count: 10000                                     │
│                                                             │
│ 3. catalogs table                                           │
│    └── file_id: "c325b621_dc15_4ffb_ab45_82984f2f8a18_input_file_1_csv"
│        summary: "This dataset appears to track..."          │
│        metadata_json: {...}                                 │
│                                                             │
│ 4. DATA TABLE (Dynamic SQL table)                           │
│    Table name: c325b621_dc15_4ffb_ab45_82984f2f8a18_input_file_1_csv
│    └── Contains 10,000 rows of actual CSV data             │
│        Date | Lead Owner | Source | Deal Stage | ...       │
│        -----|------------|--------|------------|---------- │
│        7/25/2025 | Francis Choi | Chatbot | Closed Lost | ... │
│        1/17/2025 | Elaine Christian | Cold Email | ... | ... │
│        ... (10,000 rows)                                    │
│                                                             │
│ 5. chat_sessions table                                      │
│    └── session_id, user_id, created_at                     │
│                                                             │
│ 6. chat_messages table                                      │
│    └── message_id, session_id, role, content, tool_calls   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Points

### 1. **File Record** (`files` table)
- **What it is**: A row in the `files` table containing metadata
- **What it contains**: File ID, filename, file path, row count, etc.
- **What it does NOT contain**: The actual CSV data
- **Purpose**: Tells the system "this file exists, here's its info"

### 2. **Data Table** (Dynamic SQL table)
- **What it is**: A SQL table with the same name as `file_id`
- **What it contains**: ALL the actual CSV data (all rows, all columns)
- **Purpose**: Stores the data so we can query it with SQL
- **How it's created**: `df.to_sql(table_name, con=engine)` converts pandas DataFrame to SQL table

### 3. **Physical File** (Disk)
- **What it is**: The actual CSV file on disk
- **Location**: `catalog/file_id.csv`
- **Purpose**: Backup/original file storage
- **Note**: The data is ALSO stored in the SQL table for faster querying

---

## Example: Querying Data

When you ask: **"Show me all sources"**

```python
# 1. System finds relevant file_id from `files` table
file_id = "c325b621_dc15_4ffb_ab45_82984f2f8a18_input_file_1_csv"

# 2. System generates SQL query
sql = 'SELECT "Source", COUNT(*) FROM c325b621_dc15_4ffb_ab45_82984f2f8a18_input_file_1_csv GROUP BY "Source"'

# 3. System executes query on DATA TABLE (not the file record!)
results = sql_executor.execute_query(file_id, sql)
# This queries the SQL table, not the `files` table!

# 4. Results are returned
[
    {"Source": "Chatbot", "COUNT(*)": 516},
    {"Source": "Cold Call", "COUNT(*)": 520},
    ...
]
```

---

## Summary

| Storage Location | What's Stored | Purpose |
|------------------|---------------|---------|
| **Disk** | Physical CSV file | Original file backup |
| **`files` table** | File metadata (FILE RECORD) | Track file information |
| **`catalogs` table** | AI-generated summary | Describe file contents |
| **Dynamic SQL table** | Actual CSV data (all rows) | Query data with SQL |

**File Record** = Metadata about the file (filename, path, row count)  
**Data Table** = The actual CSV data stored as a SQL table  
**Physical File** = The original CSV file on disk

All three are created when you upload a file, and all three are deleted when you delete a file!

