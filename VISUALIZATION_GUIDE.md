# Visualization Types Guide

This guide explains all available visualization types in the RAG system and when to use each.

## 📊 Available Visualization Types

### 1. **Table** 
**Best for:** Raw data, detailed records, multiple columns, exact values

**Data Format:**
- Any number of columns
- Any number of rows
- Shows all data in a grid format

**When It's Used:**
- Automatically: 3+ columns, 20+ rows, or complex data
- Requested: When you ask for "table", "list", "row and column"

**Examples:**
- "Show all sources and their counts in a table"
- "List all leads with their details"
- "Show me the data in rows and columns"

---

### 2. **Bar Chart** 📊
**Best for:** Comparing categories, rankings, counts per category

**Data Format:**
- 2 columns: Category (text) + Value (number)
- 2-20 rows recommended
- Example: Source names + Count values

**When It's Used:**
- Automatically: 2 columns with categories and numbers (no date column)
- Requested: "bar chart", "bar graph", "bars"

**Examples:**
- "Show sources and their counts" → Bar chart (default)
- "Show me a bar chart of sales by region"
- "Compare deals by stage in a bar graph"

**Good for:**
- ✅ Comparing categories (sources, stages, brands)
- ✅ Rankings (top 10, highest to lowest)
- ✅ Counts and totals per category

---

### 3. **Line Chart** 📈
**Best for:** Trends over time, time series data, continuous data

**Data Format:**
- 2 columns: Time/Date + Value (number)
- Multiple rows over time
- Example: Date + Sales amount

**When It's Used:**
- Automatically: When date/time column is detected
- Requested: "line chart", "line graph", "show trend"

**Examples:**
- "Show sales over time" → Line chart (if Date column exists)
- "Show me a line graph of monthly revenue"
- "Display the trend of leads by month"

**Good for:**
- ✅ Time series (daily, monthly, yearly)
- ✅ Trends and patterns over time
- ✅ Multiple data series on one chart
- ✅ Continuous data

**Note:** Can also be used for categorical data if you explicitly request it, but bar charts are usually better for categories.

---

### 4. **KPI Card** 🎯
**Best for:** Single important number, totals, key metrics

**Data Format:**
- 1 row
- 1 column
- Single number value

**When It's Used:**
- Automatically: When query returns a single number (COUNT, SUM, AVG, etc.)
- Requested: "count", "total", "how many"

**Examples:**
- "How many deals are closed won?" → KPI card (shows single number)
- "What's the total sales amount?"
- "Count all sources"

**Good for:**
- ✅ Single metrics
- ✅ Totals and aggregates
- ✅ Quick answers to "how many" or "what's the total"

---

### 5. **Insights Panel** 💡
**Best for:** Statistical analysis, data quality, anomalies, summaries

**Data Format:**
- Text/analysis output
- Statistical insights
- Markdown formatted

**When It's Used:**
- Automatically: When you ask for statistics, analysis, or insights
- Requested: "statistics", "analyze", "insights", "anomalies"

**Examples:**
- "Show me statistics about the data"
- "Analyze the data for anomalies"
- "What insights can you find?"
- "Find outliers in the sales data"

**Good for:**
- ✅ Statistical summaries
- ✅ Data quality analysis
- ✅ Finding anomalies and outliers
- ✅ Distribution analysis
- ✅ Correlations and patterns

---

## 🎯 Quick Decision Guide

### What data do you have?

**Single number?**
→ **KPI Card**

**Two columns (category + number)?**
- Has date/time? → **Line Chart** (or Bar Chart if you prefer)
- No date? → **Bar Chart** (default) or **Line Chart** (if requested)

**Multiple columns or many rows?**
→ **Table**

**Want statistical analysis?**
→ **Insights Panel**

---

## 📝 How to Request Each Type

### Request a Table:
- "Show as table"
- "List in table format"
- "Show rows and columns"
- "Display as a table"

### Request a Bar Chart:
- "Show as bar chart"
- "Bar graph"
- "Display bars"
- Default for categorical data

### Request a Line Chart:
- "Show as line chart"
- "Line graph"
- "Show trend"
- "Display as line"

### Request KPI:
- "Count..."
- "Total..."
- "How many..."
- Automatically used for single numbers

### Request Insights:
- "Show statistics"
- "Analyze data"
- "Find anomalies"
- "Show insights"
- "Data quality"

---

## 💡 Best Practices

1. **Bar Charts** for comparing categories (sources, stages, regions)
2. **Line Charts** for trends over time (monthly sales, daily leads)
3. **Tables** for detailed data with multiple columns
4. **KPI Cards** for quick single-number answers
5. **Insights Panel** for statistical analysis and data quality

---

## 🔄 Default Behavior

The system automatically chooses the best visualization:

1. **Single number** → KPI Card
2. **Date column + number** → Line Chart
3. **Category + number** → Bar Chart
4. **Multiple columns** → Table
5. **Statistics request** → Insights Panel

You can always override by explicitly requesting a specific type!

---

## 📌 Examples by Use Case

### Comparing Categories:
**Query:** "Show me all sources and their counts"
**Result:** Bar Chart (categories = sources, values = counts)

### Trends Over Time:
**Query:** "Show sales by month"
**Result:** Line Chart (if Date/Month column exists)

### Detailed Records:
**Query:** "Show all leads with details"
**Result:** Table (multiple columns)

### Quick Count:
**Query:** "How many closed won deals?"
**Result:** KPI Card (single number)

### Analysis:
**Query:** "Analyze the data for anomalies"
**Result:** Insights Panel (statistical analysis)

