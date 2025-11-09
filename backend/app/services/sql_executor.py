"""SQL execution service."""
import pandas as pd
import sqlite3
from typing import Dict, List, Any, Optional
from app.config import settings
from app.database.connection import engine
import re
import logging

logger = logging.getLogger(__name__)


class SQLExecutor:
    """Service for executing SQL queries."""
    
    def __init__(self):
        """Initialize SQL executor."""
        self.connection = engine.raw_connection()
    
    def create_table_from_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str
    ) -> None:
        """Create SQL table from DataFrame."""
        # Validate table name (security)
        if not self._validate_table_name(table_name):
            raise ValueError(f"Invalid table name: {table_name}")
        
        # Create table
        df.to_sql(
            table_name,
            con=engine,
            if_exists='replace',
            index=False
        )
    
    def execute_query(
        self,
        table_name: str,
        sql_query: str
    ) -> List[Dict[str, Any]]:
        """Execute SQL query and return results."""
        # Validate table name
        if not self._validate_table_name(table_name):
            raise ValueError(f"Invalid table name: {table_name}")

        # Normalize schema prefixes that Gemini might add (e.g., base.table_name)
        normalized_query = self._normalize_table_reference(sql_query, table_name)
        if normalized_query != sql_query:
            logger.info(f"Normalized SQL query by removing schema prefixes from table reference.")
            logger.info(f"Original: {sql_query}")
            logger.info(f"Normalized: {normalized_query}")
        sql_query = normalized_query
        
        # Validate SQL query (security)
        validation_result = self._validate_sql_query(sql_query, table_name)
        if not validation_result:
            error_msg = f"Invalid or unsafe SQL query. Table: {table_name}, Query: {sql_query[:200]}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Execute query
            logger.info(f"Executing SQL: {sql_query}")
            df = pd.read_sql_query(sql_query, con=engine)
            
            # Convert to list of dicts
            return df.replace({pd.NA: None, pd.NaT: None}).to_dict(orient='records')
        except Exception as e:
            error_msg = f"Error executing query: {str(e)}"
            logger.error(f"{error_msg}. Query: {sql_query}")
            raise ValueError(error_msg)
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get schema information for a table."""
        if not self._validate_table_name(table_name):
            raise ValueError(f"Invalid table name: {table_name}")
        
        try:
            df = pd.read_sql_query(
                f"SELECT * FROM {table_name} LIMIT 0",
                con=engine
            )
            return {
                "columns": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
        except Exception as e:
            raise ValueError(f"Error getting schema: {str(e)}")
    
    def _validate_table_name(self, table_name: str) -> bool:
        """Validate table name to prevent SQL injection."""
        # Only allow alphanumeric and underscore
        pattern = r'^[a-zA-Z0-9_]+$'
        return bool(re.match(pattern, table_name))
    
    def _validate_sql_query(self, sql_query: str, expected_table: str) -> bool:
        """Validate SQL query for security."""
        sql_lower = sql_query.lower().strip()
        expected_table_lower = expected_table.lower()
        logger.info(f"Validating SQL query: {sql_query}")
        logger.info(f"Expected table: {expected_table}")

        # Only allow SELECT statements
        if not sql_lower.startswith('select'):
            logger.warning(f"Query rejected: doesn't start with SELECT. Query: {sql_query[:100]}")
            return False

        # Block dangerous operations - check for whole words only
        dangerous_patterns = [
            r'\bdrop\b', r'\bdelete\b', r'\btruncate\b', r'\balter\b',
            r'\binsert\b', r'\bupdate\b', r'\bgrant\b', r'\brevoke\b',
            r'\bexec\b', r'\bexecute\b'
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, sql_lower):
                keyword = pattern.strip(r'\\b')
                logger.warning(f"Query rejected: contains dangerous keyword '{keyword}'. Query: {sql_query[:100]}")
                return False

        # Must contain expected table name (check multiple formats)
        # Check if table name appears in the query (with various quote styles)
        table_found = False
        
        # Check 1: Direct match (case-insensitive)
        if expected_table_lower in sql_lower:
            table_found = True
            logger.info(f"Table name found (direct match): {expected_table_lower}")
        
        # Check 2: With double quotes
        if f'"{expected_table}"' in sql_query:
            table_found = True
            logger.info(f"Table name found (double quotes): \"{expected_table}\"")
        
        # Check 3: With single quotes (unlikely but possible)
        if f"'{expected_table}'" in sql_query:
            table_found = True
            logger.info(f"Table name found (single quotes): '{expected_table}'")
        
        # Check 4: With backticks
        if f'`{expected_table}`' in sql_query:
            table_found = True
            logger.info(f"Table name found (backticks): `{expected_table}`")
        
        # Check 5: After FROM/JOIN keywords with regex
        from_patterns = [
            rf'\bfrom\s+["\'`]?{re.escape(expected_table_lower)}["\'`]?',
            rf'\bjoin\s+["\'`]?{re.escape(expected_table_lower)}["\'`]?',
            rf'\bfrom\s+\w+\s+as\s+["\'`]?{re.escape(expected_table_lower)}["\'`]?',
        ]
        
        for pattern in from_patterns:
            if re.search(pattern, sql_lower, re.IGNORECASE):
                table_found = True
                logger.info(f"Table name found (pattern match): {pattern}")
                break
        
        if not table_found:
            # Final check: Look for table name parts (for very long table names)
            # This is a fallback for edge cases
            table_parts = expected_table_lower.split('_')
            if len(table_parts) >= 4:  # For table names with 4+ parts
                # Check if the unique identifier parts are present
                # Usually the last few parts are unique (e.g., 'input_file_4_csv')
                unique_parts = table_parts[-4:] if len(table_parts) >= 4 else table_parts
                # Require at least 3 out of 4 parts to match (for flexibility)
                matches = sum(1 for part in unique_parts if part in sql_lower)
                if matches >= 3:
                    table_found = True
                    logger.info(f"Table name found (partial match): {matches}/{len(unique_parts)} parts matched")
        
        if not table_found:
            logger.error(f"Query rejected: doesn't contain expected table '{expected_table}'")
            logger.error(f"SQL query: {sql_query}")
            logger.error(f"Looking for table: {expected_table_lower}")
            logger.error(f"SQL (lowercase): {sql_lower[:500]}")
            return False

        logger.info("SQL query validation passed")
        return True

    def _normalize_table_reference(self, sql_query: str, expected_table: str) -> str:
        """Remove schema prefixes (e.g., base.table) to match actual SQLite table names."""
        pattern = rf'(?i)\b(?:base|main)\.{re.escape(expected_table)}\b'
        return re.sub(pattern, expected_table, sql_query)


# Create singleton instance
sql_executor = SQLExecutor()
