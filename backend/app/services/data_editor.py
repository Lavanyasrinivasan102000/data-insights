"""Data editing service."""
import pandas as pd
from typing import Dict, List, Any, Optional
from app.database.connection import engine
from app.services.gemini_service import gemini_service
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


class DataEditor:
    """Service for editing data in tables."""

    def update_row(
        self,
        table_name: str,
        row_id: int,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a single row by row ID."""
        try:
            # Build UPDATE statement
            set_clause = ", ".join([f'"{col}" = :{col}' for col in updates.keys()])
            query = f'UPDATE {table_name} SET {set_clause} WHERE rowid = :row_id'

            params = {**updates, "row_id": row_id}

            with engine.begin() as conn:
                result = conn.execute(text(query), params)

            return {
                "success": True,
                "rows_affected": result.rowcount,
                "message": f"Updated {result.rowcount} row(s)"
            }

        except Exception as e:
            logger.error(f"Error updating row: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def insert_row(
        self,
        table_name: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Insert a new row."""
        try:
            columns = ", ".join([f'"{col}"' for col in data.keys()])
            placeholders = ", ".join([f":{col}" for col in data.keys()])
            query = f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders})'

            with engine.begin() as conn:
                result = conn.execute(text(query), data)

            return {
                "success": True,
                "message": "Row inserted successfully"
            }

        except Exception as e:
            logger.error(f"Error inserting row: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def delete_row(
        self,
        table_name: str,
        row_id: int
    ) -> Dict[str, Any]:
        """Delete a row by row ID."""
        try:
            query = f'DELETE FROM {table_name} WHERE rowid = :row_id'

            with engine.begin() as conn:
                result = conn.execute(text(query), {"row_id": row_id})

            return {
                "success": True,
                "rows_affected": result.rowcount,
                "message": f"Deleted {result.rowcount} row(s)"
            }

        except Exception as e:
            logger.error(f"Error deleting row: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def ai_batch_edit(
        self,
        table_name: str,
        user_instruction: str,
        catalog_summary: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Use AI to generate and execute batch UPDATE statement."""
        logger.info(f"AI Batch Edit request: {user_instruction}")

        try:
            # Generate UPDATE SQL from natural language
            update_sql = self._generate_update_sql(
                user_instruction,
                table_name,
                catalog_summary,
                conversation_history
            )

            logger.info(f"Generated UPDATE SQL: {update_sql}")

            # Execute the UPDATE
            with engine.begin() as conn:
                result = conn.execute(text(update_sql))

            return {
                "success": True,
                "rows_affected": result.rowcount,
                "sql_executed": update_sql,
                "message": f"Updated {result.rowcount} row(s) based on: '{user_instruction}'"
            }

        except Exception as e:
            logger.error(f"Error in AI batch edit: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_update_sql(
        self,
        user_instruction: str,
        table_name: str,
        catalog_summary: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Use Gemini to generate UPDATE SQL from natural language."""
        # Build conversation context
        history_text = ""
        if conversation_history and len(conversation_history) > 1:
            history_text = "\n\nPrevious conversation (use this to understand context like 'last row', 'that data', etc.):\n"
            for msg in conversation_history[-10:]:  # Last 5 exchanges
                role = "User" if msg["role"] == "user" else "Assistant"
                history_text += f"{role}: {msg['content']}\n"
            history_text += "\nUse the conversation above to understand contextual references.\n"

        prompt = f"""You are a SQL expert. Generate an UPDATE statement for SQLite based on the user's instruction.

Table: {table_name}

Data Schema:
{catalog_summary}
{history_text}
User Instruction: "{user_instruction}"

CRITICAL REQUIREMENTS:
1. Generate ONLY an UPDATE statement - no SELECT, INSERT, DELETE, or DROP
2. Use EXACT column names from schema (case-sensitive column names in quotes!)
   - ALWAYS quote column names with double quotes: "Column Name"
   - If column has spaces: "Account Id", "Lead Owner", "Deal Stage" (MUST use quotes!)
   - NEVER use underscores for spaces: "Account Id" NOT Account_Id
   - Example: "Lead Owner" NOT Lead_Owner or LeadOwner
3. Use proper SQL syntax for SQLite
4. Be precise with WHERE clause to match user's intent
5. Use mathematical operations correctly (e.g., "RetailDollars" * 1.10 for 10% increase)
6. For string comparisons, use case-insensitive matching: UPPER("Column Name") = UPPER('value') or "Column Name" COLLATE NOCASE = 'value'
7. For "last row" or "last data", identify the row using a subquery:
   - Match the specific value mentioned (e.g., name) case-insensitively
   - Use rowid in subquery to target the specific row: WHERE rowid = (SELECT rowid FROM {table_name} WHERE [conditions] ORDER BY rowid DESC LIMIT 1)
   - If date-based ordering is relevant, use: ORDER BY "Date" ASC, rowid DESC LIMIT 1 (to get the oldest date, which appears last when ordered DESC)
   - Or simply: ORDER BY rowid DESC LIMIT 1 (to get the row with highest rowid, typically the most recent)
   - Always quote column names in ORDER BY: ORDER BY "Date" NOT ORDER BY Date
8. When user refers to "last row", "last data", "that row" - look at conversation history to understand which row they're referring to from the previous query results
9. For matching specific values mentioned (like names), use COLLATE NOCASE for case-insensitive matching
10. Return ONLY the SQL - no explanations, markdown, or code blocks

Examples:
- "increase Nike sales by 10%":
  UPDATE {table_name} SET "RetailDollars" = "RetailDollars" * 1.10 WHERE UPPER("Brand") = UPPER('NIKE')

- "set all units to 0 for Adidas in December":
  UPDATE {table_name} SET "Units" = 0 WHERE UPPER("Brand") = UPPER('ADIDAS') AND "ME_PERIOD" LIKE '%DEC%'

- "change the last row's Lead Owner from Becky Arellano to Joyce Byres":
  UPDATE {table_name} SET "Lead Owner" = 'Joyce Byres' WHERE rowid = (SELECT rowid FROM {table_name} WHERE "Lead Owner" COLLATE NOCASE = 'Becky Arellano' ORDER BY rowid DESC LIMIT 1)

- "update lead owner from Becky arellano to Joyce byres for the last data":
  UPDATE {table_name} SET "Lead Owner" = 'Joyce Byres' WHERE rowid = (SELECT rowid FROM {table_name} WHERE "Lead Owner" COLLATE NOCASE = 'Becky Arellano' ORDER BY rowid DESC LIMIT 1)

- "change the last data lead owner from Becky arellano to Joyce byres":
  UPDATE {table_name} SET "Lead Owner" = 'Joyce Byres' WHERE rowid = (SELECT rowid FROM {table_name} WHERE "Lead Owner" COLLATE NOCASE = 'Becky Arellano' ORDER BY rowid DESC LIMIT 1)

- "change name from John to Jane":
  UPDATE {table_name} SET "First Name" = 'Jane' WHERE "First Name" COLLATE NOCASE = 'John'

Generate the UPDATE statement:"""

        try:
            response = gemini_service.model.generate_content(prompt)
            sql = response.text.strip()

            # Clean markdown if present
            if sql.startswith("```sql"):
                sql = sql[6:]
            if sql.startswith("```"):
                sql = sql[3:]
            if sql.endswith("```"):
                sql = sql[:-3]

            sql = sql.strip()

            # Validate it's an UPDATE statement
            if not sql.upper().startswith("UPDATE"):
                raise ValueError("Generated SQL is not an UPDATE statement")

            return sql

        except Exception as e:
            logger.error(f"Error generating UPDATE SQL: {str(e)}")
            raise ValueError(f"Unable to generate UPDATE SQL: {str(e)}")


# Create singleton instance
data_editor = DataEditor()
