"""Statistics and anomaly detection service."""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from app.database.connection import engine
from app.services.gemini_service import gemini_service
from app.services.sql_executor import sql_executor
import logging

logger = logging.getLogger(__name__)


class StatisticsAnalyzer:
    """Service for statistical analysis and anomaly detection."""

    def analyze_data(
        self,
        table_name: str,
        user_question: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform comprehensive statistical analysis."""
        logger.info(f"Starting statistical analysis for table: {table_name}")

        try:
            # Note: table_name should already be validated, but we'll use it as-is
            # Table names with underscores are valid (e.g., c325b621_dc15_4ffb_ab45_82984f2f8a18_input_file_1_csv)
            
            # Load data with filters
            where_clause = self._build_where_clause(filters) if filters else ""
            # Use quoted table name to handle any special characters or long names
            query = f'SELECT * FROM "{table_name}" {where_clause}'
            logger.info(f"Loading data with query: {query}")
            logger.info(f"Table name: {table_name}, Length: {len(table_name)}")
            
            try:
                df = pd.read_sql_query(query, con=engine)
            except Exception as db_error:
                logger.error(f"Database error loading data: {str(db_error)}")
                # Try without quotes as fallback
                query_unquoted = f'SELECT * FROM {table_name} {where_clause}'
                logger.info(f"Trying unquoted table name: {query_unquoted}")
                df = pd.read_sql_query(query_unquoted, con=engine)

            if len(df) == 0:
                return {
                    "error": "No data found with the specified filters",
                    "has_insights": False
                }

            # Generate comprehensive statistics
            stats = {
                "basic_stats": self._calculate_basic_stats(df),
                "distribution": self._calculate_distribution(df),
                "outliers": self._detect_outliers(df),
                "time_trends": self._analyze_time_trends(df),
                "correlations": self._calculate_correlations(df),
                "data_quality": self._assess_data_quality(df)
            }

            # Generate natural language insights using Gemini
            insights_text = self._generate_insights(stats, user_question, df)

            return {
                "has_insights": True,
                "insights_text": insights_text,
                "statistics": stats,
                "row_count": len(df)
            }

        except Exception as e:
            logger.error(f"Error in statistical analysis: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "has_insights": False
            }

    def _build_where_clause(self, filters: Dict[str, Any]) -> str:
        """Build SQL WHERE clause from filters."""
        if not filters:
            return ""

        conditions = []
        for key, value in filters.items():
            # Quote column names that might have spaces
            quoted_key = f'"{key}"' if ' ' in key or '-' in key else key
            if isinstance(value, str):
                conditions.append(f'{quoted_key} = \'{value}\'')
            else:
                conditions.append(f'{quoted_key} = {value}')

        return f"WHERE {' AND '.join(conditions)}"

    def _calculate_basic_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic statistics for numeric columns."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        if not numeric_cols:
            return {}

        stats = {}
        for col in numeric_cols:
            stats[col] = {
                "count": int(df[col].count()),
                "sum": float(df[col].sum()) if not pd.isna(df[col].sum()) else 0,
                "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else 0,
                "median": float(df[col].median()) if not pd.isna(df[col].median()) else 0,
                "std": float(df[col].std()) if not pd.isna(df[col].std()) else 0,
                "min": float(df[col].min()) if not pd.isna(df[col].min()) else 0,
                "max": float(df[col].max()) if not pd.isna(df[col].max()) else 0
            }

        return stats

    def _calculate_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate distribution metrics (percentiles)."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        if not numeric_cols:
            return {}

        distribution = {}
        for col in numeric_cols:
            distribution[col] = {
                "p25": float(df[col].quantile(0.25)) if not pd.isna(df[col].quantile(0.25)) else 0,
                "p50": float(df[col].quantile(0.50)) if not pd.isna(df[col].quantile(0.50)) else 0,
                "p75": float(df[col].quantile(0.75)) if not pd.isna(df[col].quantile(0.75)) else 0,
                "p90": float(df[col].quantile(0.90)) if not pd.isna(df[col].quantile(0.90)) else 0,
                "p95": float(df[col].quantile(0.95)) if not pd.isna(df[col].quantile(0.95)) else 0,
                "p99": float(df[col].quantile(0.99)) if not pd.isna(df[col].quantile(0.99)) else 0
            }

        return distribution

    def _detect_outliers(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect outliers using IQR method."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        outliers = []

        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1

            if IQR == 0:
                continue

            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
            outlier_rows = df[outlier_mask]

            if len(outlier_rows) > 0:
                # Get top 5 outliers
                top_outliers = outlier_rows.nlargest(5, col) if len(outlier_rows) > 5 else outlier_rows

                outliers.append({
                    "column": col,
                    "count": int(len(outlier_rows)),
                    "percentage": round(len(outlier_rows) / len(df) * 100, 2),
                    "lower_bound": float(lower_bound),
                    "upper_bound": float(upper_bound),
                    "examples": top_outliers.to_dict('records')[:5]
                })

        return outliers

    def _analyze_time_trends(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Analyze trends over time if time column exists."""
        # Look for common time column names
        time_columns = [col for col in df.columns if any(
            keyword in col.lower() for keyword in ['date', 'time', 'period', 'day', 'month', 'year']
        )]

        if not time_columns:
            return None

        time_col = time_columns[0]
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        if not numeric_cols:
            return None

        # Group by time and calculate aggregates
        trends = {}
        for num_col in numeric_cols[:3]:  # Limit to first 3 numeric columns
            grouped = df.groupby(time_col)[num_col].agg(['sum', 'mean', 'count'])
            trends[num_col] = grouped.to_dict('index')

        return {
            "time_column": time_col,
            "trends": trends
        }

    def _calculate_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate correlations between numeric columns."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        if len(numeric_cols) < 2:
            return {}

        corr_matrix = df[numeric_cols].corr()

        # Find strong correlations (> 0.7 or < -0.7)
        strong_correlations = []
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) > 0.7 and not pd.isna(corr_value):
                    strong_correlations.append({
                        "col1": numeric_cols[i],
                        "col2": numeric_cols[j],
                        "correlation": float(corr_value)
                    })

        return {
            "strong_correlations": strong_correlations
        }

    def _assess_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess data quality metrics."""
        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isnull().sum().sum()

        return {
            "total_rows": int(df.shape[0]),
            "total_columns": int(df.shape[1]),
            "missing_values": int(missing_cells),
            "missing_percentage": round(missing_cells / total_cells * 100, 2) if total_cells > 0 else 0,
            "columns_with_nulls": df.isnull().sum()[df.isnull().sum() > 0].to_dict()
        }

    def _generate_insights(
        self,
        stats: Dict[str, Any],
        user_question: str,
        df: pd.DataFrame
    ) -> str:
        """Use Gemini to generate natural language insights."""
        # Format statistics for Gemini
        stats_summary = self._format_stats_for_gemini(stats, df)

        prompt = f"""You are a data analyst AI. Analyze the following statistics and provide actionable insights.

User Question: "{user_question}"

{stats_summary}

Provide a comprehensive analysis with:

## 📊 Key Statistics
- Highlight 3-4 most important metrics

## 🔍 Anomalies Detected
- List any unusual patterns or outliers found
- Explain their potential impact

## 📈 Trends & Patterns
- Identify significant trends
- Note any correlations

## 💡 Actionable Insights
- 2-3 specific recommendations based on the data

## ⚠️ Data Quality Notes
- Any data quality issues to be aware of

Format the response in markdown with clear sections. Be concise but insightful."""

        try:
            response = gemini_service.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return "Unable to generate insights at this time."

    def _format_stats_for_gemini(self, stats: Dict[str, Any], df: pd.DataFrame) -> str:
        """Format statistics into readable text for Gemini."""
        lines = []

        # Basic stats
        if stats.get("basic_stats"):
            lines.append("### Basic Statistics:")
            for col, col_stats in list(stats["basic_stats"].items())[:3]:  # Top 3 columns
                lines.append(f"\n**{col}:**")
                lines.append(f"- Count: {col_stats['count']:,}")
                lines.append(f"- Sum: ${col_stats['sum']:,.2f}" if 'Dollar' in col or 'Sales' in col else f"- Sum: {col_stats['sum']:,.2f}")
                lines.append(f"- Mean: ${col_stats['mean']:,.2f}" if 'Dollar' in col or 'Sales' in col else f"- Mean: {col_stats['mean']:,.2f}")
                lines.append(f"- Median: ${col_stats['median']:,.2f}" if 'Dollar' in col or 'Sales' in col else f"- Median: {col_stats['median']:,.2f}")
                lines.append(f"- Range: {col_stats['min']:,.2f} to {col_stats['max']:,.2f}")

        # Outliers
        if stats.get("outliers"):
            lines.append("\n### Outliers:")
            for outlier in stats["outliers"][:3]:  # Top 3 outlier groups
                lines.append(f"\n**{outlier['column']}:** {outlier['count']} outliers ({outlier['percentage']}% of data)")
                lines.append(f"- Expected range: {outlier['lower_bound']:,.2f} to {outlier['upper_bound']:,.2f}")

        # Time trends
        if stats.get("time_trends"):
            lines.append("\n### Time-based Trends:")
            lines.append(f"- Time column: {stats['time_trends']['time_column']}")
            lines.append(f"- Number of periods: {len(df[stats['time_trends']['time_column']].unique())}")

        # Correlations
        if stats.get("correlations", {}).get("strong_correlations"):
            lines.append("\n### Strong Correlations:")
            for corr in stats["correlations"]["strong_correlations"][:3]:
                lines.append(f"- {corr['col1']} ↔ {corr['col2']}: {corr['correlation']:.2f}")

        # Data quality
        if stats.get("data_quality"):
            dq = stats["data_quality"]
            lines.append(f"\n### Data Quality:")
            lines.append(f"- Total rows: {dq['total_rows']:,}")
            lines.append(f"- Total columns: {dq['total_columns']}")
            lines.append(f"- Missing values: {dq['missing_values']:,} ({dq['missing_percentage']}%)")

        return "\n".join(lines)


# Create singleton instance
statistics_analyzer = StatisticsAnalyzer()
