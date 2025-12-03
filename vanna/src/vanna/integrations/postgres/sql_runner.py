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
        connect_timeout: int = 120,
        statement_timeout: Optional[int] = None,
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
            connect_timeout: Connection timeout in seconds (default: 60)
            statement_timeout: Query timeout in milliseconds (default: None = no limit). 
                               Set to 0 to disable timeout, or a value like 3600000 for 1 hour.
            **kwargs: Additional psycopg2 connection parameters (sslmode, etc.)
        """
        try:
            import psycopg2
            import psycopg2.extras

            self.psycopg2 = psycopg2
        except Exception as e:
            raise ImportError(
                "psycopg2 package is required. Install with: pip install 'vanna[postgres]'"
            ) from e

        self.connect_timeout = connect_timeout
        self.statement_timeout = statement_timeout

        if connection_string:
            # Parse connection string and add timeout parameters
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
                "connect_timeout": connect_timeout,
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
        logger.info(
            "Attempting database connection: db=%s connect_timeout=%ds",
            db_info,
            self.connect_timeout,
        )
        
        conn = None
        try:
            if self.connection_string:
                # Parse connection string to add timeout parameters
                from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
                parsed = urlparse(self.connection_string)
                query_params = parse_qs(parsed.query)
                # Add connect_timeout if not already present
                if 'connect_timeout' not in query_params:
                    query_params['connect_timeout'] = [str(self.connect_timeout)]
                # Rebuild connection string with timeout
                new_query = urlencode(query_params, doseq=True)
                connection_string_with_timeout = urlunparse((
                    parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment
                ))
                conn = self.psycopg2.connect(connection_string_with_timeout)
            else:
                conn = self.psycopg2.connect(**self.connection_params)
            
            logger.info(
                "Database connection successful: db=%s",
                db_info,
            )
        except Exception as conn_error:
            logger.error(
                "Database connection FAILED: db=%s error=%s",
                db_info,
                str(conn_error),
            )
            raise

        cursor = conn.cursor(cursor_factory=self.psycopg2.extras.RealDictCursor)

        try:
            # Set statement timeout if specified (in milliseconds)
            if self.statement_timeout is not None:
                if self.statement_timeout == 0:
                    # Disable timeout
                    cursor.execute("SET statement_timeout = 0")
                    logger.info("Statement timeout disabled for this connection (no query timeout)")
                else:
                    cursor.execute(f"SET statement_timeout = {self.statement_timeout}")
                    logger.info(
                        "Statement timeout set to %d ms (%.1f minutes) for query execution",
                        self.statement_timeout,
                        self.statement_timeout / 60000.0,
                    )
            
            # Execute the query
            logger.info(
                "SQL query execution started: type=%s db=%s timeout=%s",
                query_type,
                db_info,
                "disabled" if self.statement_timeout == 0 else 
                f"{self.statement_timeout}ms" if self.statement_timeout else "default",
            )
            cursor.execute(args.sql)
            logger.info(
                "SQL query execution completed: type=%s db=%s (fetching results...)",
                query_type,
                db_info,
            )

            # Decide based on presence of a result set instead of first keyword.
            # This correctly handles queries starting with WITH that return rows.
            if cursor.description:
                logger.debug("Fetching query results from database...")
                rows = cursor.fetchall()
                row_count = len(rows) if rows else 0

                logger.info(
                    "SQL query results returned: type=%s db=%s rows=%d columns=%d",
                    query_type,
                    db_info,
                    row_count,
                    len(cursor.description) if cursor.description else 0,
                )

                if row_count > 0:
                    column_names = [desc[0] for desc in cursor.description]
                    logger.debug(
                        "Query result columns: %s",
                        ", ".join(column_names[:10]) + ("..." if len(column_names) > 10 else ""),
                    )

                # Return empty DataFrame if no rows
                if not rows:
                    return pd.DataFrame()

                # Convert rows to list of dictionaries
                results_data = [dict(row) for row in rows]
                return pd.DataFrame(results_data)
            else:
                # No result set (e.g., DML/DDL). Commit and return rows affected.
                logger.debug("Committing transaction for %s query...", query_type)
                conn.commit()
                rows_affected = cursor.rowcount

                logger.info(
                    "SQL query executed successfully: type=%s db=%s rows_affected=%d",
                    query_type,
                    db_info,
                    rows_affected,
                )

                return pd.DataFrame({"rows_affected": [rows_affected]})

        except self.psycopg2.OperationalError as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                logger.error(
                    "Database connection/query timeout error: db=%s error=%s (connect_timeout=%ds, statement_timeout=%s)",
                    db_info,
                    error_msg,
                    self.connect_timeout,
                    f"{self.statement_timeout}ms" if self.statement_timeout else "default",
                )
            else:
                logger.error(
                    "Database operational error: db=%s error=%s",
                    db_info,
                    error_msg,
                )
            raise
        except self.psycopg2.extensions.QueryCanceledError as e:
            logger.error(
                "Query canceled due to statement timeout: db=%s statement_timeout=%s error=%s",
                db_info,
                f"{self.statement_timeout}ms" if self.statement_timeout else "default",
                str(e),
            )
            raise
        except self.psycopg2.Error as e:
            logger.error(
                "Database error during query execution: db=%s error=%s",
                db_info,
                str(e),
            )
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during query execution: db=%s error=%s type=%s",
                db_info,
                str(e),
                type(e).__name__,
            )
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                logger.debug("Closing database connection: db=%s", db_info)
                conn.close()
                logger.debug("Database connection closed: db=%s", db_info)
