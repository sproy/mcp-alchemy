# MCP Alchemy

UNDER ACTIVE DEVELOPMENT. WORKS GREAT BUT WILL CHANGE :)

MCP Alchemy is a Model Context Protocol (MCP) server that gives Claude direct access to your SQL databases. It allows Claude to explore database schemas, execute queries, and analyze large result sets through a clean, consistent interface. Supports any SQLAlchemy-compatible database including PostgreSQL, MySQL, MariaDB, and SQLite.

For handling large result sets that exceed Claude's context window, MCP Alchemy integrates with [claude-local-files](https://github.com/runekaagaard/claude-local-files) to enable Claude to analyze complete datasets and generate reports or visualizations.

## Features

- Execute SQL queries with readable vertical output
- Introspect database schemas and column relationships
- List and filter tables
- Handle large result sets with smart truncation
- Full result access via Claude Desktop artifacts
- Clean handling of NULL values and dates

**Note**: The server requires database connection details via environment variables.

## API

### Resources

- `database://system`: SQL database operations interface

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

- **get_schema_definitions**
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
```

2. Install dependencies using uv:
```bash
# Install uv if you haven't already
pip install uv

# Create and activate virtual environment, install dependencies
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# install individual database drivers
uv pip install pymysql
uv pip install psycopg2-binary
```

3. Add database to claude_desktop_config.json

## License

Mozilla Public License Version 2.0 
