"""PostgreSQL implementation of SqlRunner interface."""

from typing import Optional
import logging
import pandas as pd

from vanna.capabilities.sql_runner import SqlRunner, RunSqlToolArgs
from vanna.core.tool import ToolContext

logger = logging.getLogger(__name__)


class PostgresRunner(SqlRunner):
    """PostgreSQL implementation of the SqlRunner interface."""

    def __init__(
        self,
        connection_string: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = 5432,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs,
    ):
        """Initialize with PostgreSQL connection parameters.

        You can either provide a connection_string OR individual parameters (host, database, etc.).
        If connection_string is provided, it takes precedence.

        Args:
            connection_string: PostgreSQL connection string (e.g., "postgresql://user:password@host:port/database")
            host: Database host address
            port: Database port (default: 5432)
            database: Database name
            user: Database user
            password: Database password
            **kwargs: Additional psycopg2 connection parameters (sslmode, connect_timeout, etc.)
        """
        try:
            import psycopg2
            import psycopg2.extras

            self.psycopg2 = psycopg2
        except Exception as e:
            raise ImportError(
                "psycopg2 package is required. Install with: pip install 'vanna[postgres]'"
            ) from e

        if connection_string:
            self.connection_string = connection_string
            self.connection_params = None
        elif host and database and user:
            self.connection_string = None
            self.connection_params = {
                "host": host,
                "port": port,
                "database": database,
                "user": user,
                "password": password,
                **kwargs,
            }
        else:
            raise ValueError(
                "Either provide connection_string OR (host, database, and user) parameters"
            )

    async def run_sql(self, args: RunSqlToolArgs, context: ToolContext) -> pd.DataFrame:
        """Execute SQL query against PostgreSQL database and return results as DataFrame.

        Args:
            args: SQL query arguments
            context: Tool execution context

        Returns:
            DataFrame with query results

        Raises:
            psycopg2.Error: If query execution fails
        """
        # Extract database info for logging
        db_info = "datalake postgres"
        if self.connection_string:
            # Try to extract host/database from connection string
            try:
                from urllib.parse import urlparse
                parsed = urlparse(self.connection_string)
                db_info = f"{parsed.hostname}:{parsed.port or 5432}/{parsed.path.lstrip('/')}"
            except Exception:
                pass
        elif self.connection_params:
            db_info = f"{self.connection_params.get('host', 'unknown')}:{self.connection_params.get('port', 5432)}/{self.connection_params.get('database', 'unknown')}"

        # Determine query type
        query_type = args.sql.strip().upper().split()[0]
        
        # Truncate SQL for logging (first 200 chars)
        sql_preview = args.sql[:200] + "..." if len(args.sql) > 200 else args.sql
        
        logger.info(
            "Executing SQL query on datalake postgres db: type=%s db=%s sql_preview=%r",
            query_type,
            db_info,
            sql_preview,
        )

        # Connect to the database using either connection string or parameters
        if self.connection_string:
            conn = self.psycopg2.connect(self.connection_string)
        else:
            conn = self.psycopg2.connect(**self.connection_params)

        cursor = conn.cursor(cursor_factory=self.psycopg2.extras.RealDictCursor)

        try:
            # Execute the query
            cursor.execute(args.sql)

            if query_type == "SELECT":
                # Fetch results for SELECT queries
                rows = cursor.fetchall()
                row_count = len(rows) if rows else 0
                
                logger.info(
                    "SQL query results returned from datalake postgres db: type=%s db=%s rows=%d",
                    query_type,
                    db_info,
                    row_count,
                )
                
                if not rows:
                    # Return empty DataFrame
                    return pd.DataFrame()

                # Convert rows to list of dictionaries
                results_data = [dict(row) for row in rows]
                return pd.DataFrame(results_data)
            else:
                # For non-SELECT queries (INSERT, UPDATE, DELETE, etc.)
                conn.commit()
                rows_affected = cursor.rowcount
                
                logger.info(
                    "SQL query executed on datalake postgres db: type=%s db=%s rows_affected=%d",
                    query_type,
                    db_info,
                    rows_affected,
                )
                
                # Return a DataFrame indicating rows affected
                return pd.DataFrame({"rows_affected": [rows_affected]})

        finally:
            cursor.close()
            conn.close()
