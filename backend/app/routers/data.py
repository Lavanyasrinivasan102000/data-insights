"""Data retrieval endpoints for interactive tables."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from app.database.connection import get_db
from app.services.sql_executor import sql_executor
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/data", tags=["data"])


@router.get("/table/{table_name}")
async def get_table_data(
    table_name: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of rows per page"),
    search: Optional[str] = Query(None, description="Search term to filter rows"),
    sort_by: Optional[str] = Query(None, description="Column name to sort by"),
    sort_order: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Sort order (asc/desc)"),
    db: Session = Depends(get_db),
):
    """
    Get paginated, filterable, and sortable data from a table.
    
    Args:
        table_name: Name of the table to query
        page: Page number (1-indexed)
        page_size: Number of rows per page
        search: Optional search term to filter rows (searches across all columns)
        sort_by: Optional column name to sort by
        sort_order: Sort order (asc or desc)
        db: Database session
    
    Returns:
        Dictionary with paginated data, total count, and pagination metadata
    """
    try:
        # Validate table name (security check)
        if not sql_executor._validate_table_name(table_name):
            raise HTTPException(status_code=400, detail=f"Invalid table name: {table_name}")
        
        # Get table schema to get column names
        try:
            schema = sql_executor.get_table_schema(table_name)
            columns = schema.get("columns", [])
            if not columns:
                raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found or has no columns")
        except Exception as e:
            logger.error(f"Error getting table schema: {str(e)}")
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        
        # Build WHERE clause for search
        where_clause = ""
        if search and search.strip():
            # Sanitize search term (prevent SQL injection)
            search_term = search.strip()
            # Remove dangerous characters (keep only alphanumeric, spaces, and common safe chars)
            # Escape single quotes for SQL
            search_term_escaped = search_term.replace("'", "''")
            
            # Build search conditions for all columns (use LIKE for pattern matching)
            search_conditions = []
            for col in columns:
                # Quote column names that might have spaces
                quoted_col = f'"{col}"' if ' ' in col or '-' in col else col
                # Use LIKE with escaped search term and CAST to TEXT for type safety
                search_conditions.append(f'CAST({quoted_col} AS TEXT) LIKE \'%{search_term_escaped}%\'')
            
            if search_conditions:
                where_clause = "WHERE " + " OR ".join(search_conditions)
        
        # Build ORDER BY clause
        order_by_clause = ""
        if sort_by:
            # Validate sort_by column name
            if sort_by not in columns:
                raise HTTPException(status_code=400, detail=f"Invalid sort column: {sort_by}")
            
            # Quote column name if it has spaces
            quoted_sort_col = f'"{sort_by}"' if ' ' in sort_by or '-' in sort_by else sort_by
            order_by = "DESC" if sort_order and sort_order.lower() == "desc" else "ASC"
            order_by_clause = f"ORDER BY {quoted_sort_col} {order_by}"
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Quote table name if it's long or has special characters
        quoted_table = f'"{table_name}"' if len(table_name) > 30 or '_' in table_name else table_name
        
        # Build query for total count
        count_query = f'SELECT COUNT(*) as total FROM {quoted_table}'
        if where_clause:
            count_query += f" {where_clause}"
        
        # Execute count query
        try:
            count_result = sql_executor.execute_query(table_name, count_query)
            total_rows = count_result[0]["total"] if count_result else 0
        except Exception as e:
            logger.error(f"Error executing count query: {str(e)}")
            total_rows = 0
        
        # Build main query with pagination
        main_query = f'SELECT * FROM {quoted_table}'
        if where_clause:
            main_query += f" {where_clause}"
        if order_by_clause:
            main_query += f" {order_by_clause}"
        else:
            # Default sort by rowid for consistent pagination
            main_query += " ORDER BY rowid ASC"
        
        main_query += f" LIMIT {page_size} OFFSET {offset}"
        
        # Execute main query
        try:
            rows = sql_executor.execute_query(table_name, main_query)
        except Exception as e:
            logger.error(f"Error executing main query: {str(e)}")
            # If query fails, try without search parameters (might be issue with parameterized query)
            # Fallback to simple query
            simple_query = f'SELECT * FROM {quoted_table}'
            if order_by_clause:
                simple_query += f" {order_by_clause}"
            else:
                simple_query += " ORDER BY rowid ASC"
            simple_query += f" LIMIT {page_size} OFFSET {offset}"
            rows = sql_executor.execute_query(table_name, simple_query)
        
        # Calculate pagination metadata
        total_pages = (total_rows + page_size - 1) // page_size if total_rows > 0 else 0
        has_next = page < total_pages
        has_previous = page > 1
        
        return {
            "data": rows,
            "columns": columns,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_rows": total_rows,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_previous": has_previous,
            },
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_table_data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving data: {str(e)}")


@router.get("/table/{table_name}/columns")
async def get_table_columns(
    table_name: str,
    db: Session = Depends(get_db),
):
    """
    Get column names and types for a table.
    
    Args:
        table_name: Name of the table
        db: Database session
    
    Returns:
        Dictionary with column names and types
    """
    try:
        # Validate table name
        if not sql_executor._validate_table_name(table_name):
            raise HTTPException(status_code=400, detail=f"Invalid table name: {table_name}")
        
        # Get table schema
        schema = sql_executor.get_table_schema(table_name)
        columns = schema.get("columns", [])
        column_types = schema.get("types", {})
        
        if not columns:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found or has no columns")
        
        return {
            "columns": columns,
            "column_types": column_types,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_table_columns: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving columns: {str(e)}")

