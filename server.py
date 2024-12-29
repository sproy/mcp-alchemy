from mcp.server.fastmcp import FastMCP
from sqlalchemy import create_engine, inspect, text
from tabulate import tabulate
from typing import Optional
import os

def get_engine(readonly=True):
    engine = os.environ['DB_ENGINE']
    user = os.environ['DB_USER']
    host = os.environ['DB_HOST']
    database = os.environ['DB_DATABASE']
    password = os.environ.get('DB_PASSWORD', '')

    connection_string = f"{engine}://{user}:{password}@{host}/{database}" if password else f"{engine}://{host}/{database}"
    return create_engine(connection_string, isolation_level='AUTOCOMMIT' if not readonly else 'SERIALIZABLE',
                         execution_options={'readonly': readonly})

# Get database connection info first
engine = get_engine(readonly=True)
with engine.connect() as conn:
    db_info = (f"Connected to {engine.dialect.name} "
               f"version {'.'.join(str(x) for x in engine.dialect.server_version_info)} "
               f"database '{os.environ['DB_DATABASE']}' on {os.environ['DB_HOST']} "
               f"as user '{os.environ['DB_USER']}'")

mcp = FastMCP("MCP Alchemy")

@mcp.tool(description=f"Return all table names in the database separated by comma. {db_info}")
def all_table_names() -> str:
    engine = get_engine()
    inspector = inspect(engine)
    return ", ".join(inspector.get_table_names())

@mcp.tool(
    description=f"Return all table names in the database containing the substring 'q' separated by comma. {db_info}"
)
def filter_table_names(q: str) -> str:
    engine = get_engine()
    inspector = inspect(engine)
    return ", ".join(x for x in inspector.get_table_names() if q in x)

@mcp.tool(description=f"Returns schema and relation information for the given tables. {db_info}")
def get_schema_definitions(table_names: list[str]) -> str:
    engine = get_engine()
    inspector = inspect(engine)

    def format_table_schema(inspector, table_name):
        columns = inspector.get_columns(table_name)
        foreign_keys = inspector.get_foreign_keys(table_name)
        primary_keys = set(inspector.get_pk_constraint(table_name)["constrained_columns"])
        output = f"{table_name}:\n"

        # Process columns
        show_key_only = {"nullable", "autoincrement"}
        for column in columns:
            if "comment" in column:
                del column["comment"]
            name = column.pop("name")

            column_parts = (["primary key"] if name in primary_keys else []) + [str(
                column.pop("type"))] + [k if k in show_key_only else f"{k}={v}" for k, v in column.items() if v]

            output += f"    {name}: " + ", ".join(column_parts) + "\n"

        # Process relationships
        if foreign_keys:
            output += "\n    Relationships:\n"
            for fk in foreign_keys:
                constrained_columns = ", ".join(fk['constrained_columns'])
                referred_table = fk['referred_table']
                referred_columns = ", ".join(fk['referred_columns'])
                output += f"      {constrained_columns} -> {referred_table}.{referred_columns}\n"

        return output

    return "\n".join(format_table_schema(inspector, table_name) for table_name in table_names)

# Build dynamic description based on environment
execute_query_max_chars = int(os.environ.get('EXECUTE_QUERY_MAX_CHARS', 4000))
claude_files_path = os.environ.get('CLAUDE_LOCAL_FILES_PATH')

base_desc = (f"Execute a SQL query and return results in a readable format. Results will be truncated after "
             f"{execute_query_max_chars} characters. ")

if claude_files_path:
    base_desc += (
        "Claude Desktop artifacts can fetch the full result set formatted as [[columns], [row1_values], [row2_values], ...] via a supplied url."
    )

@mcp.tool(description=f"{base_desc}{db_info}")
def execute_query(query: str, params: Optional[dict] = None) -> str:
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
                    if len(table) > execute_query_max_chars:
                        # If CLAUDE_LOCAL_FILES_PATH is set, save full results
                        claude_files_path = os.environ.get('CLAUDE_LOCAL_FILES_PATH')
                        if claude_files_path:
                            import json
                            import hashlib

                            # Prepare data in the format [[col1, col2], [val1, val2], ...]
                            data = [list(columns)]
                            data.extend([list(row) for row in rows])

                            # Create SHA256 hash of the data
                            data_str = json.dumps(data)
                            file_hash = hashlib.sha256(data_str.encode()).hexdigest()
                            file_name = f"{file_hash}.json"
                            file_path = os.path.join(claude_files_path, file_name)

                            # Save the file
                            with open(file_path, 'w') as f:
                                json.dump(data, f)

                        # Find the last complete row that fits within the limit
                        lines = table.split('\n')
                        total_chars = 0
                        for i, line in enumerate(lines):
                            total_chars += len(line) + 1  # +1 for newline
                            if total_chars > execute_query_max_chars:
                                table = '\n'.join(lines[:i])
                                message = f"{table}\n\nResult: {len(rows)} rows (output truncated)"
                                if claude_files_path:
                                    message += f"\nArtifact fetch url: https://cdn.jsdelivr.net/pyodide/claude-local-files/{file_name}"
                                return message
                    else:
                        return f"{table}\n\nResult: {len(rows)} rows"
                return "No rows returned"
            else:
                return f"Success: {result.rowcount} rows affected"

    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()
