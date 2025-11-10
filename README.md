# RAG Application - Data Ingestion & Query System

A full-stack application that allows users to upload CSV/JSON files, automatically catalog them using Google Gemini API, and query the data through a natural language chat interface with SQL execution and visualization.

## 🚀 Features

- **File Upload**: Support for CSV and JSON files
- **Automatic Cataloging**: AI-powered data summarization using Gemini API
- **Natural Language Queries**: Ask questions about your data in plain English
- **SQL Execution**: Automatic SQL query generation and execution
- **Visualizations**: Automatic chart generation (bar, line, KPI, table)
- **Multi-file Support**: Handle multiple datasets per user

## 📋 Tech Stack

### Frontend
- React with TypeScript
- Tailwind CSS
- Recharts for visualizations
- React Query for data fetching

### Backend
- Python FastAPI
- SQLite/PostgreSQL
- Pandas for data processing
- Google Gemini API

## 📁 Project Structure

```
rag/
├── frontend/          # React application
├── backend/           # FastAPI application
├── catalog/           # Uploaded files and catalogs (created at runtime)
├── IMPLEMENTATION_PLAN.md
├── ARCHITECTURE.md
├── QUICK_START.md
└── README.md
```

## 🏃 Quick Start

See [QUICK_START.md](./QUICK_START.md) for detailed setup instructions.

### Prerequisites
- Python 3.9+
- Node.js 18+
- Google Gemini API key

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Set GEMINI_API_KEY in .env
# DATABASE_URL=sqlite:///./rag.db
# CATALOG_DIR=./catalog
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
# Set REACT_APP_API_URL in .env
npm start
```

## 📖 Documentation

- [Implementation Plan](./IMPLEMENTATION_PLAN.md) - Detailed step-by-step implementation guide
- [Architecture](./ARCHITECTURE.md) - System architecture and design
- [Quick Start](./QUICK_START.md) - Setup and getting started guide

## 🔄 Workflow

1. **Sign In**: User gets a unique `user_id`
2. **Upload Files**: Upload CSV/JSON files
3. **Automatic Cataloging**: System generates catalog summaries using Gemini
4. **Query Data**: Ask natural language questions
5. **Get Results**: Receive answers with visualizations

## 🛠️ Development Status

This is a planning phase. See [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) for the complete roadmap.

## 📝 License

MIT

