# MCP Alchemy

![MCP Alchemy in action](screenshot.png)

Let Claude be your database expert! MCP Alchemy connects Claude Desktop directly to your databases, allowing it to:

- Help you explore and understand your database structure
- Assist in writing and validating SQL queries
- Analyze large datasets and create reports
- Map relationships between tables

Works with PostgreSQL, MySQL, MariaDB, SQLite, and other SQLAlchemy-compatible databases.

## Key Features

For Database Exploration:
- Ask Claude about available tables and their relationships
- Get detailed schema information and foreign key mappings
- Have Claude explain complex database structures

For Query Assistance:
- Let Claude write and validate SQL queries
- Get results in a clean, readable format
- Handle NULL values and dates properly

For Data Analysis:
- Work with datasets larger than Claude's context window
- Generate reports and visualizations through [claude-local-files](https://github.com/runekaagaard/claude-local-files)
- Let Claude analyze complete result sets

**Note**: The server requires database connection details via environment variables.

## API

### Tools

- **all_table_names**
  - Return all table names in the database
  - No input required
  - Returns comma-separated list of tables
  ```
  users, orders, products, categories
  ```

- **filter_table_names**
  - Find tables matching a substring
  - Input: `q` (string)
  - Returns matching table names
  ```
  Input: "user"
  Returns: "users, user_roles, user_permissions"
  ```

- **schema_definitions**
  - Get detailed schema for specified tables
  - Input: `table_names` (string[])
  - Returns table definitions including:
    - Column names and types
    - Primary keys
    - Foreign key relationships
    - Nullable flags
  ```
  users:
      id: INTEGER, primary key, autoincrement
      email: VARCHAR(255), nullable
      created_at: DATETIME
      
      Relationships:
        id -> orders.user_id
  ```

- **execute_query**
  - Execute SQL query with vertical output format
  - Inputs:
    - `query` (string): SQL query
    - `params` (object, optional): Query parameters
  - Returns results in clean vertical format:
  ```
  1. row
  id: 123
  name: John Doe
  created_at: 2024-03-15T14:30:00
  email: NULL

  Result: 1 rows
  ```
  - Features:
    - Smart truncation of large results
    - Full result set access via [claude-local-files](https://github.com/runekaagaard/claude-local-files) integration
    - Clean NULL value display
    - ISO formatted dates
    - Clear row separation

## Usage with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "my_database": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp-alchemy",
        "run",
        "server.py"
      ],
      "env": {
        "DB_URL": "mysql+pymysql://root:secret@localhost/databasename",
        "EXECUTE_QUERY_MAX_CHARS": "5000"  // Optional, default 4000
        "CLAUDE_LOCAL_FILES_PATH": "/path/to/claude-local-files/files",  // Optional
      }
    }
  }
}
```

## Environment Variables

- `DB_URL`: SQLAlchemy [database URL](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls) (required)
  Examples:
  - PostgreSQL: `postgresql://user:password@localhost/dbname`
  - MySQL: `mysql+pymysql://user:password@localhost/dbname`
  - MariaDB: `mariadb+pymysql://user:password@localhost/dbname`
  - SQLite: `sqlite:///path/to/database.db`
- `CLAUDE_LOCAL_FILES_PATH`: Directory for full result sets (optional)
- `EXECUTE_QUERY_MAX_CHARS`: Maximum output length (optional, default 4000)

## Installation

1. Clone repository:
```bash
git clone https://github.com/runekaagaard/mcp-alchemy.git
cd mcp-alchemy
```

2. Install using uv:
```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install the project with all dependencies
uv venv
source .venv/bin/activate
uv pip install -e .
```

3. Add database to claude_desktop_config.json

## Database Drivers

The following database drivers are included by default:
- SQLite: Built into Python, no additional installation needed
- MySQL/MariaDB: Via `pymysql`
- PostgreSQL: Via `psycopg2-binary`

To use other databases supported by SQLAlchemy, install the appropriate driver:
```bash
# Microsoft SQL Server
uv pip install pymssql

# Oracle
uv pip install cx_oracle

# Other databases
# See: https://docs.sqlalchemy.org/en/20/dialects/
```

## License

Mozilla Public License Version 2.0 
