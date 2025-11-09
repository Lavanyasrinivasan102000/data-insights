"""Chat routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.chat import ChatSession, ChatMessage
from app.models.catalog import Catalog, File as FileModel
from app.services.gemini_service import gemini_service
from app.services.sql_executor import sql_executor
from app.services.statistics_analyzer import statistics_analyzer
from app.services.data_editor import data_editor
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import re
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessageRequest(BaseModel):
    """Chat message request."""

    user_id: str
    message: str
    session_id: Optional[str] = None


class VisualizationConfig(BaseModel):
    """Visualization configuration."""

    type: str  # bar_chart, line_chart, kpi, table, insights
    show_bar_chart: bool = False
    input_data: Optional[List[Dict[str, Any]]] = None


class ChatMessageResponse(BaseModel):
    """Chat message response."""

    message: str
    data: Optional[Dict[str, Any]] = None
    visualization: Optional[VisualizationConfig] = None
    session_id: str


def is_small_talk(message: str) -> bool:
    """Detect if message is small talk."""
    small_talk_patterns = [
        r"\b(hi|hello|hey|greetings)\b",
        r"\b(how are you|how\'?s it going)\b",
        r"\b(thanks|thank you|thx)\b",
        r"\b(bye|goodbye|see you)\b",
    ]

    message_lower = message.lower()
    return any(re.search(pattern, message_lower) for pattern in small_talk_patterns)


def is_stats_request(message: str) -> bool:
    """Detect if user wants statistical analysis or insights."""
    message_lower = message.lower().strip()
    
    # Explicit patterns for anomaly/outlier detection
    anomaly_keywords = ["anomal", "outlier", "unusual", "abnormal", "exception"]
    stats_keywords = ["statistics", "stats", "statistical", "analyze", "analysis", "insights", "insight"]
    
    # Check for anomaly-related requests
    if any(keyword in message_lower for keyword in anomaly_keywords):
        logger.info(f"Detected anomaly keyword in: {message_lower}")
        return True
    
    # Check for stats/analysis requests
    if any(keyword in message_lower for keyword in stats_keywords):
        logger.info(f"Detected stats keyword in: {message_lower}")
        return True
    
    # Pattern-based detection (more specific)
    stats_patterns = [
        r"\b(show|find|detect|identify|list|display)\s+(anomal|outlier|unusual)",
        r"\b(distribution|variance|std dev|standard deviation)\b",
        r"\b(trend(s)?|pattern(s)?)\b",
        r"\b(summarize|summary)\b",
        r"\b(data quality|missing values?)\b",
        r"\b(correlation(s)?)\b",
        r"\b(show me (the )?(stats|statistics|insights))\b",
    ]
    
    for pattern in stats_patterns:
        if re.search(pattern, message_lower):
            logger.info(f"Matched stats pattern '{pattern}' for: {message_lower}")
            return True
    
    return False


def is_edit_capability_question(message: str) -> bool:
    """Detect if user is asking about edit capabilities."""
    capability_patterns = [
        r"^can\s+i\s+edit",
        r"^is\s+there\s+a\s+way\s+to\s+edit",
        r"^how\s+(do|can)\s+i\s+(edit|modify|change|update)",
        r"^is\s+it\s+possible\s+to\s+(edit|modify|change|update)",
    ]
    message_lower = message.lower().strip()
    return any(re.search(pattern, message_lower) for pattern in capability_patterns)


def is_visualization_customization_request(message: str) -> bool:
    """Detect if user is asking to customize visualization (colors only - chart type changes are handled separately)."""
    # Only detect color customization requests here
    # Chart type change requests are handled by checking for chart type keywords in the main flow
    color_customization_patterns = [
        r"\b(change|modify|update|set|make)\s+(the\s+)?(color|colour|colours|colors)",
        r"\b(color|colour|colours|colors)\s+(of|for)\s+(the\s+)?(chart|graph|bar|line)",
        r"\b(change|switch|make)\s+(it|the\s+chart|the\s+graph)\s+(to\s+)?(different\s+)?(color|colour|colours|colors)",
    ]
    message_lower = message.lower().strip()
    return any(re.search(pattern, message_lower) for pattern in color_customization_patterns)


def is_chart_type_change_request(message: str) -> bool:
    """Detect if user wants to see data in a different chart type."""
    chart_type_patterns = [
        r"\b(show|see|display|view)\s+(the\s+)?(data|it|this|that)\s+(in|as|with)\s+(a\s+)?(different\s+)?(chart|graph|table)",
        r"\b(show|see|display|view)\s+(it|this|that|the\s+data)\s+as\s+(a\s+)?(bar|line|table)",
        r"\b(chart\s+type|graph\s+type|visualization\s+type)",
        r"\b(bar\s+chart|line\s+chart|pie\s+chart|table)\s+(instead|please|now)",
        r"\b(change|switch|convert)\s+(to|into)\s+(a\s+)?(bar\s+chart|line\s+chart|table)",
        r"\b(different\s+)?(chart|graph|visualization)\s+type",
    ]
    message_lower = message.lower().strip()
    return any(re.search(pattern, message_lower) for pattern in chart_type_patterns)


def is_edit_request(message: str) -> bool:
    """Detect if user wants to edit/update/modify data."""
    # First check if it's just a question about capabilities
    if is_edit_capability_question(message):
        return False

    edit_patterns = [
        r"\b(increase|decrease|raise|lower|reduce)\b.*\bby\b",
        r"\b(set|assign)\s+.*\s+to\s+",
        r"\b(add|insert|create)\s+(a\s+)?(new\s+)?row",
        r"\b(delete|remove)\s+(row|data|entry)",
        r"\b(double|triple|halve)\b.*\b(the|all)\b",
        r"\b(multiply|divide)\b.*\bby\b",
        r"(update|change|modify)\s+.*\s+(to|=)\s+",
    ]

    message_lower = message.lower()
    return any(re.search(pattern, message_lower) for pattern in edit_patterns)


def is_file_metadata_question(question: str) -> bool:
    """Detect if user is asking about file metadata/description."""
    question_lower = question.lower().strip()
    
    # Exclude queries that are clearly about data content, not file metadata
    # These patterns indicate the user wants to query the data, not get file description
    data_query_indicators = [
        r"what.*are.*(the|under|in)",
        r"list.*(the|all|all the)",
        r"show.*(me|the|all)",
        r"count.*of",
        r"how.*many",
        r"select.*from",
        r"get.*(the|all)",
    ]
    
    # If the question contains data query indicators, it's NOT a metadata question
    for pattern in data_query_indicators:
        if re.search(pattern, question_lower):
            return False
    
    metadata_patterns = [
        r"^what.*file$",  # "what file" (standalone)
        r"^tell.*about.*file$",  # "tell about file" (standalone)
        r"file.*about$",  # "file about" (at end)
        r"describe.*file",
        r"tell.*about.*file",
        r"tell.*about.*(the\s+)?data$",  # "tell about the data" (at end, not "what are under data")
        r"^what.*dataset$",  # "what dataset" (standalone)
        r"^what.*data$",  # "what data" (standalone, not "what are the data")
        r"explain.*file",
        r"file.*description",
        r"^what.*in.*file$",  # "what in file" (standalone)
        r"file.*contains$",
        r"tell.*me.*about.*(the\s+)?file",
        r"can.*you.*tell.*about.*file",
        r"describe.*(the\s+)?file",
        r"explain.*(the\s+)?file",
    ]
    return any(re.search(pattern, question_lower) for pattern in metadata_patterns)


def select_relevant_file(question: str, catalogs: List[Dict[str, str]], db: Session = None) -> Optional[str]:
    """Select most relevant file based on question and catalogs."""
    if not catalogs:
        return None

    if len(catalogs) == 1:
        return catalogs[0]["file_id"]

    # Check if it's a file metadata question with no specific file mentioned
    is_metadata_q = is_file_metadata_question(question)
    question_lower = question.lower()
    
    # Check if user mentioned a specific file number (file 1, file 2, file2, first file, etc.)
    # Match patterns like: "file 1", "file1", "file2", "file 2", etc.
    file_number_match = re.search(r"file\s*(\d+)", question_lower)
    if file_number_match:
        file_num = int(file_number_match.group(1))
        # File numbers are 1-indexed, convert to 0-indexed
        if 1 <= file_num <= len(catalogs):
            logger.info(f"Matched file number {file_num} from question: {question}")
            return catalogs[file_num - 1]["file_id"]
    
    # Also check for just a number (e.g., "2" after "which file" prompt)
    # This handles cases where user just types "2" or "file2" without space
    # But only if the question is very short (likely a file selection response)
    if len(question_lower.strip()) <= 10:  # Short response like "file2", "2", "file 2"
        # Try to extract just a number
        just_number_match = re.search(r"^(\d+)$", question_lower.strip())
        if just_number_match:
            file_num = int(just_number_match.group(1))
            if 1 <= file_num <= len(catalogs):
                logger.info(f"Matched file number {file_num} from short response: {question}")
                return catalogs[file_num - 1]["file_id"]
    
    # Check for ordinal mentions (first, second, third file)
    if re.search(r"first\s*file", question_lower) and len(catalogs) >= 1:
        return catalogs[0]["file_id"]
    if re.search(r"second\s*file", question_lower) and len(catalogs) >= 2:
        return catalogs[1]["file_id"]
    if re.search(r"third\s*file", question_lower) and len(catalogs) >= 3:
        return catalogs[2]["file_id"]
    
    # Check if file_id is directly mentioned
    for catalog in catalogs:
        if catalog["file_id"].lower() in question_lower:
            return catalog["file_id"]
    
    # If metadata question and no specific file mentioned, return None to trigger file list
    if is_metadata_q and len(catalogs) > 1:
        return None  # Signal that we need to ask which file

    # For data queries: Try keyword matching, but if no strong match and multiple files exist,
    # return None to ask user which file (don't default to first file)
    keywords = question_lower.split()
    # Filter out common words that don't help with file selection
    stop_words = {'show', 'the', 'last', 'first', 'rows', 'row', 'data', 'me', 'can', 'you', 'get', 'give', 'tell', 'what', 'is', 'are', 'in', 'of', 'with', 'count', 'how', 'many', 'from', 'select', 'all', 'display', 'list'}
    meaningful_keywords = [kw for kw in keywords if kw not in stop_words and len(kw) > 2]

    best_match = None
    best_score = 0

    for catalog in catalogs:
        summary_lower = catalog["summary"].lower()
        # Only count meaningful keywords that actually help identify the file
        score = sum(1 for keyword in meaningful_keywords if keyword in summary_lower)
        if score > best_score:
            best_score = score
            best_match = catalog["file_id"]

    # If we have a strong match (multiple meaningful keywords), use it
    if best_score >= 2:
        logger.info(f"Selected file based on strong keyword match (score: {best_score})")
        return best_match
    
    # If no strong match and multiple files exist, ask user which file
    # This prevents defaulting to first file for ambiguous queries like "show last 5 rows"
    if len(catalogs) > 1:
        logger.info(f"Ambiguous query with {len(catalogs)} files. No strong match (score: {best_score}). Returning None to ask user.")
        return None  # Ask user which file
    
    # If only one file, return it (even with weak/no match)
    return catalogs[0]["file_id"]


def determine_visualization(rows: List[Dict[str, Any]], columns: List[str], user_message: Optional[str] = None) -> Optional[VisualizationConfig]:
    """Determine visualization type based on query results and user preferences."""
    if not rows:
        return None

    user_message_lower = (user_message or "").lower()

    # Check for explicit user preferences
    table_keywords = ["table", "row and column", "rows and columns", "list", "show as table", "as table", "in table format"]
    line_chart_keywords = ["line chart", "line graph", "linechart", "linegraph", "line"]
    bar_chart_keywords = ["bar chart", "bar graph", "barchart", "bargraph", "bars"]
    chart_keywords = ["chart", "graph", "visualize", "pie chart", "show chart", "show graph"]
    
    wants_table = any(keyword in user_message_lower for keyword in table_keywords)
    wants_line_chart = any(keyword in user_message_lower for keyword in line_chart_keywords)
    wants_bar_chart = any(keyword in user_message_lower for keyword in bar_chart_keywords)
    wants_chart = any(keyword in user_message_lower for keyword in chart_keywords)

    # Single value - KPI (unless user wants table)
    if len(rows) == 1 and len(columns) == 1:
        if wants_table:
            return VisualizationConfig(type="table", show_bar_chart=False, input_data=rows)
        value = list(rows[0].values())[0]
        return VisualizationConfig(type="kpi", show_bar_chart=False, input_data=[{"value": value}])

    # If user explicitly wants a table, return table
    if wants_table:
        return VisualizationConfig(type="table", show_bar_chart=False, input_data=rows)

    # Check for time series (date/datetime/period column + numeric) - PRIORITIZE CHARTS
    date_columns = [
        col
        for col in columns
        if any(keyword in col.lower() for keyword in ["date", "time", "day", "month", "year", "period"])
    ]
    if date_columns and len(columns) == 2 and len(rows) > 1:
        # Line chart for time series (unless user wants table)
        if wants_table:
            return VisualizationConfig(type="table", show_bar_chart=False, input_data=rows)
        return VisualizationConfig(type="line_chart", show_bar_chart=False, input_data=rows)

    # Check for categorical + numeric (bar chart) - 2 columns, multiple rows
    # Show as bar chart by default, unless user explicitly wants table or line chart
    if len(columns) == 2 and len(rows) > 1 and len(rows) <= 20:
        # Format data for charts (label/value format works for both bar and line charts)
        formatted_data = [{"label": str(row[columns[0]]), "value": row[columns[1]]} for row in rows]
        
        if wants_table:
            # User wants table, so return table
            return VisualizationConfig(type="table", show_bar_chart=False, input_data=rows)
        elif wants_line_chart:
            # User specifically wants line chart, return line chart with formatted data
            # LineChart component can handle label/value format or raw rows
            return VisualizationConfig(type="line_chart", show_bar_chart=False, input_data=formatted_data)
        else:
            # Default to bar chart for 2-column categorical data (unless user wants table or line chart)
            return VisualizationConfig(
                type="bar_chart",
                show_bar_chart=True,
                input_data=formatted_data,
            )

    # Default to table for everything else
    return VisualizationConfig(type="table", show_bar_chart=False, input_data=rows)


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(request: ChatMessageRequest, db: Session = Depends(get_db)):
    """Send a chat message and get response."""
    logger.info(f"Received message from user {request.user_id}: {request.message}")

    # Get or create session
    if request.session_id:
        session = db.query(ChatSession).filter(ChatSession.session_id == request.session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = ChatSession(user_id=request.user_id)
        db.add(session)
        db.commit()
        db.refresh(session)

    # Save user message
    user_message = ChatMessage(session_id=session.session_id, role="user", content=request.message)
    db.add(user_message)
    db.commit()

    # Check if file metadata question FIRST (before small talk check)
    # This ensures queries about file data are handled properly
    is_metadata_q = is_file_metadata_question(request.message)
    
    # Get files and catalogs early (needed for both metadata and data queries)
    files = db.query(FileModel).filter(FileModel.user_id == request.user_id).all()
    if not files:
        # No files - this might be small talk or a request for files
        if is_small_talk(request.message):
            logger.info("Detected small talk, responding directly")
            response_text = gemini_service.chat_completion(
                messages=[{"role": "user", "content": request.message}], use_tools=False
            )
            assistant_message = ChatMessage(session_id=session.session_id, role="assistant", content=response_text)
            db.add(assistant_message)
            db.commit()
            return ChatMessageResponse(message=response_text, session_id=session.session_id)
        else:
            return ChatMessageResponse(
                message="No data files found. Please upload a file first.", session_id=session.session_id
            )
    
    file_ids = [f.file_id for f in files]
    catalogs_query = db.query(Catalog).filter(Catalog.file_id.in_(file_ids)).all()
    file_map = {f.file_id: f for f in files}
    catalog_list = [
        {
            "file_id": cat.file_id,
            "summary": cat.summary,
            "original_filename": file_map[cat.file_id].original_filename if cat.file_id in file_map else cat.file_id
        }
        for cat in catalogs_query
    ]
    
    # Check if small talk (but NOT metadata questions)
    if is_small_talk(request.message) and not is_metadata_q:
        logger.info("Detected small talk, responding directly")
        # Direct response without tool calls
        response_text = gemini_service.chat_completion(
            messages=[{"role": "user", "content": request.message}], use_tools=False
        )
        logger.info(f"Small talk response: {response_text}")

        # Save assistant message
        assistant_message = ChatMessage(session_id=session.session_id, role="assistant", content=response_text)
        db.add(assistant_message)
        db.commit()

        return ChatMessageResponse(message=response_text, session_id=session.session_id)

    # Get conversation history early (needed for chart type change detection)
    previous_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
        .all()
    )  # Last 10 messages (most recent first)

    # Check if user wants to change chart type for previous data
    if is_chart_type_change_request(request.message):
        logger.info("Detected chart type change request")
        # Find the last query that returned data
        last_data_query = None
        last_visualization_type = None
        for msg in previous_messages:
            if msg.role == "assistant" and msg.tool_calls:
                tool_calls = msg.tool_calls
                if isinstance(tool_calls, dict) and "sql_query" in tool_calls:
                    last_data_query = tool_calls
                    # Try to determine what visualization was used last time
                    # Check if there's a visualization type in the response data
                    break
        
        if last_data_query and "sql_query" in last_data_query:
            # Re-execute the last query with new visualization type
            sql_query = last_data_query["sql_query"]
            table_name = last_data_query.get("file_id")
            
            if table_name:
                try:
                    logger.info(f"Re-executing previous query with different chart type: {sql_query}")
                    rows = sql_executor.execute_query(table_name, sql_query)
                    columns = list(rows[0].keys()) if rows else []
                    
                    # Determine visualization based on user's request
                    user_msg_lower = request.message.lower()
                    has_specific_chart_type = any(keyword in user_msg_lower for keyword in 
                        ["bar chart", "line chart", "table", "bar graph", "line graph", "bars", "line"])
                    
                    if not has_specific_chart_type and "different" in user_msg_lower:
                        # User wants a different chart type but didn't specify which one
                        # Try to infer what they saw before and show a different type
                        # For 2-column categorical data (like Source + Count), cycle through options
                        if len(columns) == 2 and len(rows) > 1:
                            # Check if data looks like time series (has date column)
                            date_columns = [col for col in columns if any(kw in col.lower() for kw in ["date", "time", "day", "month", "year"])]
                            if date_columns:
                                # Time series data - show as table (since line is default)
                                visualization = determine_visualization(rows, columns, user_message="show as table")
                            else:
                                # Categorical data - if they saw bar chart, show as line chart
                                # Otherwise show as table
                                visualization = determine_visualization(rows, columns, user_message="show as line chart")
                                # If it still comes out as bar chart, force table
                                if visualization and visualization.type == "bar_chart":
                                    visualization = determine_visualization(rows, columns, user_message="show as table")
                        else:
                            # Use table as safe default for other data types
                            visualization = determine_visualization(rows, columns, user_message="show as table")
                    else:
                        # User specified a chart type or determine_visualization will infer it
                        visualization = determine_visualization(rows, columns, user_message=request.message)
                    
                    logger.info(f"New visualization type: {visualization.type if visualization else 'None'}")
                    
                    chart_type_name = visualization.type.replace('_', ' ') if visualization else "chart"
                    response_text = f"I found {len(rows)} result(s). Showing in {chart_type_name} format."
                    
                    # Save assistant message
                    assistant_message = ChatMessage(
                        session_id=session.session_id,
                        role="assistant",
                        content=response_text,
                        tool_calls={"sql_query": sql_query, "file_id": table_name, "row_count": len(rows), "re_visualization": True},
                    )
                    db.add(assistant_message)
                    db.commit()
                    
                    # Prepare response
                    response_data = {"rows": rows, "columns": columns, "sql_query": sql_query, "file_id": table_name}
                    
                    return ChatMessageResponse(
                        message=response_text, data=response_data, visualization=visualization, session_id=session.session_id
                    )
                except Exception as e:
                    logger.error(f"Error re-executing query: {str(e)}", exc_info=True)
                    # Fall through to normal query flow
                    pass
        else:
            # No previous query found, give helpful message
            response_text = """I'd be happy to show your data in a different chart type! 

However, I don't see any previous data query to re-visualize. Please:
1. First ask a question about your data (e.g., "show me sources with count")
2. Then ask to see it in a different format (e.g., "show it as a line chart" or "show it as a table")

**Available chart types:**
- Bar chart: Great for comparing categories
- Line chart: Perfect for trends over time
- Table: Best for detailed data viewing

Try asking a data question first!"""

            # Save assistant message
            assistant_message = ChatMessage(session_id=session.session_id, role="assistant", content=response_text)
            db.add(assistant_message)
            db.commit()

            return ChatMessageResponse(message=response_text, session_id=session.session_id)

    # Check if visualization customization request (colors only)
    if is_visualization_customization_request(request.message):
        logger.info("Detected visualization color customization request")
        response_text = """I understand you'd like to customize the chart colors! 

Currently, the chart colors and styles are automatically set to provide the best visual experience. The system uses vibrant gradients and modern styling.

**Note:** Advanced color customization (like specifying exact colors) is not yet available in this version. The charts automatically use a modern color scheme with gradients.

**Available options:**
- You can change the chart type: "show it as a line chart" or "show it as a table"
- You can ask different questions about your data

Would you like to see your data in a different chart type or ask a new question?"""

        # Save assistant message
        assistant_message = ChatMessage(session_id=session.session_id, role="assistant", content=response_text)
        db.add(assistant_message)
        db.commit()

        return ChatMessageResponse(message=response_text, session_id=session.session_id)

    # Check if user is asking about edit capabilities
    if is_edit_capability_question(request.message):
        logger.info("Detected edit capability question")
        response_text = """Yes! You can edit your data in two ways:

1. **Natural Language Editing**: Just tell me what you want to change. For example:
   - "Increase [column name] by 10%"
   - "Set all [column name] to 0 for [condition]"
   - "Double the [column name] for [filter condition]"
   - "Change [column name] from [old value] to [new value]"
   - "Update [column name] where [condition]"

2. **Specific Instructions**: Be as specific as possible about:
   - Which rows to update (by any column values, filters, or conditions)
   - What values to change (column names and new values)
   - How to change them (increase by X%, set to Y, multiply by Z, etc.)

You can reference any columns in your dataset, and I'll help you make the changes. Try asking me to make a specific change to your data!"""

        # Save assistant message
        assistant_message = ChatMessage(session_id=session.session_id, role="assistant", content=response_text)
        db.add(assistant_message)
        db.commit()

        return ChatMessageResponse(message=response_text, session_id=session.session_id)

    # Check if edit/update request
    if is_edit_request(request.message):
        logger.info("Detected data edit request")

        # Get conversation history for context
        previous_messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session.session_id)
            .order_by(ChatMessage.created_at)
            .limit(10)
            .all()
        )
        conversation_context = []
        for msg in previous_messages:
            conversation_context.append({"role": msg.role, "content": msg.content})

        # Get user files
        files = db.query(FileModel).filter(FileModel.user_id == request.user_id).all()
        if not files:
            return ChatMessageResponse(
                message="No data files found. Please upload a file first.", session_id=session.session_id
            )

        file_ids = [f.file_id for f in files]
        catalogs_query = db.query(Catalog).filter(Catalog.file_id.in_(file_ids)).all()
        catalog_list = [{"file_id": cat.file_id, "summary": cat.summary} for cat in catalogs_query]

        # Select relevant file
        selected_file_id = select_relevant_file(request.message, catalog_list)
        logger.info(f"Selected file for edit: {selected_file_id}")

        # Get catalog summary
        catalog = db.query(Catalog).filter(Catalog.file_id == selected_file_id).first()
        catalog_summary = catalog.summary if catalog else "No catalog available"

        # Execute AI batch edit
        try:
            result = data_editor.ai_batch_edit(
                table_name=selected_file_id,
                user_instruction=request.message,
                catalog_summary=catalog_summary,
                conversation_history=conversation_context
            )

            if result.get("success"):
                response_text = result["message"]

                # Save assistant message
                assistant_message = ChatMessage(
                    session_id=session.session_id,
                    role="assistant",
                    content=response_text,
                    tool_calls={"sql_executed": result.get("sql_executed"), "rows_affected": result.get("rows_affected")}
                )
                db.add(assistant_message)
                db.commit()

                return ChatMessageResponse(
                    message=response_text,
                    data={"sql_executed": result.get("sql_executed"), "rows_affected": result.get("rows_affected")},
                    session_id=session.session_id
                )
            else:
                error_msg = result.get("error", "Unable to execute edit")
                return ChatMessageResponse(message=f"Error: {error_msg}", session_id=session.session_id)

        except Exception as e:
            logger.error(f"Error in data edit: {str(e)}", exc_info=True)
            return ChatMessageResponse(
                message=f"Error editing data: {str(e)}", session_id=session.session_id
            )

    # Check if statistics/insights request (do this BEFORE file selection to avoid SQL generation)
    # IMPORTANT: This must come before the data query flow to catch anomaly/stats requests
    if is_stats_request(request.message):
        logger.info(f"Detected statistics/insights request: '{request.message}'")

        # Get user files
        files = db.query(FileModel).filter(FileModel.user_id == request.user_id).all()
        if not files:
            return ChatMessageResponse(
                message="No data files found. Please upload a file first.", session_id=session.session_id
            )

        file_ids = [f.file_id for f in files]
        catalogs_query = db.query(Catalog).filter(Catalog.file_id.in_(file_ids)).all()
        catalog_list = [{"file_id": cat.file_id, "summary": cat.summary} for cat in catalogs_query]

        # Select relevant file (use db session if available)
        selected_file_id = select_relevant_file(request.message, catalog_list, db)
        logger.info(f"Selected file for stats: {selected_file_id}")

        if not selected_file_id:
            # If no file selected and multiple files exist, ask user to specify
            if len(catalog_list) > 1:
                file_list_items = []
                for i, cat in enumerate(catalog_list):
                    file_info = db.query(FileModel).filter(FileModel.file_id == cat["file_id"]).first()
                    filename = file_info.original_filename if file_info else cat["file_id"]
                    file_list_items.append(f"File {i+1}: {filename} (ID: {cat['file_id']})")
                file_list_text = "\n".join([f"- {item}" for item in file_list_items])
                response_text = f"I found {len(catalog_list)} files. Which file would you like to analyze for anomalies?\n\n{file_list_text}\n\nYou can specify a file by saying:\n- 'show anomalies in file 1'\n- 'find outliers in file 2'"
                assistant_message = ChatMessage(session_id=session.session_id, role="assistant", content=response_text)
                db.add(assistant_message)
                db.commit()
                return ChatMessageResponse(message=response_text, session_id=session.session_id)
            else:
                selected_file_id = catalog_list[0]["file_id"]

        # Run statistical analysis
        try:
            stats_result = statistics_analyzer.analyze_data(
                table_name=selected_file_id,
                user_question=request.message,
                filters=None  # TODO: Extract filters from conversation history
            )

            if stats_result.get("has_insights"):
                # Save assistant message
                assistant_message = ChatMessage(
                    session_id=session.session_id,
                    role="assistant",
                    content=stats_result["insights_text"]
                )
                db.add(assistant_message)
                db.commit()

                # Return insights visualization
                return ChatMessageResponse(
                    message=stats_result["insights_text"],
                    visualization=VisualizationConfig(
                        type="insights",
                        show_bar_chart=False,
                        input_data=[stats_result["statistics"]]
                    ),
                    session_id=session.session_id
                )
            else:
                error_msg = stats_result.get("error", "Unable to generate insights")
                logger.error(f"Stats analysis failed: {error_msg}")
                return ChatMessageResponse(message=f"Error analyzing data: {error_msg}", session_id=session.session_id)

        except Exception as e:
            logger.error(f"Error in statistical analysis: {str(e)}", exc_info=True)
            return ChatMessageResponse(
                message=f"Error analyzing data: {str(e)}", session_id=session.session_id
            )

    # Data query flow
    # Step 1: Get conversation history for context (reorder to chronological)
    conversation_messages_chronological = list(reversed(previous_messages))  # Reverse to get chronological order
    
    conversation_context = []
    for msg in conversation_messages_chronological:
        msg_dict = {"role": msg.role, "content": msg.content}
        # Include tool_calls (SQL queries) if available to help understand context
        if msg.tool_calls:
            msg_dict["tool_calls"] = msg.tool_calls
        conversation_context.append(msg_dict)

    # Step 2: Retrieve catalog
    files = db.query(FileModel).filter(FileModel.user_id == request.user_id).all()
    if not files:
        return ChatMessageResponse(
            message="No data files found. Please upload a file first.", session_id=session.session_id
        )

    file_ids = [f.file_id for f in files]
    catalogs_query = db.query(Catalog).filter(Catalog.file_id.in_(file_ids)).all()
    # Create a map of file_id to file info for easier lookup
    file_map = {f.file_id: f for f in files}
    catalog_list = [
        {
            "file_id": cat.file_id,
            "summary": cat.summary,
            "original_filename": file_map[cat.file_id].original_filename if cat.file_id in file_map else cat.file_id
        }
        for cat in catalogs_query
    ]

    if not catalog_list:
        return ChatMessageResponse(
            message="No data files found. Please upload a file first.", session_id=session.session_id
        )

    logger.info(f"Found {len(catalog_list)} catalogs for user {request.user_id}")

    # Step 3: Check if previous message was asking which file (file selection prompt)
    # This handles follow-up responses like "file2" or "file 2" after we asked which file
    is_follow_up_file_selection = False
    original_query_intent = None  # Store the original query intent
    last_user_msg_for_context = None  # Store the last user message for context
    if previous_messages and len(previous_messages) > 0:
        last_assistant_msg = None
        # previous_messages is already in reverse chronological order (most recent first)
        # Structure: [0] = most recent (user: "file 1"), [1] = assistant ("which file..."), [2] = user (original query)
        # Find the assistant's file selection prompt first
        for msg in previous_messages:
            if msg.role == "assistant":
                last_assistant_msg = msg.content
                break
        
        # Then find the user message that came BEFORE the assistant's file selection prompt
        # This is the original query (e.g., "tell me about the file", "show stats", "show me sources")
        found_file_prompt = False
        for msg in previous_messages:
            if msg.role == "assistant" and (
                "Which file would you like to know about" in msg.content or 
                "Which file would you like to query" in msg.content or
                "Which file would you like to analyze" in msg.content
            ):
                found_file_prompt = True
            elif msg.role == "user" and found_file_prompt:
                # This is the user message before the file selection prompt (the original query)
                last_user_msg_for_context = msg.content
                break
        
        # Check if last assistant message was asking which file (for metadata or data queries)
        if last_assistant_msg and (
            "Which file would you like to know about" in last_assistant_msg or 
            "Which file would you like to query" in last_assistant_msg or
            "Which file would you like to analyze" in last_assistant_msg or
            ("I found" in last_assistant_msg and "files" in last_assistant_msg and "Which file" in last_assistant_msg)
        ):
            is_follow_up_file_selection = True
            logger.info("Detected follow-up file selection after file list prompt")
            
            # Determine the original query intent from the user's message BEFORE the file selection prompt
            if last_user_msg_for_context:
                logger.info(f"Original query message: {last_user_msg_for_context}")
                
                # Check what type of query it was
                if is_file_metadata_question(last_user_msg_for_context):
                    original_query_intent = "metadata"
                elif is_stats_request(last_user_msg_for_context):
                    original_query_intent = "stats"
                else:
                    original_query_intent = "data_query"
                logger.info(f"Detected query intent: {original_query_intent}")
            else:
                # Fallback: check the current message for intent
                if is_file_metadata_question(request.message):
                    original_query_intent = "metadata"
                elif is_stats_request(request.message):
                    original_query_intent = "stats"
                else:
                    original_query_intent = "data_query"
    
    # Step 4: Select relevant file (considering conversation context)
    selected_file_id = select_relevant_file(request.message, catalog_list, db)
    logger.info(f"Selected file: {selected_file_id}")

    # Handle ambiguous file selection (multiple files, no specific file mentioned)
    if selected_file_id is None and len(catalog_list) > 1:
        # List all files with original filenames and ask user to specify
        file_list_items = []
        for i, cat in enumerate(catalog_list):
            filename = cat.get('original_filename', cat['file_id'])
            file_list_items.append(f"File {i+1}: {filename}")
        file_list_text = "\n".join([f"- {item}" for item in file_list_items])
        
        # Check if it's a metadata question or data query
        is_metadata_q = is_file_metadata_question(request.message)
        if is_metadata_q:
            response_text = f"I found {len(catalog_list)} files. Which file would you like to know about?\n\n{file_list_text}\n\nYou can specify a file by saying:\n- 'file 1', 'file2', 'file 3', etc.\n- 'tell me about file 1'\n- 'what is file 2 about'"
        else:
            response_text = f"I found {len(catalog_list)} files. Which file would you like to query?\n\n{file_list_text}\n\nPlease specify which file by saying:\n- 'file 1' or 'file2' or 'file 3', etc.\n- 'show last 5 rows from file 1'\n- 'file 2: show last 5 rows'\n- Or just 'file 1', 'file2', etc. and I'll use that file for your query."
        
        # Save assistant message
        assistant_message = ChatMessage(session_id=session.session_id, role="assistant", content=response_text)
        db.add(assistant_message)
        db.commit()
        
        return ChatMessageResponse(message=response_text, session_id=session.session_id)
    
    # If still no file selected after file selection prompt (shouldn't happen, but safety check)
    # Only default if we're not in a file selection flow
    if selected_file_id is None and not is_follow_up_file_selection:
        # This means we somehow didn't trigger the file selection prompt
        # Only default if there's exactly one file (edge case)
        if len(catalog_list) == 1:
            selected_file_id = catalog_list[0]["file_id"]
            logger.warning(f"No file selected but only one file exists, using: {selected_file_id}")
        else:
            # Multiple files but no selection - this shouldn't happen, but log it
            logger.error(f"No file selected with {len(catalog_list)} files. This should have been caught earlier.")
            return ChatMessageResponse(
                message="I'm having trouble determining which file to use. Please specify which file you'd like to query.",
                session_id=session.session_id
            )

    # Handle follow-up file selection
    # If user is responding to "which file" prompt, use the ORIGINAL query intent
    if is_follow_up_file_selection:
        if selected_file_id:
            # User selected a file after being asked "which file"
            # Use the original query intent, not the current message (which is just "file 1" or "file2")
            if original_query_intent == "metadata":
                # Query catalog table directly for file description
                catalog = db.query(Catalog).filter(Catalog.file_id == selected_file_id).first()
                if catalog:
                    file_info = db.query(FileModel).filter(FileModel.file_id == selected_file_id).first()
                    original_filename = file_info.original_filename if file_info else selected_file_id
                    
                    response_text = f"**File: {original_filename}**\n\n{catalog.summary}"
                    
                    # Save assistant message
                    assistant_message = ChatMessage(session_id=session.session_id, role="assistant", content=response_text)
                    db.add(assistant_message)
                    db.commit()
                    
                    return ChatMessageResponse(message=response_text, session_id=session.session_id)
                else:
                    return ChatMessageResponse(
                        message=f"Catalog not found for file {selected_file_id}", session_id=session.session_id
                    )
            elif original_query_intent == "stats":
                # It's a stats request - run statistical analysis
                logger.info(f"User selected file {selected_file_id} for statistical analysis")
                try:
                    # Use the original query message for stats analysis
                    stats_question = last_user_msg_for_context if last_user_msg_for_context else "analyze data"
                    stats_result = statistics_analyzer.analyze_data(
                        table_name=selected_file_id,
                        user_question=stats_question,
                        filters=None
                    )
                    
                    if stats_result.get("has_insights"):
                        # Save assistant message
                        assistant_message = ChatMessage(
                            session_id=session.session_id,
                            role="assistant",
                            content=stats_result["insights_text"]
                        )
                        db.add(assistant_message)
                        db.commit()
                        
                        # Return insights visualization
                        return ChatMessageResponse(
                            message=stats_result["insights_text"],
                            visualization=VisualizationConfig(
                                type="insights",
                                show_bar_chart=False,
                                input_data=[stats_result["statistics"]]
                            ),
                            session_id=session.session_id
                        )
                    else:
                        error_msg = stats_result.get("error", "Unable to generate insights")
                        logger.error(f"Stats analysis failed: {error_msg}")
                        return ChatMessageResponse(message=f"Error analyzing data: {error_msg}", session_id=session.session_id)
                except Exception as e:
                    logger.error(f"Error in statistical analysis: {str(e)}", exc_info=True)
                    return ChatMessageResponse(
                        message=f"Error analyzing data: {str(e)}", session_id=session.session_id
                    )
            else:
                # It's a data query - proceed with SQL generation using the selected file
                # Use the original query message, not just "file 1"
                original_query = last_user_msg_for_context if last_user_msg_for_context else request.message
                logger.info(f"User selected file {selected_file_id} for data query. Original query: {original_query}")
                # Update request.message to use the original query for SQL generation
                request.message = original_query
                # Continue to SQL generation below
        else:
            # User responded to "which file" prompt but we couldn't identify which file
            # Ask again with clearer instructions
            file_list_items = []
            for i, cat in enumerate(catalog_list):
                filename = cat.get('original_filename', cat['file_id'])
                file_list_items.append(f"File {i+1}: {filename}")
            file_list_text = "\n".join([f"- {item}" for item in file_list_items])
            
            response_text = f"I couldn't identify which file you meant. Please specify which file:\n\n{file_list_text}\n\nYou can say:\n- 'file 1' or 'file2' or 'file 3'\n- '1' or '2' or '3'\n- 'first file' or 'second file'"
            
            # Save assistant message
            assistant_message = ChatMessage(session_id=session.session_id, role="assistant", content=response_text)
            db.add(assistant_message)
            db.commit()
            
            return ChatMessageResponse(message=response_text, session_id=session.session_id)
    
    # Handle file metadata questions (when file is already selected and it's a metadata question)
    if is_file_metadata_question(request.message) and selected_file_id and not is_follow_up_file_selection:
        # Query catalog table directly for file description
        catalog = db.query(Catalog).filter(Catalog.file_id == selected_file_id).first()
        if catalog:
            file_info = db.query(FileModel).filter(FileModel.file_id == selected_file_id).first()
            original_filename = file_info.original_filename if file_info else selected_file_id
            
            response_text = f"**File: {original_filename}**\n\n{catalog.summary}"
            
            # Save assistant message
            assistant_message = ChatMessage(session_id=session.session_id, role="assistant", content=response_text)
            db.add(assistant_message)
            db.commit()
            
            return ChatMessageResponse(message=response_text, session_id=session.session_id)
        else:
            return ChatMessageResponse(
                message=f"Catalog not found for file {selected_file_id}", session_id=session.session_id
            )

    # Step 4: Generate SQL with conversation context
    logger.info(f"Generating SQL for question: {request.message}")
    try:
        sql_query = gemini_service.generate_sql_query(
            user_question=request.message,
            catalog_summaries=catalog_list,
            selected_file_id=selected_file_id,
            conversation_history=conversation_context,
        )
        logger.info(f"Generated SQL: {sql_query}")
    except Exception as e:
        logger.error(f"Error generating query: {str(e)}", exc_info=True)
        return ChatMessageResponse(message=f"Error generating query: {str(e)}", session_id=session.session_id)

    # Step 4: Execute SQL
    table_name = selected_file_id
    logger.info(f"Executing SQL on table: {table_name}")
    try:
        rows = sql_executor.execute_query(table_name, sql_query)
        logger.info(f"Query returned {len(rows)} rows")
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}", exc_info=True)
        return ChatMessageResponse(message=f"Error executing query: {str(e)}", session_id=session.session_id)

    # Step 5: Determine visualization
    columns = list(rows[0].keys()) if rows else []
    visualization = determine_visualization(rows, columns, user_message=request.message)
    logger.info(f"Visualization type: {visualization.type if visualization else 'None'}")

    # Step 6: Generate response message
    response_text = f"I found {len(rows)} result(s) for your query."
    logger.info(f"Preparing response with {len(rows)} rows")

    # Save assistant message with tool calls
    assistant_message = ChatMessage(
        session_id=session.session_id,
        role="assistant",
        content=response_text,
        tool_calls={"sql_query": sql_query, "file_id": selected_file_id, "row_count": len(rows)},
    )
    db.add(assistant_message)
    db.commit()

    # Prepare response
    response_data = {"rows": rows, "columns": columns, "sql_query": sql_query, "file_id": selected_file_id}

    logger.info(f"Sending response for session {session.session_id}")
    return ChatMessageResponse(
        message=response_text, data=response_data, visualization=visualization, session_id=session.session_id
    )


@router.post("/sql/execute")
async def execute_sql(table: str, sql: str, db: Session = Depends(get_db)):
    """Execute SQL query directly."""
    try:
        rows = sql_executor.execute_query(table, sql)
        columns = list(rows[0].keys()) if rows else []
        return {"rows": rows, "columns": columns}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions/{user_id}")
async def get_chat_sessions(user_id: str, db: Session = Depends(get_db)):
    """Get chat history for a user."""
    sessions = (
        db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(ChatSession.created_at.desc()).all()
    )

    result = []
    for session in sessions:
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session.session_id)
            .order_by(ChatMessage.created_at)
            .all()
        )

        result.append(
            {
                "session_id": session.session_id,
                "created_at": session.created_at,
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "tool_calls": msg.tool_calls,
                        "created_at": msg.created_at,
                    }
                    for msg in messages
                ],
            }
        )

    return result
