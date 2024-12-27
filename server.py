from mcp.server.fastmcp import FastMCP
from sqlalchemy import create_engine, inspect, text
from tabulate import tabulate
from typing import Optional
import os

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

def format_table_schemas(engine):
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    return "\n".join(format_table_schema(inspector, table_name) for table_name in table_names)

def get_engine():
    engine = os.environ['DB_ENGINE']
    user = os.environ['DB_USER']
    host = os.environ['DB_HOST']
    database = os.environ['DB_DATABASE']
    password = os.environ.get('DB_PASSWORD', '')
    
    connection_string = f"{engine}://{user}:{password}@{host}/{database}" if password else f"{engine}://{host}/{database}"
    return create_engine(connection_string)

# Create engine once at module level for docstring
_engine = get_engine()
_db_info = f"Database: {_engine.dialect.name} version {'.'.join(str(x) for x in _engine.dialect.server_version_info)}"

mcp = FastMCP("MCP Alchemy")

@mcp.tool()
def all_table_names() -> str:
    """Return all table names in the database separated by comma"""
    engine = get_engine()
    inspector = inspect(engine)

    return ", ".join(inspector.get_table_names())

@mcp.tool()
def filter_table_names(q: str) -> str:
    """Return all table names in the database containing the substring 'q' separated by comma"""
    engine = get_engine()
    inspector = inspect(engine)

    return ", ".join(x for x in inspector.get_table_names() if q in x)

@mcp.tool()
def table_columns(table_names: list[str]) -> str:
    """Returns information of table columns and relations for the given list of table_names"""
    engine = get_engine()
    inspector = inspect(engine)

    return "\n".join(format_table_schema(inspector, table_name) for table_name in table_names)

@mcp.tool()
def execute_query(query: str, params: Optional[dict] = None) -> str:
    f"""Execute a SQL query and return results in a readable format. {_db_info}"""
    params = params or {}
    try:
        engine = get_engine()
        with engine.connect() as connection:
            with connection.begin():
                result = connection.execute(text(query), params)
                columns = result.keys()
                rows = result.fetchall()

                output = []
                output.append(f"Query: {query}\n")

                if rows:
                    table = tabulate(rows, headers=columns, tablefmt='grid')
                    output.append(table)
                    output.append(f"\nResult: {len(rows)} rows")
                elif result.rowcount > 0:
                    output.append(f"Success: {result.rowcount} rows affected")
                else:
                    output.append("Success: Query executed")

                return "\n".join(output)

    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()