"""Gemini API service."""

import google.generativeai as genai
from typing import Dict, List, Any, Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for interacting with Gemini API."""

    def __init__(self):
        """Initialize Gemini client."""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-flash-lite-latest")

    def generate_catalog(self, schema: Dict[str, Any], sample_rows: List[Dict[str, Any]], row_count: int) -> str:
        """Generate catalog summary using Gemini."""
        prompt = self._prepare_catalog_prompt(schema, sample_rows, row_count)

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise ValueError(f"Error generating catalog: {str(e)}")

    def generate_sql_query(
        self,
        user_question: str,
        catalog_summaries: List[Dict[str, str]],
        selected_file_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Generate SQL query from user question and catalog summaries."""
        # Store catalog_summaries and table_name for potential auto-fix
        self._current_catalog_summaries = catalog_summaries
        self._current_table_name = selected_file_id if selected_file_id else None
        
        logger.info("=" * 80)
        logger.info(f"GENERATING SQL QUERY")
        logger.info(f"User Question: '{user_question}'")
        logger.info(f"Selected File ID: {selected_file_id}")
        logger.info(f"Number of catalogs: {len(catalog_summaries)}")
        if conversation_history:
            logger.info(f"Conversation history length: {len(conversation_history)}")

        prompt = self._prepare_sql_prompt(user_question, catalog_summaries, selected_file_id, conversation_history)
        logger.info(f"Full Prompt to Gemini:\n{prompt}")
        logger.info("-" * 80)

        try:
            logger.info("Calling Gemini API...")
            response = self.model.generate_content(prompt)
            sql = response.text.strip()
            logger.info(f"Raw Gemini Response:\n{sql}")

            # Remove markdown code blocks if present
            import re
            # Remove ```sql or ``` blocks
            sql = re.sub(r'^```sql\s*', '', sql, flags=re.IGNORECASE | re.MULTILINE)
            sql = re.sub(r'^```\s*', '', sql, flags=re.MULTILINE)
            sql = re.sub(r'```\s*$', '', sql, flags=re.MULTILINE)
            
            # Extract SQL query if there's text before/after
            # Look for SELECT statement (case-insensitive)
            select_match = re.search(r'select\s+', sql, re.IGNORECASE | re.MULTILINE)
            if select_match:
                # Start from the SELECT statement
                sql = sql[select_match.start():]
                # Find the end (remove any trailing explanation text)
                # SQL should end with semicolon, or at end of line, or before common explanation phrases
                # More aggressive cleaning - stop at any line that doesn't look like SQL
                sql_lines = sql.split('\n')
                cleaned_lines = []
                sql_keywords = {'select', 'from', 'where', 'group', 'order', 'by', 'having', 'limit', 'distinct', 'count', 'sum', 'avg', 'max', 'min', 'as', 'and', 'or', 'not', 'in', 'like', 'between', 'case', 'when', 'then', 'else', 'end'}
                
                for line in sql_lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Stop if we hit explanation text (common patterns)
                    if re.match(r'^(note|explanation|this query|the query|result|returns|the user|based on|applying|transforming|given|wait|however|since|but|also|however|when|if|since|given|applying|transforming|selecting|using|i will|i should|the system|the instruction)', line, re.IGNORECASE):
                        break
                    
                    # Stop if line contains backticks that aren't part of SQL (likely markdown or explanation)
                    if line.count('`') > 2:  # SQL shouldn't have many backticks
                        # Check if it's actually SQL with backticks vs explanation text
                        if not any(keyword in line.lower() for keyword in sql_keywords):
                            break
                    
                    # Stop if line looks like explanation (contains words like "query", "file", "user" in explanatory context)
                    if re.search(r'\b(the|this|that|these|those)\s+(query|file|user|statement|sql)', line, re.IGNORECASE):
                        # But allow if it's part of SQL (like in a string literal)
                        if not (line.count("'") >= 2 or line.count('"') >= 2):
                            break
                    
                    cleaned_lines.append(line)
                    # If line ends with semicolon, that's likely the end
                    if line.rstrip().endswith(';'):
                        break
                
                sql = ' '.join(cleaned_lines)
                
            # Additional aggressive cleaning: find the complete SQL statement
            # SQL statements typically end with a semicolon or at the end of a logical block
            # Try to extract just the first complete SELECT statement
            
            # Method 1: Find SELECT ... FROM ... (optional WHERE/GROUP BY/ORDER BY) ... (semicolon or end)
            # This pattern matches a complete SQL SELECT statement
            # Updated to handle long table names - use non-greedy matching but ensure we capture the full table name
            # Pattern: SELECT ... FROM (quoted or unquoted table name) ... ORDER BY ... LIMIT ...
            complete_sql_pattern = r'(SELECT\s+(?:DISTINCT\s+)?.*?FROM\s+(?:"[^"]+"|[\w_]+).*?(?:\s+WHERE\s+.*?)?(?:\s+GROUP\s+BY\s+.*?)?(?:\s+ORDER\s+BY\s+.*?)?(?:\s+HAVING\s+.*?)?(?:\s+LIMIT\s+\d+)?)'
            match = re.search(complete_sql_pattern, sql, re.IGNORECASE | re.DOTALL)
            if match:
                extracted_sql = match.group(1).strip()
                # Verify the extracted SQL is reasonable (not cut off mid-table-name)
                # Check if it ends with a number (LIMIT) or a keyword
                if re.search(r'(LIMIT\s+\d+|ORDER\s+BY\s+.*|GROUP\s+BY\s+.*|WHERE\s+.*)$', extracted_sql, re.IGNORECASE):
                    sql = extracted_sql
                    logger.info(f"Extracted complete SQL statement using pattern matching: {sql[:150]}...")
                else:
                    # SQL might be incomplete, try a different approach
                    logger.warning(f"Extracted SQL might be incomplete, using as-is: {extracted_sql[:150]}...")
                    sql = extracted_sql
            else:
                # Method 2: Try to find SQL up to the first explanation phrase
                # Look for common SQL ending patterns followed by explanation
                explanation_markers = [
                    r'\.\s+(?:The|This|That|These|Those|Note|Explanation|Wait|However|Since|But|Also|Given|Applying|Transforming|Selecting|Using|I will|I should|The system|The instruction)',
                    r';\s+(?:The|This|That|Note|Explanation)',
                    r'\s+`\s*[^`]*(?:The|This|That|Note|Explanation)',
                ]
                for marker in explanation_markers:
                    parts = re.split(marker, sql, maxsplit=1, flags=re.IGNORECASE)
                    if len(parts) > 1:
                        sql = parts[0].strip()
                        logger.info(f"Trimmed SQL at explanation marker: {marker}")
                        break
                
                # Method 3: Remove anything after backticks that aren't part of SQL
                # SQL with backticks for identifiers should be minimal
                if '`' in sql:
                    # Count backticks - if odd or excessive, likely markdown/explanation
                    backtick_count = sql.count('`')
                    if backtick_count > 4:  # More than 2 pairs suggests markdown
                        # Find the last reasonable SQL keyword before excessive backticks
                        sql_keyword_positions = []
                        for keyword in ['FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'LIMIT']:
                            pos = sql.upper().rfind(keyword)
                            if pos != -1:
                                sql_keyword_positions.append((pos, keyword))
                        if sql_keyword_positions:
                            last_keyword_pos = max(sql_keyword_positions, key=lambda x: x[0])
                            # Take SQL up to 500 characters after the last keyword (increased for long table names)
                            # Look for common SQL ending patterns (LIMIT, ORDER BY, etc.) instead of arbitrary cutoff
                            remaining_sql = sql[last_keyword_pos[0]:]
                            # Find where SQL logically ends (semicolon, newline with non-SQL text, or end of string)
                            # Look for LIMIT, ORDER BY, or end of statement
                            limit_match = re.search(r'(LIMIT\s+\d+)', remaining_sql, re.IGNORECASE)
                            if limit_match:
                                end_pos = last_keyword_pos[0] + limit_match.end()
                                sql = sql[:end_pos].strip()
                                logger.info(f"Trimmed SQL after LIMIT clause")
                            else:
                                # Take up to 500 chars after last keyword (enough for long table names + ORDER BY + LIMIT)
                                end_pos = min(last_keyword_pos[0] + 500, len(sql))
                                sql = sql[:end_pos].strip()
                                logger.info(f"Trimmed SQL after last keyword: {last_keyword_pos[1]}")
            
            # Remove semicolon at the end if present
            cleaned_sql = sql.strip().rstrip(';').strip()
            
            # Final validation: must start with SELECT and be reasonable length
            if not cleaned_sql.upper().startswith('SELECT'):
                logger.error(f"Cleaned SQL doesn't start with SELECT: {cleaned_sql[:200]}")
                # Try one more aggressive extraction: find SELECT and take everything up to first explanation
                # Use a more complete pattern that includes ORDER BY and LIMIT
                select_match = re.search(r'(SELECT\s+.*?(?:FROM\s+.*?)(?:\s+WHERE\s+.*?)?(?:\s+GROUP\s+BY\s+.*?)?(?:\s+ORDER\s+BY\s+.*?)?(?:\s+LIMIT\s+\d+)?)', cleaned_sql, re.IGNORECASE | re.DOTALL)
                if select_match:
                    cleaned_sql = select_match.group(1).strip().rstrip(';').strip()
                    logger.info(f"Extracted SQL using aggressive pattern: {cleaned_sql[:150]}...")
                else:
                    # Last resort: take first line that starts with SELECT and continue until we have complete query
                    for line in cleaned_sql.split('\n'):
                        line = line.strip()
                        if line.upper().startswith('SELECT'):
                            # Take this line and join with next lines until we have a complete SQL statement
                            lines = [line]
                            # Check if we already have FROM clause in the first line
                            has_from = 'FROM' in line.upper()
                            has_limit = 'LIMIT' in line.upper()
                            has_order_by = 'ORDER BY' in line.upper()
                            
                            # Continue reading lines until we have a complete query
                            for next_line in cleaned_sql.split('\n')[cleaned_sql.split('\n').index(line.strip()) + 1:]:
                                next_line = next_line.strip()
                                if not next_line:
                                    continue
                                
                                # Stop if we hit explanation text
                                if re.match(r'^(note|explanation|this query|the query|result|returns|the user|based on|applying|transforming|given|wait|however|since|but|also)', next_line, re.IGNORECASE):
                                    break
                                
                                # Add SQL keywords
                                next_upper = next_line.upper()
                                if any(keyword in next_upper for keyword in ['FROM', 'WHERE', 'GROUP', 'ORDER', 'LIMIT', 'HAVING', 'ASC', 'DESC']):
                                    lines.append(next_line)
                                    if 'FROM' in next_upper:
                                        has_from = True
                                    if 'LIMIT' in next_upper:
                                        has_limit = True
                                    if 'ORDER BY' in next_upper:
                                        has_order_by = True
                                # If we have FROM and this line doesn't look like SQL, stop
                                elif has_from and not any(char in next_line for char in ['"', "'", '(', ')', ',', '*', '=']):
                                    break
                            
                            cleaned_sql = ' '.join(lines).strip().rstrip(';').strip()
                            logger.info(f"Extracted SQL from SELECT line: {cleaned_sql[:150]}...")
                            break
                    
                    if not cleaned_sql.upper().startswith('SELECT'):
                        logger.error(f"Failed to extract SQL. Original response (first 1000 chars): {response.text[:1000]}")
                        raise ValueError(f"Could not extract valid SQL query from response. First 500 chars: {response.text[:500]}")
            
            # Get table_name from selected_file_id parameter (define early for use in validation)
            table_name = selected_file_id
            
            # Ensure the query contains the full table name (not truncated)
            # Check if table name appears to be truncated (e.g., just "c" instead of full name)
            if 'FROM' in cleaned_sql.upper() and table_name:
                # Check if the full table name is in the query
                table_name_quoted = f'"{table_name}"'
                table_name_unquoted = table_name
                
                # Check if table name is missing or truncated
                if table_name not in cleaned_sql and table_name_quoted not in cleaned_sql:
                    logger.warning(f"Table name '{table_name}' not found in cleaned SQL: {cleaned_sql[:200]}")
                    # Try to find where FROM clause is and replace the table name
                    # Match FROM followed by optional quotes and any identifier (including underscores)
                    from_pattern = r'FROM\s+(["\']?)([a-zA-Z0-9_]+)(["\']?)'
                    from_match = re.search(from_pattern, cleaned_sql, re.IGNORECASE)
                    
                    if from_match:
                        current_table_ref = from_match.group(2)
                        # If current table ref is much shorter than expected, replace it
                        if len(current_table_ref) < len(table_name) / 2:
                            logger.warning(f"Table name appears truncated: '{current_table_ref}' (expected: '{table_name}')")
                            # Replace with full table name (use quotes for long names)
                            if len(table_name) > 30 or '_' in table_name:
                                replacement = f'FROM "{table_name}"'
                            else:
                                replacement = f'FROM {table_name}'
                            cleaned_sql = re.sub(from_pattern, replacement, cleaned_sql, count=1, flags=re.IGNORECASE)
                            logger.info(f"Fixed truncated table name in SQL query: {cleaned_sql[:200]}")
                    else:
                        # If we can't find FROM pattern, try to add it after SELECT
                        logger.error(f"Could not find FROM clause pattern in SQL. Attempting to fix...")
                        # Try to find and replace any partial table name
                        # Get table_name from selected_file_id for this check
                        table_name_for_check = selected_file_id
                        if table_name_for_check and len(table_name_for_check) > 10 and table_name_for_check[:10] in response.text:  # Check if table name start is in response
                            # Find the table name in original response and use it
                            table_name_match = re.search(re.escape(table_name_for_check), response.text, re.IGNORECASE)
                            if table_name_match:
                                # The table name exists in response, so the issue is in extraction
                                # Try to rebuild the FROM clause
                                select_match = re.search(r'SELECT\s+.*?FROM\s+', cleaned_sql, re.IGNORECASE)
                                if select_match:
                                    # Replace everything after FROM with the correct table name
                                    cleaned_sql = re.sub(
                                        r'(FROM\s+)([^\s;]+)',
                                        f'\\1"{table_name_for_check}"',
                                        cleaned_sql,
                                        count=1,
                                        flags=re.IGNORECASE
                                    )
                                    logger.info(f"Rebuilt FROM clause with full table name: {cleaned_sql[:200]}")
                else:
                    # Table name is present, but might need quotes
                    table_name_for_quotes = selected_file_id
                    if table_name_for_quotes and table_name_for_quotes in cleaned_sql and f'"{table_name_for_quotes}"' not in cleaned_sql:
                        # Table name is there but not quoted - quote it if it's long or has underscores
                        if len(table_name_for_quotes) > 30 or '_' in table_name_for_quotes:
                            cleaned_sql = cleaned_sql.replace(f'FROM {table_name_for_quotes}', f'FROM "{table_name_for_quotes}"')
                            cleaned_sql = cleaned_sql.replace(f'FROM {table_name_for_quotes.upper()}', f'FROM "{table_name_for_quotes}"')
                            cleaned_sql = cleaned_sql.replace(f'FROM {table_name_for_quotes.lower()}', f'FROM "{table_name_for_quotes}"')
                            logger.info(f"Added quotes to table name in SQL query")
            
            # Fix incomplete GROUP BY clauses (e.g., "GROUP BY" without column name)
            # Check if GROUP BY is incomplete (ends with GROUP BY or GROUP BY with no column)
            if re.search(r'\bGROUP\s+BY\s*$', cleaned_sql, re.IGNORECASE):
                # Remove incomplete GROUP BY clause
                cleaned_sql = re.sub(r'\s+GROUP\s+BY\s*$', '', cleaned_sql, flags=re.IGNORECASE).strip()
                logger.info("Removed incomplete GROUP BY clause")
            # Also check for GROUP BY with just whitespace
            if re.search(r'\bGROUP\s+BY\s+\s*$', cleaned_sql, re.IGNORECASE):
                cleaned_sql = re.sub(r'\s+GROUP\s+BY\s+\s*$', '', cleaned_sql, flags=re.IGNORECASE).strip()
                logger.info("Removed incomplete GROUP BY clause (whitespace only)")
            # Check for GROUP BY followed by ORDER BY without column (GROUP BY ORDER BY)
            if re.search(r'\bGROUP\s+BY\s+ORDER\s+BY', cleaned_sql, re.IGNORECASE):
                # Remove the incomplete GROUP BY, keep ORDER BY if it has a column
                cleaned_sql = re.sub(r'\s+GROUP\s+BY\s+(?=ORDER\s+BY)', '', cleaned_sql, flags=re.IGNORECASE).strip()
                logger.info("Removed incomplete GROUP BY before ORDER BY")
            
            # Fix incomplete ORDER BY clauses (e.g., "ORDER BY" without column name)
            # Check if ORDER BY is incomplete (ends with ORDER BY or ORDER BY with no column)
            if re.search(r'\bORDER\s+BY\s*$', cleaned_sql, re.IGNORECASE):
                # Remove incomplete ORDER BY clause
                cleaned_sql = re.sub(r'\s+ORDER\s+BY\s*$', '', cleaned_sql, flags=re.IGNORECASE).strip()
                logger.info("Removed incomplete ORDER BY clause")
            # Also check for ORDER BY with just whitespace or common incomplete patterns
            if re.search(r'\bORDER\s+BY\s+\s*$', cleaned_sql, re.IGNORECASE):
                cleaned_sql = re.sub(r'\s+ORDER\s+BY\s+\s*$', '', cleaned_sql, flags=re.IGNORECASE).strip()
                logger.info("Removed incomplete ORDER BY clause (whitespace only)")
            
            # Fix incomplete WHERE clauses (e.g., "WHERE" without condition)
            # Check if WHERE is incomplete (ends with WHERE or WHERE with no condition)
            if re.search(r'\bWHERE\s*$', cleaned_sql, re.IGNORECASE):
                # Remove incomplete WHERE clause
                cleaned_sql = re.sub(r'\s+WHERE\s*$', '', cleaned_sql, flags=re.IGNORECASE).strip()
                logger.warning("Removed incomplete WHERE clause (no condition provided)")
            # Also check for WHERE followed by just whitespace before end of query
            if re.search(r'\bWHERE\s+\s*$', cleaned_sql, re.IGNORECASE):
                cleaned_sql = re.sub(r'\s+WHERE\s+\s*$', '', cleaned_sql, flags=re.IGNORECASE).strip()
                logger.warning("Removed incomplete WHERE clause (whitespace only)")
            # Check for WHERE followed by ORDER BY or GROUP BY without a condition (WHERE ORDER BY, WHERE GROUP BY)
            if re.search(r'\bWHERE\s+(ORDER\s+BY|GROUP\s+BY)', cleaned_sql, re.IGNORECASE):
                # Remove the incomplete WHERE clause
                cleaned_sql = re.sub(r'\s+WHERE\s+(?=ORDER\s+BY|GROUP\s+BY)', '', cleaned_sql, flags=re.IGNORECASE).strip()
                logger.warning("Removed incomplete WHERE clause before ORDER BY/GROUP BY")
            
            # Final sanity check: SQL should be reasonable length (not thousands of characters)
            if len(cleaned_sql) > 2000:
                logger.warning(f"SQL is very long ({len(cleaned_sql)} chars), may contain explanation text")
                # Try to find where SQL logically ends
                # Look for common SQL ending patterns
                ending_patterns = [
                    r'(.*?\s+ORDER\s+BY\s+\w+[^;]*)',  # ORDER BY with column
                    r'(.*?\s+GROUP\s+BY\s+[^;]+\s+ORDER\s+BY\s+\w+[^;]*)',  # GROUP BY + ORDER BY
                    r'(.*?\s+LIMIT\s+\d+)',  # LIMIT clause
                    r'(.*?\s+WHERE\s+[^;]+)',  # WHERE clause (if no ORDER BY/LIMIT)
                ]
                for pattern in ending_patterns:
                    match = re.search(pattern, cleaned_sql, re.IGNORECASE | re.DOTALL)
                    if match:
                        cleaned_sql = match.group(1).strip()
                        logger.info(f"Trimmed long SQL using ending pattern")
                        break
                
                # Final check: remove incomplete clauses if still present after trimming
                if re.search(r'\bGROUP\s+BY\s*$', cleaned_sql, re.IGNORECASE):
                    cleaned_sql = re.sub(r'\s+GROUP\s+BY\s*$', '', cleaned_sql, flags=re.IGNORECASE).strip()
                    logger.info("Removed incomplete GROUP BY clause after trimming")
                if re.search(r'\bORDER\s+BY\s*$', cleaned_sql, re.IGNORECASE):
                    cleaned_sql = re.sub(r'\s+ORDER\s+BY\s*$', '', cleaned_sql, flags=re.IGNORECASE).strip()
                    logger.info("Removed incomplete ORDER BY clause after trimming")
            
            # Store table_name for potential auto-fix
            table_name = selected_file_id if selected_file_id else None
            
            # Final validation: Ensure table name is correct and not truncated
            # table_name is already set above, just validate it here
            if not table_name:
                logger.warning("No table_name/selected_file_id provided for SQL validation")
            elif 'FROM' in cleaned_sql.upper():
                # Check if table name is present and complete
                table_name_found = False
                # Check various formats
                if table_name in cleaned_sql or f'"{table_name}"' in cleaned_sql:
                    table_name_found = True
                
                if not table_name_found:
                    # Table name is missing - try to fix it
                    logger.error(f"Table name '{table_name}' not found in final SQL: {cleaned_sql}")
                    # Find FROM clause and replace table name
                    from_pattern = r'(FROM\s+)([^\s;,"\'`]+)'
                    if re.search(from_pattern, cleaned_sql, re.IGNORECASE):
                        # Replace with correct table name (quote it for long names)
                        if len(table_name) > 30:
                            cleaned_sql = re.sub(from_pattern, f'\\1"{table_name}"', cleaned_sql, count=1, flags=re.IGNORECASE)
                        else:
                            cleaned_sql = re.sub(from_pattern, f'\\1{table_name}', cleaned_sql, count=1, flags=re.IGNORECASE)
                        logger.info(f"Fixed missing table name: {cleaned_sql[:200]}")
                    else:
                        # FROM clause is malformed - try to rebuild
                        logger.error(f"FROM clause is malformed. Original response: {response.text[:500]}")
                        # As last resort, if we have SELECT but broken FROM, rebuild it
                        if cleaned_sql.upper().startswith('SELECT') and 'FROM' not in cleaned_sql.upper():
                            # Add FROM clause
                            cleaned_sql = f'{cleaned_sql} FROM "{table_name}"'
                            logger.info(f"Added missing FROM clause: {cleaned_sql[:200]}")
                else:
                    # Table name found, but verify it's not truncated
                    # Extract current table name from SQL - handle both quoted and unquoted
                    from_patterns = [
                        r'FROM\s+"([^"]+)"',  # Quoted table name
                        r'FROM\s+\'([^\']+)\'',  # Single-quoted table name
                        r'FROM\s+([a-zA-Z0-9_]+)',  # Unquoted table name (alphanumeric + underscore)
                    ]
                    
                    current_table = None
                    for pattern in from_patterns:
                        from_match = re.search(pattern, cleaned_sql, re.IGNORECASE)
                        if from_match:
                            current_table = from_match.group(1)
                            break
                    
                    if current_table:
                        # If current table is much shorter than expected, it's truncated
                        # Also check if it's just a single character (like "c")
                        if (len(current_table) < len(table_name) * 0.5) or (len(current_table) < 5 and len(table_name) > 20):
                            logger.warning(f"Table name appears truncated: '{current_table}' (expected: '{table_name}')")
                            # Replace with full table name (always quote long names)
                            if len(table_name) > 30 or '_' in table_name:
                                # Replace any table name after FROM with quoted full name
                                cleaned_sql = re.sub(
                                    r'FROM\s+(?:"[^"]+"|\'[^\']+\'|[a-zA-Z0-9_]+)',
                                    f'FROM "{table_name}"',
                                    cleaned_sql,
                                    count=1,
                                    flags=re.IGNORECASE
                                )
                            else:
                                cleaned_sql = re.sub(
                                    r'FROM\s+(?:"[^"]+"|\'[^\']+\'|[a-zA-Z0-9_]+)',
                                    f'FROM {table_name}',
                                    cleaned_sql,
                                    count=1,
                                    flags=re.IGNORECASE
                                )
                            logger.info(f"Fixed truncated table name: {cleaned_sql[:200]}")
                        elif current_table != table_name and current_table.upper() != table_name.upper():
                            # Table name doesn't match - might be wrong table
                            logger.warning(f"Table name mismatch: found '{current_table}', expected '{table_name}'")
                            # Only fix if it's clearly wrong (very short or doesn't match pattern)
                            if len(current_table) < 10:
                                cleaned_sql = re.sub(
                                    r'FROM\s+(?:"[^"]+"|\'[^\']+\'|[a-zA-Z0-9_]+)',
                                    f'FROM "{table_name}"',
                                    cleaned_sql,
                                    count=1,
                                    flags=re.IGNORECASE
                                )
                                logger.info(f"Replaced mismatched table name: {cleaned_sql[:200]}")
            
            # Post-process: Fix missing GROUP BY when COUNT(*) is used with a column
            # Pattern: SELECT "Column", COUNT(*) FROM ... (without GROUP BY)
            # This should have GROUP BY "Column"
            if 'COUNT(*)' in cleaned_sql.upper() and 'GROUP BY' not in cleaned_sql.upper():
                # Check if we have SELECT column, COUNT(*) pattern
                select_match = re.search(r'SELECT\s+"([^"]+)"\s*,\s*COUNT\(\*\)', cleaned_sql, re.IGNORECASE)
                if select_match:
                    column_name = select_match.group(1)
                    # Add GROUP BY clause before any ORDER BY or at the end
                    if 'ORDER BY' in cleaned_sql.upper():
                        # Insert GROUP BY before ORDER BY
                        cleaned_sql = re.sub(
                            r'(\s+)(ORDER\s+BY)',
                            f' \\1GROUP BY "{column_name}"\\1\\2',
                            cleaned_sql,
                            count=1,
                            flags=re.IGNORECASE
                        )
                    else:
                        # Add GROUP BY at the end
                        cleaned_sql = f'{cleaned_sql} GROUP BY "{column_name}"'
                    logger.info(f"Added missing GROUP BY clause for column: {column_name}")
            
            # Post-process: Fix missing LIMIT and ORDER BY for "last N rows" or "first N rows" queries
            # Check if user asked for "last N rows" or "first N rows" but SQL doesn't have LIMIT
            user_question_lower = user_question.lower()
            # Pattern: "last 3 rows", "show last 5 rows", "last 10 rows", etc.
            last_rows_match = re.search(r'last\s+(\d+)\s+rows?', user_question_lower)
            # Pattern: "first 3 rows", "show first 5 rows", "first 10 rows", etc.
            first_rows_match = re.search(r'first\s+(\d+)\s+rows?', user_question_lower)
            # Pattern: "just N rows", "only N rows" (context-dependent, but often means last/first)
            just_rows_match = re.search(r'(just|only)\s+(\d+)\s+rows?', user_question_lower)
            
            # Check if SQL is a simple SELECT * FROM table (no WHERE, no GROUP BY, no LIMIT)
            is_simple_select = (
                re.match(r'SELECT\s+\*\s+FROM\s+', cleaned_sql, re.IGNORECASE) and
                'WHERE' not in cleaned_sql.upper() and
                'GROUP BY' not in cleaned_sql.upper() and
                'LIMIT' not in cleaned_sql.upper()
            )
            
            if is_simple_select:
                if last_rows_match:
                    # User asked for last N rows
                    n = last_rows_match.group(1)
                    cleaned_sql = f'{cleaned_sql} ORDER BY rowid DESC LIMIT {n}'
                    logger.info(f"Added ORDER BY rowid DESC LIMIT {n} for 'last {n} rows' query")
                elif first_rows_match:
                    # User asked for first N rows
                    n = first_rows_match.group(1)
                    cleaned_sql = f'{cleaned_sql} ORDER BY rowid ASC LIMIT {n}'
                    logger.info(f"Added ORDER BY rowid ASC LIMIT {n} for 'first {n} rows' query")
                elif just_rows_match:
                    # User asked for "just N rows" - assume they want last N (most common)
                    n = just_rows_match.group(2)
                    cleaned_sql = f'{cleaned_sql} ORDER BY rowid DESC LIMIT {n}'
                    logger.info(f"Added ORDER BY rowid DESC LIMIT {n} for 'just {n} rows' query")
            
            # Post-process: Detect "how many X is Y" or "count of Y" queries that are missing WHERE clauses
            # This is a critical check - if user asks "how many deal stage is on hold" but SQL has no WHERE, it's wrong
            user_question_lower = user_question.lower()
            
            # Pattern 1: "how many X is Y" or "how many X are Y" - should have WHERE clause
            how_many_with_value_pattern = re.search(r'how many (.+?)\s+(is|are)\s+(.+)', user_question_lower)
            
            # Pattern 2: "count of [value]" or "give the count of [value]" - should have WHERE clause
            count_of_pattern = re.search(r'(?:count|give the count)\s+of\s+(.+)', user_question_lower)
            
            # Pattern 3: "count [value]" (without "of") - might need WHERE clause if it's a specific value
            count_value_pattern = re.search(r'count\s+(.+)', user_question_lower)
            
            should_have_where = False
            column_mention = None
            value_mention = None
            
            if how_many_with_value_pattern:
                column_mention = how_many_with_value_pattern.group(1).strip()
                value_mention = how_many_with_value_pattern.group(3).strip()
                should_have_where = True
            elif count_of_pattern:
                value_mention = count_of_pattern.group(1).strip()
                should_have_where = True
            elif count_value_pattern and not re.search(r'\b(rows?|all|everything)\b', count_value_pattern.group(1)):
                # If it's "count [value]" and value is not "rows", "all", "everything", it might need WHERE
                value_mention = count_value_pattern.group(1).strip()
                # Check if it looks like a specific value (not "rows", "all", etc.)
                if value_mention and len(value_mention) < 50:  # Reasonable value length
                    should_have_where = True
            
            # Check if SQL is just COUNT(*) without WHERE (this is wrong for filtered queries)
            if should_have_where and 'COUNT(*)' in cleaned_sql.upper() and 'WHERE' not in cleaned_sql.upper():
                logger.error(f"ERROR: Detected filtered count query pattern but SQL has no WHERE clause!")
                logger.error(f"User question: '{user_question}'")
                logger.error(f"Column mention: '{column_mention}', Value mention: '{value_mention}'")
                logger.error(f"Generated SQL: {cleaned_sql}")
                logger.error(f"Attempting to auto-fix by constructing WHERE clause...")
                
                # Get table_name for auto-fix
                current_table_name = getattr(self, '_current_table_name', None)
                if not current_table_name:
                    # Try to extract from SQL
                    from_match = re.search(r'FROM\s+["\']?([^"\'\s;]+)', cleaned_sql, re.IGNORECASE)
                    if from_match:
                        current_table_name = from_match.group(1).strip('"\'')
                
                # Try to auto-fix by constructing WHERE clause from database schema
                fixed_sql = self._attempt_where_clause_fix(
                    cleaned_sql=cleaned_sql,
                    table_name=current_table_name,
                    user_question=user_question,
                    column_mention=column_mention,
                    value_mention=value_mention,
                    catalog_summaries=getattr(self, '_current_catalog_summaries', [])
                )
                
                if fixed_sql and fixed_sql != cleaned_sql:
                    logger.info(f"Auto-fixed SQL: {fixed_sql}")
                    cleaned_sql = fixed_sql
                else:
                    logger.error(f"Could not auto-fix SQL - WHERE clause construction failed")
                    
            logger.info(f"Final Cleaned SQL:\n{cleaned_sql}")
            logger.info("=" * 80)
            return cleaned_sql
        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}", exc_info=True)
            raise ValueError(f"Error generating SQL: {str(e)}")
    
    def _attempt_where_clause_fix(
        self,
        cleaned_sql: str,
        table_name: Optional[str],
        user_question: str,
        column_mention: Optional[str],
        value_mention: Optional[str],
        catalog_summaries: List[Dict[str, str]]
    ) -> Optional[str]:
        """Attempt to auto-fix SQL by constructing WHERE clause from database schema."""
        try:
            import re
            from app.services.sql_executor import sql_executor
            
            if not table_name:
                logger.warning("No table_name provided for WHERE clause auto-fix")
                return None
            
            # Extract value from user question
            target_value = value_mention if value_mention else ""
            if not target_value:
                # Try to extract from user question directly
                match = re.search(r'count\s+of\s+(.+)', user_question.lower())
                if not match:
                    match = re.search(r'count\s+(.+)', user_question.lower())
                if match:
                    target_value = match.group(1).strip()
            
            if not target_value:
                logger.warning("Could not extract target value from user question")
                return None
            
            # Normalize value (handle common typos like "closest" -> "Closed")
            target_value_lower = target_value.lower()
            value_corrections = {
                "closest won": "Closed Won",
                "closest": "Closed",
                "on hold": "On Hold",
                "closed won": "Closed Won",
                "closed lost": "Closed Lost",
                "new lead": "New Lead",
                "contacted": "Contacted",
                "qualified": "Qualified",
                "negotiation": "Negotiation",
                "proposal sent": "Proposal Sent",
                "re-engagement": "Re-engagement",
                "disqualified": "Disqualified"
            }
            
            corrected_value = None
            for typo, correct in value_corrections.items():
                if typo in target_value_lower or target_value_lower in typo:
                    corrected_value = correct
                    break
            
            # Fuzzy matching for partial matches
            if not corrected_value:
                if "won" in target_value_lower:
                    corrected_value = "Closed Won"
                elif "hold" in target_value_lower:
                    corrected_value = "On Hold"
                elif "lost" in target_value_lower:
                    corrected_value = "Closed Lost"
                else:
                    corrected_value = target_value.title()
            
            logger.info(f"Extracted value: '{target_value}' -> Corrected: '{corrected_value}'")
            
            # Find column name from database
            column_name = None
            
            try:
                schema = sql_executor.get_table_schema(table_name)
                columns = schema.get('columns', [])
                
                # Prioritize columns matching column_mention or likely status/stage columns
                likely_columns = []
                for col in columns:
                    col_lower = col.lower()
                    if any(keyword in col_lower for keyword in ['stage', 'status', 'state', 'deal']):
                        likely_columns.append(col)
                
                # If column_mention exists, prioritize matching columns
                if column_mention:
                    for col in columns:
                        col_lower = col.lower()
                        mention_lower = column_mention.lower()
                        if mention_lower in col_lower or col_lower in mention_lower:
                            if col not in likely_columns:
                                likely_columns.insert(0, col)
                
                # Try to find column containing the value
                for col in likely_columns:
                    try:
                        # Try exact match
                        test_query = f'SELECT COUNT(*) as cnt FROM "{table_name}" WHERE "{col}" = \'{corrected_value}\' LIMIT 1'
                        result = sql_executor.execute_query(table_name, test_query)
                        if result and len(result) > 0 and result[0].get('cnt', 0) > 0:
                            column_name = col
                            logger.info(f"Found column '{col}' for value '{corrected_value}' (exact match)")
                            break
                    except Exception:
                        # Try case-insensitive match
                        try:
                            test_query = f'SELECT COUNT(*) as cnt FROM "{table_name}" WHERE LOWER("{col}") = LOWER(\'{corrected_value}\') LIMIT 1'
                            result = sql_executor.execute_query(table_name, test_query)
                            if result and len(result) > 0 and result[0].get('cnt', 0) > 0:
                                column_name = col
                                # Get exact value from database
                                distinct_query = f'SELECT DISTINCT "{col}" FROM "{table_name}" WHERE LOWER("{col}") = LOWER(\'{corrected_value}\') LIMIT 1'
                                distinct_result = sql_executor.execute_query(table_name, distinct_query)
                                if distinct_result and len(distinct_result) > 0:
                                    corrected_value = str(list(distinct_result[0].values())[0])
                                logger.info(f"Found column '{col}' for value '{corrected_value}' (case-insensitive)")
                                break
                        except Exception:
                            continue
                
                # If still no match, try all columns with fuzzy matching
                if not column_name:
                    for col in columns:
                        if col in likely_columns:
                            continue
                        try:
                            distinct_query = f'SELECT DISTINCT "{col}" FROM "{table_name}" LIMIT 50'
                            distinct_values = sql_executor.execute_query(table_name, distinct_query)
                            for row in distinct_values:
                                row_value = str(list(row.values())[0]) if row else ""
                                row_value_lower = row_value.lower()
                                if (corrected_value.lower() in row_value_lower or 
                                    row_value_lower in corrected_value.lower() or
                                    any(word in row_value_lower for word in target_value_lower.split() if len(word) > 2)):
                                    column_name = col
                                    corrected_value = row_value
                                    logger.info(f"Found column '{col}' with value '{corrected_value}' (fuzzy match)")
                                    break
                            if column_name:
                                break
                        except Exception:
                            continue
                
            except Exception as e:
                logger.warning(f"Error querying database: {str(e)}")
            
            # Construct WHERE clause
            if column_name and corrected_value:
                escaped_value = corrected_value.replace("'", "''")
                where_clause = f' WHERE "{column_name}" = \'{escaped_value}\''
                
                # Insert WHERE before ORDER BY, GROUP BY, or LIMIT
                sql_upper = cleaned_sql.upper()
                insert_pos = len(cleaned_sql)
                
                for keyword in [' ORDER BY', ' GROUP BY', ' LIMIT']:
                    pos = sql_upper.find(keyword)
                    if pos > 0:
                        insert_pos = min(insert_pos, pos)
                
                fixed_sql = cleaned_sql[:insert_pos] + where_clause + cleaned_sql[insert_pos:]
                logger.info(f"Auto-fixed SQL with WHERE clause: {where_clause}")
                return fixed_sql
            else:
                logger.warning(f"Could not determine column or value. Column: {column_name}, Value: {corrected_value}")
                return None
        
        except Exception as e:
            logger.error(f"Error in _attempt_where_clause_fix: {str(e)}", exc_info=True)
            return None

    def chat_completion(self, messages: List[Dict[str, str]], use_tools: bool = False) -> str:
        """Generate chat completion."""
        # For small talk, use simple completion
        if not use_tools:
            prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            prompt += "\nassistant:"

            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                raise ValueError(f"Error in chat completion: {str(e)}")

        # For tool calls, use structured approach
        return self.chat_completion(messages, use_tools=False)

    def _prepare_catalog_prompt(self, schema: Dict[str, Any], sample_rows: List[Dict[str, Any]], row_count: int) -> str:
        """Prepare prompt for catalog generation."""
        columns_info = "\n".join(
            [f"- {col}: {schema.get('types', {}).get(col, 'unknown')}" for col in schema.get("columns", [])]
        )

        # Add distinct values for categorical columns if available
        categorical_values = schema.get("categorical_values", {})
        if categorical_values:
            values_info = "\n\nDistinct Values in Categorical Columns:\n"
            for col, values in categorical_values.items():
                values_list = ", ".join(values[:15])  # Show first 15 values
                if len(values) > 15:
                    values_list += f", ... (and {len(values) - 15} more)"
                values_info += f"- {col}: {values_list}\n"
        else:
            values_info = ""

        samples_str = "\n".join([str(row) for row in sample_rows[:20]])

        prompt = f"""You are a data cataloging assistant. Analyze the following data schema and samples:

Schema:
{columns_info}
{values_info}
Sample Rows (showing {len(sample_rows)} of {row_count} total rows):
{samples_str}

Total Rows: {row_count}

Generate a concise catalog summary (250-400 words) in markdown format including:
1. Column/keys list with inferred types - LIST ALL COLUMN NAMES EXACTLY AS THEY APPEAR (case-sensitive, with spaces if any)
2. For each categorical column, list the DISTINCT VALUES or SAMPLE VALUES that appear in the data (this is critical for filtering queries)
   - Example: "Deal Stage: On Hold, Closed Won, New Lead, Contacted, Qualified, Negotiation, Proposal Sent, Re-engagement, Disqualified, Closed Lost"
   - This helps users query like "count of On Hold" - they need to know which column contains "On Hold"
3. Null rates and sample values
4. Basic statistics (numeric: min/max/mean; categorical: cardinality and list of unique values)
5. Time columns and grain (if any)
6. Potential join keys or ID columns
7. Quality notes (duplicates, missingness, anomalies)

CRITICAL: When listing categorical columns, show the ACTUAL VALUES that appear (e.g., "Deal Stage: On Hold, Closed Won, New Lead, etc.")
This helps with queries like "count of On Hold" - the system needs to know which column contains "On Hold"

Format as markdown. Be factual and concise."""

        return prompt

    def _prepare_sql_prompt(
        self,
        user_question: str,
        catalog_summaries: List[Dict[str, str]],
        selected_file_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Prepare prompt for SQL generation."""
        catalogs_text = "\n\n".join([f"File: {cat['file_id']}\nSummary: {cat['summary']}" for cat in catalog_summaries])

        table_name = selected_file_id if selected_file_id else "{file_id}"

        # Build conversation context
        history_text = ""
        previous_sql_queries = []
        if conversation_history and len(conversation_history) > 1:
            history_text = "\n\nPrevious conversation:\n"
            for msg in conversation_history[-6:]:  # Last 3 exchanges (6 messages)
                role = "User" if msg["role"] == "user" else "Assistant"
                content = msg['content']
                # Include tool calls (SQL queries) if available to understand what was queried
                if role == "Assistant" and "tool_calls" in msg and msg["tool_calls"]:
                    sql_query = msg["tool_calls"].get("sql_query", "")
                    if sql_query:
                        previous_sql_queries.append(sql_query)
                        content += f"\n[Previous SQL: {sql_query}]"
                history_text += f"{role}: {content}\n"
            
            history_text += "\n" + "="*80 + "\n"
            history_text += "CRITICAL: CONTEXT FOR VISUALIZATION REQUESTS\n"
            history_text += "="*80 + "\n"
            if previous_sql_queries:
                history_text += f"\nPrevious SQL queries (MOST RECENT LAST):\n"
                for i, sql in enumerate(previous_sql_queries[-2:], 1):  # Show last 2 SQL queries
                    history_text += f"Query {i}: {sql}\n"
            history_text += "\nWhen user says 'show it', 'visualize it', 'show that', 'show this', 'show in chart/graph':\n"
            history_text += "1. They are referring to the MOST RECENT SQL query above\n"
            history_text += "2. Extract WHERE clauses and filters from that previous SQL\n"
            history_text += "3. If previous query selected dates only (e.g., SELECT \"Date\" FROM ...):\n"
            history_text += "   → Transform to: SELECT \"Date\", COUNT(*) FROM ... [same WHERE] GROUP BY \"Date\" ORDER BY \"Date\"\n"
            history_text += "4. If previous query selected categories only (e.g., SELECT \"Source\" FROM ...):\n"
            history_text += "   → Transform to: SELECT \"Source\", COUNT(*) FROM ... [same WHERE] GROUP BY \"Source\" ORDER BY COUNT(*) DESC\n"
            history_text += "5. Always maintain all WHERE filters from the previous query\n"
            history_text += "6. Create exactly 2 columns: category/date column + count/value column for visualization\n"
            history_text += "\nEXAMPLE:\n"
            history_text += "  Previous SQL: SELECT \"Date\" FROM table WHERE \"Deal Stage\" = 'Closed Won'\n"
            history_text += "  User says: 'show it in line graph'\n"
            history_text += "  Your answer: SELECT \"Date\", COUNT(*) FROM table WHERE \"Deal Stage\" = 'Closed Won' GROUP BY \"Date\" ORDER BY \"Date\"\n"
            history_text += "="*80 + "\n"

        prompt = f"""You are a SQLite query expert. Generate a query to answer the user's question.
{history_text}
Current question: "{user_question}"

Available data:
{catalogs_text}

Table to query: {table_name}

🚨 CRITICAL DISTINCTION - READ THIS FIRST 🚨
"how many rows" ≠ "how many X is Y" ≠ "count of Y"

WRONG (DO NOT DO THIS):
- User: "how many deal stage is on hold" → SELECT COUNT(*) FROM table ❌ (missing WHERE clause)
- User: "count of On Hold" → SELECT COUNT(*) FROM table ❌ (missing WHERE clause)

CORRECT (DO THIS):
- User: "how many rows" → SELECT COUNT(*) FROM table ✅ (no WHERE needed - user said "rows" not a specific value)
- User: "how many deal stage is on hold" → SELECT COUNT(*) FROM table WHERE "Deal Stage" = 'On Hold' ✅
- User: "can you give the count of On Hold" → SELECT COUNT(*) FROM table WHERE "Deal Stage" = 'On Hold' ✅
- User: "count of Closed Won" → SELECT COUNT(*) FROM table WHERE "Deal Stage" = 'Closed Won' ✅

STEP-BY-STEP PROCESS FOR "how many X is Y":
1. Parse user question: "how many deal stage is on hold"
2. Identify parts:
   - Column mention: "deal stage" (user's words, might be lowercase)
   - Value: "on hold" (user's words, might be lowercase)
3. Find column in catalog:
   - Search catalog for column names containing "deal" and "stage" (case-insensitive)
   - User says "deal stage" → Catalog has "Deal Stage" → Use "Deal Stage" (exact catalog name)
4. Find value format:
   - Check catalog for values in that column
   - Catalog shows: "Deal Stage: On Hold, Closed Won, New Lead, ..."
   - User says "on hold" → Catalog has "On Hold" → Use 'On Hold' (exact case from catalog)
5. Generate SQL:
   SELECT COUNT(*) FROM table WHERE "Deal Stage" = 'On Hold'

STEP-BY-STEP PROCESS FOR "count of Y":
1. Parse user question: "can you give the count of On Hold"
2. Identify value: "On Hold"
3. Find which column contains this value:
   - Search catalog for columns that list "On Hold" as a value
   - Catalog shows: "Deal Stage: On Hold, Closed Won, New Lead, ..."
   - Found! Column is "Deal Stage"
4. Generate SQL:
   SELECT COUNT(*) FROM table WHERE "Deal Stage" = 'On Hold'

CRITICAL RULES:
- If user mentions BOTH a column AND a value → MUST add WHERE clause
- If user mentions ONLY a value (like "On Hold") → MUST find the column containing that value, then add WHERE clause
- NEVER generate COUNT(*) without WHERE when user mentions a specific value
- ALWAYS search catalog case-insensitively to find column names, but use EXACT column name from catalog in SQL

CRITICAL REQUIREMENTS:
1. Database Type: SQLite (NOT PostgreSQL, MySQL, etc.)
2. Table Name: Use EXACTLY "{table_name}" - no schema prefixes (no base., no main.)
   - IMPORTANT: The table name is: {table_name}
   - Use it EXACTLY as shown: {table_name}
   - Do NOT modify it, do NOT add prefixes, do NOT change case
   - Example: FROM {table_name} (correct)
   - Wrong: FROM base.{table_name}, FROM main.{table_name}, FROM "{table_name}".table
3. Column Names: Use EXACT column names from the catalog above (case-sensitive!)
   - CRITICAL: The catalog above contains the ACTUAL column names for THIS specific file - ALWAYS use those names, not examples
   - ALWAYS quote column names with double quotes: "Column Name"
   - If column has spaces: "Account Id", "Lead Owner", "Deal Stage" (MUST use quotes!)
   - If column has no spaces: "Brand" or Brand (quotes recommended for consistency)
   - NEVER use underscores for spaces: "Account Id" NOT Account_Id
   - NEVER use example column names from this prompt - always use the actual column names from the catalog
   - Example: If catalog shows "Brand", use "Brand" NOT "brand"
   - Example: If catalog shows "Account Id", use "Account Id" NOT Account_Id or AccountId
   - IMPORTANT: All examples in this prompt use placeholder names (like "Deal Stage", "Source", "Brand") - these are PATTERNS only
   - You must replace these pattern names with the ACTUAL column names from the catalog above
   - When user asks about a column, search the catalog to find the matching column name (case-sensitive match)
   - CRITICAL FOR FILTERING: When user asks "how many X is Y":
     * First, find the column name "X" in the catalog (e.g., if user says "deal stage", look for "Deal Stage" in catalog)
     * Second, extract the value "Y" from user's question (e.g., "on hold", "closed won")
     * Third, generate: SELECT COUNT(*) FROM table WHERE "X" = 'Y'
     * NEVER generate SELECT COUNT(*) FROM table without WHERE when user mentions a specific column and value
4. Context Awareness: If user refers to "this", "that", "it", "show it", "visualize it" - look at conversation history to understand what they're referring to
   - Check the previous SQL query in conversation history
   - If previous query had filters (WHERE clauses), maintain those filters
   - If previous query returned dates, and user wants to visualize, create: SELECT "Date", COUNT(*) FROM {table_name} WHERE [same filters] GROUP BY "Date" ORDER BY "Date"
5. Date Handling: Dates may be stored as strings in M/D/YYYY format (e.g., "3/29/2025")
   - SQLite's strftime() CANNOT parse M/D/YYYY format directly - it will return NULL or '-'
   - To group by month from M/D/YYYY format, use string manipulation:
     SELECT SUBSTR("Date", -4) || '-' || printf('%02d', CAST(SUBSTR("Date", 1, INSTR("Date", '/') - 1) AS INTEGER)) AS month_year, COUNT(*) 
     FROM {table_name} WHERE ... GROUP BY month_year ORDER BY month_year
   - Explanation: SUBSTR("Date", -4) = last 4 chars (year), SUBSTR("Date", 1, INSTR("Date", '/') - 1) = month, printf pads with zero
   - When user asks "show it in months" or "group by month", use this formula to extract YYYY-MM format
6. Visualization Queries: When user asks to "visualize", "show chart", "show graph", "show it in chart", "show it in months" - return data in 2 columns: label/category column and value column
   - For time series (dates by day): SELECT "Date", COUNT(*) FROM {table_name} WHERE ... GROUP BY "Date" ORDER BY "Date"
   - For time series (dates by month): Use the date extraction formula from requirement 5 to group by month
   - When user says "show it in months": Extract month from date using: SUBSTR("Date", -4) || '-' || printf('%02d', CAST(SUBSTR("Date", 1, INSTR("Date", '/') - 1) AS INTEGER))
   - For dates with counts: If previous query was about dates, group by date and count: SELECT "Date", COUNT(*) FROM {table_name} WHERE [previous filters] GROUP BY "Date" ORDER BY "Date"
   - For time series with values: SELECT "ME_PERIOD", SUM("RetailDollars") FROM {table_name} WHERE ... GROUP BY "ME_PERIOD" ORDER BY "ME_PERIOD"
   - For categorical: SELECT "Brand", SUM("RetailDollars") FROM {table_name} WHERE ... GROUP BY "Brand" ORDER BY SUM("RetailDollars") DESC LIMIT 15
   - For sources with counts: SELECT "Source", COUNT(*) FROM {table_name} GROUP BY "Source" ORDER BY COUNT(*) DESC
   - For listing sources: SELECT DISTINCT "Source" FROM {table_name} ORDER BY "Source"
   - For row count: SELECT COUNT(*) FROM {table_name}
7. NO STRING LITERALS: DO NOT generate SELECT statements with hardcoded string literals like SELECT 'description text'
   - Always query actual data from the table
   - Use actual column names from the catalog
   - Query the data, don't generate descriptive text in SQL
8. No System Tables: DO NOT use INFORMATION_SCHEMA, sqlite_master for column discovery
9. Direct Queries Only: Query the data table directly using column names from catalog
10. Output Format: Return ONLY the SQL query - no explanations, no markdown, no code blocks, no backticks
    - Just the raw SQL query starting with SELECT
    - Example output: SELECT "Source", COUNT(*) FROM {table_name} GROUP BY "Source"
11. Safety: Use SELECT only (no INSERT, UPDATE, DELETE, etc.)
12. Performance: Limit to 100 rows for raw data, 15-20 rows for charts
13. Table Aliases: If using table aliases (AS T1), quote column names in the alias too: T1."Account Id" NOT T1.Account_Id
14. Common Queries (PATTERNS - replace column names with ACTUAL names from catalog):
    - PATTERN: "what are the [column]" or "list the [column]" → SELECT DISTINCT "[ActualColumnName]" FROM {table_name} ORDER BY "[ActualColumnName]"
      * Example pattern: If user asks "what are the sources" and catalog has column "Source", generate: SELECT DISTINCT "Source" FROM {table_name}
      * Example pattern: If user asks "list the categories" and catalog has column "Category", generate: SELECT DISTINCT "Category" FROM {table_name}
      * IMPORTANT: Find the matching column name in the catalog (case-sensitive) and use it exactly as shown
    - PATTERN: "[column] with count" or "[column] and their count" → SELECT "[ActualColumnName]", COUNT(*) FROM {table_name} GROUP BY "[ActualColumnName]" ORDER BY COUNT(*) DESC
      * CRITICAL: When user asks for a column "with count" or "and count" or "along with count", you MUST include GROUP BY to get counts per value
      * CRITICAL: SELECT "Column", COUNT(*) ALWAYS requires GROUP BY "Column" - without GROUP BY, you'll get only one row with total count, not per-value counts
      * IMPORTANT: Replace [column] with the actual column name from the catalog
    - PATTERN: "how many rows" → SELECT COUNT(*) FROM {table_name}
    - PATTERN: "how many [column] is [value]" or "count [column] where [value]" or "how many [column] are [value]" → SELECT COUNT(*) FROM {table_name} WHERE "[ActualColumnName]" = '[ActualValue]'
      * CRITICAL: When user asks "how many X is Y", this means "count rows WHERE X = Y", NOT "count all rows"
      * STEP-BY-STEP PROCESS:
        1. Parse user question: "how many deal stage is on hold"
        2. Identify column mention: "deal stage" → Find "Deal Stage" in catalog (case-insensitive search, but use exact catalog name)
        3. Identify value: "on hold" → Use "On Hold" (match case from catalog if available, or use as-is)
        4. Generate: SELECT COUNT(*) FROM {table_name} WHERE "Deal Stage" = 'On Hold'
      * Example pattern: User asks "how many status is active" and catalog has column "Status" → SELECT COUNT(*) FROM {table_name} WHERE "Status" = 'active'
      * Example pattern: User asks "how many deal stage is on hold" and catalog has column "Deal Stage" → SELECT COUNT(*) FROM {table_name} WHERE "Deal Stage" = 'On Hold'
      * Example pattern: User asks "how many deal stage is closed won" → SELECT COUNT(*) FROM {table_name} WHERE "Deal Stage" = 'Closed Won'
      * Example pattern: User asks "count rows where type is email" and catalog has column "Type" → SELECT COUNT(*) FROM {table_name} WHERE "Type" = 'email'
      * Example pattern: User asks "how many products are available" → SELECT COUNT(*) FROM {table_name} WHERE "Products" = 'available' (if column is "Products")
      * CRITICAL RULE: "how many X is Y" ALWAYS means COUNT(*) WHERE X = Y (with filter), NOT COUNT(*) (without filter)
      * CRITICAL: Always include the complete WHERE condition with column and value. NEVER write just "WHERE" without a condition
      * CRITICAL: NEVER generate SELECT COUNT(*) FROM table without WHERE when user mentions a specific column and value
      * IMPORTANT: Find the matching column name in the catalog (case-insensitive search for matching, but use exact catalog name in SQL)
      * IMPORTANT: Extract the value from user's question (e.g., "on hold", "closed won", "active") and use it in the WHERE clause
      * IMPORTANT: Match the value format from the catalog if available, or use the exact value mentioned by the user
    - PATTERN: "count of [value]" or "count [value]" or "give the count of [value]" → SELECT COUNT(*) FROM {table_name} WHERE "[ColumnName]" = '[value]'
      * CRITICAL: When user asks "count of On Hold" or "give the count of On Hold", you MUST find which column contains "On Hold"
      * STEP-BY-STEP PROCESS:
        1. Parse user question: "can you give the count of On Hold"
        2. Identify value: "On Hold"
        3. Look at catalog to find which column contains values like "On Hold" (e.g., "Deal Stage" column)
        4. Generate: SELECT COUNT(*) FROM {table_name} WHERE "Deal Stage" = 'On Hold'
      * Example: User asks "count of On Hold" → Look in catalog, find "Deal Stage" has values like "On Hold" → SELECT COUNT(*) FROM {table_name} WHERE "Deal Stage" = 'On Hold'
      * Example: User asks "give the count of Closed Won" → Find "Deal Stage" column → SELECT COUNT(*) FROM {table_name} WHERE "Deal Stage" = 'Closed Won'
      * CRITICAL: If user mentions a specific value (like "On Hold", "Closed Won"), you MUST find the column that contains that value and add WHERE clause
      * CRITICAL: NEVER generate COUNT(*) without WHERE when user mentions a specific value
    - PATTERN: "last N rows" or "show last N rows" → SELECT * FROM {table_name} ORDER BY rowid DESC LIMIT N
    - PATTERN: "first N rows" or "show first N rows" → SELECT * FROM {table_name} ORDER BY rowid ASC LIMIT N
    - PATTERN: "just N rows" or "only N rows" → SELECT * FROM {table_name} ORDER BY rowid DESC LIMIT N (typically means last N rows)
    - CRITICAL: When user asks for "last N rows", you MUST include ORDER BY rowid DESC LIMIT N
    - CRITICAL: When user asks for "first N rows", you MUST include ORDER BY rowid ASC LIMIT N
    - CRITICAL: When user asks for "just N rows" or "only N rows", you MUST include ORDER BY rowid DESC LIMIT N (assume they want the last N)
    - For "last rows", always use: ORDER BY rowid DESC LIMIT [number]
    - For "first rows", always use: ORDER BY rowid ASC LIMIT [number]
    - IMPORTANT: Use rowid for ordering when user asks for "last" or "first" rows
    - IMPORTANT: Always include the complete table name: {table_name} (do NOT truncate it)
    - IMPORTANT: NEVER generate SELECT * FROM table without LIMIT when user explicitly asks for a specific number of rows

Example Query Patterns (NOTE: Column names shown are PLACEHOLDERS - use ACTUAL column names from catalog):
- To see data: SELECT * FROM {table_name} LIMIT 10
- Last N rows: SELECT * FROM {table_name} ORDER BY rowid DESC LIMIT N
- First N rows: SELECT * FROM {table_name} ORDER BY rowid ASC LIMIT N
- Count all rows: SELECT COUNT(*) FROM {table_name}
- Count with filter (PATTERN): SELECT COUNT(*) FROM {table_name} WHERE "[ColumnName]" = 'value'
  * Replace [ColumnName] with actual column name from catalog
  * Replace 'value' with the actual value user mentioned (check catalog for value format)
- Count per category (PATTERN): SELECT "[ColumnName]", COUNT(*) FROM {table_name} GROUP BY "[ColumnName]" ORDER BY COUNT(*) DESC
  * Replace [ColumnName] with actual column name from catalog
- Sum with filter (PATTERN): SELECT "[CategoryColumn]", SUM("[NumericColumn]") FROM {table_name} WHERE "[FilterColumn]" = 'value' GROUP BY "[CategoryColumn]"
  * Replace all [ColumnName] placeholders with actual column names from catalog
- Time series (PATTERN): SELECT "[DateColumn]", COUNT(*) FROM {table_name} WHERE ... GROUP BY "[DateColumn]" ORDER BY "[DateColumn]"
  * Replace [DateColumn] with actual date column name from catalog
- IMPORTANT: All column names in examples above are PLACEHOLDERS - you MUST use the actual column names from the catalog

REAL EXAMPLES FROM YOUR DATA (if catalog shows "Deal Stage" column):
- User: "what are the deal stage" → SELECT DISTINCT "Deal Stage" FROM {table_name} ORDER BY "Deal Stage"
  (This works - you can list the values)
- User: "how many deal stage is on hold" → SELECT COUNT(*) FROM {table_name} WHERE "Deal Stage" = 'On Hold'
  (This MUST have WHERE clause - you're counting rows where Deal Stage equals 'On Hold')
- User: "can you give the count of On Hold" → SELECT COUNT(*) FROM {table_name} WHERE "Deal Stage" = 'On Hold'
  (This MUST have WHERE clause - find which column has "On Hold", then filter by it)

The key difference:
- Listing values: SELECT DISTINCT "Deal Stage" FROM table (no WHERE, shows all values)
- Counting filtered: SELECT COUNT(*) FROM table WHERE "Deal Stage" = 'On Hold' (WITH WHERE, counts specific value)

SPECIFIC SCENARIO PATTERNS (NOTE: Column names are PLACEHOLDERS - use ACTUAL names from catalog):

PATTERN 1: Date filtering and visualization
- User asks about dates with a filter → Previous SQL: SELECT "[DateColumn]" FROM {table_name} WHERE "[FilterColumn]" = 'value'
- User now says: "show it in line graph" → Generate: SELECT "[DateColumn]", COUNT(*) FROM {table_name} WHERE "[FilterColumn]" = 'value' GROUP BY "[DateColumn]" ORDER BY "[DateColumn]"
  * Replace [DateColumn] and [FilterColumn] with actual column names from catalog
  * Maintain the WHERE filter from previous query, add GROUP BY and COUNT(*) for visualization

PATTERN 2: Month grouping
- User asked about dates with filter → Previous SQL: SELECT "[DateColumn]" FROM {table_name} WHERE "[FilterColumn]" = 'value'
- User now says: "show it in months" → Generate: SELECT SUBSTR("[DateColumn]", -4) || '-' || printf('%02d', CAST(SUBSTR("[DateColumn]", 1, INSTR("[DateColumn]", '/') - 1) AS INTEGER)) AS month_year, COUNT(*) FROM {table_name} WHERE "[FilterColumn]" = 'value' GROUP BY month_year ORDER BY month_year
  * Replace [DateColumn] and [FilterColumn] with actual column names from catalog
  * Extract month from M/D/YYYY format, maintain WHERE filter, group by month

PATTERN 3: Category listing and counting
- User asks: "show me [category]" → Previous SQL: SELECT "[CategoryColumn]" FROM {table_name}
- User now says: "show it in chart" → Generate: SELECT "[CategoryColumn]", COUNT(*) FROM {table_name} GROUP BY "[CategoryColumn]" ORDER BY COUNT(*) DESC
  * Replace [CategoryColumn] with actual column name from catalog
  * Group by the category and count to create chart data

PATTERN 4: Listing unique values
- User asks: "what are the [items]" or "list the [items]" → Generate: SELECT DISTINCT "[ColumnName]" FROM {table_name} ORDER BY "[ColumnName]"
  * Replace [ColumnName] with actual column name from catalog that matches the user's question

PATTERN 5: Counting with filters
- User asks: "how many [column] is [value]" or "how many [column] are [value]" → Generate: SELECT COUNT(*) FROM {table_name} WHERE "[ColumnName]" = 'value'
  * CRITICAL: "how many X is Y" ALWAYS requires a WHERE clause with X = Y. This is NOT the same as "how many rows"
  * "how many rows" = COUNT(*) FROM table (no WHERE clause) - ONLY when user says "rows" without any column/value
  * "how many X is Y" = COUNT(*) FROM table WHERE "X" = 'Y' (WITH WHERE clause)
  * STEP-BY-STEP:
    1. Parse: "how many deal stage is on hold"
    2. Column: "deal stage" → Search catalog for "Deal Stage" (case-insensitive match, use exact catalog name)
    3. Value: "on hold" → Use "On Hold" (check catalog for exact case, or use as capitalized)
    4. Generate: SELECT COUNT(*) FROM {table_name} WHERE "Deal Stage" = 'On Hold'
  * Find the matching column name in catalog (case-insensitive search, but use exact catalog name in SQL)
  * Extract the value from the user's question (the part after "is" or "are")
  * Use the exact value format from the catalog or user's question (preserve case if catalog shows it)
  * Example: User asks "how many deal stage is on hold" → Find "Deal Stage" column in catalog → Generate: WHERE "Deal Stage" = 'On Hold'
  * Example: User asks "how many status is active" → Find "Status" column in catalog → Generate: WHERE "Status" = 'active'
  * Example: User asks "how many products are available" → Find "Products" column in catalog → Generate: WHERE "Products" = 'available'

PATTERN 6: Counting specific values (value-first queries)
- User asks: "count of [value]" or "give the count of [value]" or "count [value]" → Generate: SELECT COUNT(*) FROM {table_name} WHERE "[ColumnName]" = 'value'
  * CRITICAL: When user mentions a specific value (like "On Hold", "Closed Won"), you MUST find which column contains that value
  * STEP-BY-STEP:
    1. Parse: "can you give the count of On Hold"
    2. Value: "On Hold"
    3. Look at catalog - find which column has values like "On Hold" (e.g., catalog shows "Deal Stage" column with values: "On Hold", "Closed Won", etc.)
    4. Generate: SELECT COUNT(*) FROM {table_name} WHERE "Deal Stage" = 'On Hold'
  * Example: User asks "count of On Hold" → Catalog shows "Deal Stage" column with "On Hold" → WHERE "Deal Stage" = 'On Hold'
  * Example: User asks "give the count of Closed Won" → Find "Deal Stage" column → WHERE "Deal Stage" = 'Closed Won'
  * CRITICAL: If catalog shows a column with sample values matching what user asked, use that column
  * CRITICAL: NEVER generate COUNT(*) without WHERE when user mentions a specific value

CRITICAL REMINDER:
- ALL column names in examples above (like "Date", "Deal Stage", "Source", "Status") are PLACEHOLDERS
- You MUST look at the catalog above to find the ACTUAL column names for THIS specific file
- Match user's question to the actual column names in the catalog (case-sensitive)
- Use the exact column names as they appear in the catalog, not the placeholder names from examples

CRITICAL RULES FOR WHERE, GROUP BY AND ORDER BY:
- NEVER generate "WHERE" without a condition. Always include a condition: WHERE "Column" = 'value' NOT just WHERE
- NEVER generate "GROUP BY" without a column name. Always include the column: GROUP BY "Source" NOT just GROUP BY
- NEVER generate "ORDER BY" without a column name. Always include the column: ORDER BY "Source" NOT just ORDER BY
- When using WHERE clause, always specify the condition: WHERE "Deal Stage" = 'On Hold' NOT just WHERE
- When using GROUP BY with COUNT(*), always include the grouped column: GROUP BY "Source"
- When using ORDER BY, always specify what to order by: ORDER BY "Source" or ORDER BY COUNT(*) DESC
- If you're not sure what condition to use in WHERE, don't include WHERE at all
- If you're not sure what column to use in GROUP BY or ORDER BY, don't include them at all
- When user asks "how many X is Y" or "count X where Y is Z", extract X (column) and Y/Z (value) and create: SELECT COUNT(*) FROM {table_name} WHERE "X" = 'Y' or WHERE "X" = 'Z'
- Example: "how many deal stage is on hold" → SELECT COUNT(*) FROM {table_name} WHERE "Deal Stage" = 'On Hold'
- Example: "count deal stage closed won" → SELECT COUNT(*) FROM {table_name} WHERE "Deal Stage" = 'Closed Won'"""

        return prompt


# Create singleton instance
gemini_service = GeminiService()
