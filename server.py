import os, json, hashlib
from typing import Optional

from mcp.server.fastmcp import FastMCP
from sqlalchemy import create_engine, inspect, text
from tabulate import tabulate

### Utility functions ###

def get_engine(readonly=True):
    engine = os.environ['DB_ENGINE']
    user = os.environ['DB_USER']
    host = os.environ['DB_HOST']
    database = os.environ['DB_DATABASE']
    password = os.environ.get('DB_PASSWORD', '')
    connection_string = f"{engine}://{user}:{password}@{host}/{database}" if password else f"{engine}://{host}/{database}"

    return create_engine(connection_string, isolation_level='AUTOCOMMIT', execution_options={'readonly': readonly})

def get_db_info():
    engine = get_engine(readonly=True)
    with engine.connect() as conn:
        return (f"Connected to {engine.dialect.name} "
                f"version {'.'.join(str(x) for x in engine.dialect.server_version_info)} "
                f"database '{os.environ['DB_DATABASE']}' on {os.environ['DB_HOST']} "
                f"as user '{os.environ['DB_USER']}'")

### Constants ###

DB_INFO = get_db_info()
EXECUTE_QUERY_MAX_CHARS = int(os.environ.get('EXECUTE_QUERY_MAX_CHARS', 4000))
CLAUDE_FILES_PATH = os.environ.get('CLAUDE_LOCAL_FILES_PATH')

### MCP tools ###

mcp = FastMCP("MCP Alchemy")

@mcp.tool(description=f"Return all table names in the database separated by comma. {DB_INFO}")
def all_table_names() -> str:
    engine = get_engine()
    inspector = inspect(engine)
    return ", ".join(inspector.get_table_names())

@mcp.tool(
    description=f"Return all table names in the database containing the substring 'q' separated by comma. {DB_INFO}"
)
def filter_table_names(q: str) -> str:
    engine = get_engine()
    inspector = inspect(engine)
    return ", ".join(x for x in inspector.get_table_names() if q in x)

@mcp.tool(description=f"Returns schema and relation information for the given tables. {DB_INFO}")
def get_schema_definitions(table_names: list[str]) -> str:
    def format(inspector, table_name):
        columns = inspector.get_columns(table_name)
        foreign_keys = inspector.get_foreign_keys(table_name)
        primary_keys = set(inspector.get_pk_constraint(table_name)["constrained_columns"])
        result = [f"{table_name}:"]

        # Process columns
        show_key_only = {"nullable", "autoincrement"}
        for column in columns:
            if "comment" in column:
                del column["comment"]
            name = column.pop("name")

            column_parts = (["primary key"] if name in primary_keys else []) + [str(
                column.pop("type"))] + [k if k in show_key_only else f"{k}={v}" for k, v in column.items() if v]

            result.append(f"    {name}: " + ", ".join(column_parts))

        # Process relationships
        if foreign_keys:
            result.extend(["", "    Relationships:"])
            for fk in foreign_keys:
                constrained_columns = ", ".join(fk['constrained_columns'])
                referred_table = fk['referred_table']
                referred_columns = ", ".join(fk['referred_columns'])
                result.append(f"      {constrained_columns} -> {referred_table}.{referred_columns}")

        return "\n".join(result)

    engine = get_engine()
    inspector = inspect(engine)

    return "\n".join(format(inspector, table_name) for table_name in table_names)

def execute_query_description():
    description_parts = [
        f"Execute a SQL query and return results in a readable format. Results will be truncated after"
        f"{EXECUTE_QUERY_MAX_CHARS} characters."
    ]

    if CLAUDE_FILES_PATH:
        description_parts.append(
            "Claude Desktop may fetch the full result set via an url for analysis and artifacts.")

    description_parts.append(DB_INFO)

    return " ".join(description_parts)

@mcp.tool(description=execute_query_description())
def execute_query(query: str, params: Optional[dict] = None) -> str:
    def claude_local_files(rows):
        CLAUDE_FILES_PATH = os.environ.get('CLAUDE_LOCAL_FILES_PATH')
        if not CLAUDE_FILES_PATH:
            return ""

        data = [list(row) for row in rows]
        file_hash = hashlib.sha256(json.dumps(data).encode()).hexdigest()
        file_name = f"{file_hash}.json"
        file_path = os.path.join(CLAUDE_FILES_PATH, file_name)

        with open(file_path, 'w') as f:
            json.dump(data, f)

        return (f"\nFull result set url: https://cdn.jsdelivr.net/pyodide/claude-local-files/{file_name}"
                " (format: [[row1_value1, row1_value2, ...], [row2_value1, row2_value2, ...], ...])")

    params = params or {}

    try:
        engine = get_engine(readonly=False)

        with engine.connect() as connection:
            result = connection.execute(text(query), params)

            if result.returns_rows:
                columns = result.keys()
                rows = result.fetchall()
                if rows:
                    table = tabulate(rows, headers=columns, tablefmt='simple')
                    claude_files_message = claude_local_files(rows)

                    if len(table) > EXECUTE_QUERY_MAX_CHARS:
                        # Find the last complete row that fits within the limit
                        lines = table.split('\n')
                        total_chars = 0
                        for i, line in enumerate(lines):
                            total_chars += len(line) + 1  # +1 for newline
                            if total_chars > EXECUTE_QUERY_MAX_CHARS:
                                table = '\n'.join(lines[:i])
                                message = f"{table}\n\nResult: {len(rows)} rows (output truncated)"

                                return message + claude_files_message
                    else:
                        return f"{table}\n\nResult: {len(rows)} rows" + claude_files_message
                return "No rows returned"
            else:
                return f"Success: {result.rowcount} rows affected"

    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()
