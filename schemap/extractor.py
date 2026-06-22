import psycopg
import libsql
from typing import Any
import fnmatch

def _is_excluded(table_name: str, exclude_tables: list[str]) -> bool:
    for pattern in exclude_tables:
        if fnmatch.fnmatch(table_name, pattern):
            return True
    return False

def _extract_postgres(connection_url: str, exclude_tables: list[str]) -> list[dict[str, Any]]:
    # Query for tables
    tables_query = """
        SELECT table_name,
               obj_description(pg_class.oid, 'pg_class') AS table_description
        FROM information_schema.tables
        JOIN pg_class ON pg_class.relname = information_schema.tables.table_name
        WHERE table_schema = 'public' 
          AND table_type = 'BASE TABLE'
    """
    
    # Query for columns and primary keys
    columns_query = """
        SELECT 
            c.table_name,
            c.column_name,
            c.data_type,
            c.is_nullable,
            col_description(pc.oid, c.ordinal_position) AS column_description,
            CASE WHEN pk.column_name IS NOT NULL THEN TRUE ELSE FALSE END AS is_primary_key
        FROM information_schema.columns c
        JOIN pg_class pc ON pc.relname = c.table_name
        JOIN pg_namespace pn ON pn.oid = pc.relnamespace AND pn.nspname = c.table_schema
        LEFT JOIN (
            SELECT kcu.table_schema, kcu.table_name, kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
        ) pk ON pk.table_schema = c.table_schema 
             AND pk.table_name = c.table_name 
             AND pk.column_name = c.column_name
        WHERE c.table_schema = 'public'
        ORDER BY c.table_name, c.ordinal_position;
    """
    
    # Query for foreign keys
    fk_query = """
        SELECT
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
          AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema = 'public';
    """

    try:
        with psycopg.connect(connection_url) as conn:
            with conn.cursor() as cur:
                # 1. Fetch tables
                cur.execute(tables_query)
                tables_raw = cur.fetchall()
                
                # 2. Fetch columns
                cur.execute(columns_query)
                columns_raw = cur.fetchall()
                
                # 3. Fetch foreign keys
                cur.execute(fk_query)
                fks_raw = cur.fetchall()
    except psycopg.OperationalError as e:
        raise ConnectionError(f"Failed to connect to the PostgreSQL database: {e}")

    # Build the dictionary payload
    tables_dict = {}
    
    for t_name, t_desc in tables_raw:
        if _is_excluded(t_name, exclude_tables):
            continue
        tables_dict[t_name] = {"name": t_name, "description": t_desc, "columns": [], "foreign_keys": []}
        
    for t_name, c_name, c_type, is_null, c_desc, is_pk in columns_raw:
        if t_name in tables_dict:
            tables_dict[t_name]["columns"].append({
                "name": c_name, "data_type": c_type, "is_nullable": is_null == 'YES',
                "primary_key": is_pk, "description": c_desc
            })
            
    for t_name, c_name, f_table, f_col in fks_raw:
        if t_name in tables_dict:
            tables_dict[t_name]["foreign_keys"].append({
                "column_name": c_name, "foreign_table_name": f_table, "foreign_column_name": f_col
            })
            
    return list(tables_dict.values())

def _extract_libsql(connection_url: str, exclude_tables: list[str]) -> list[dict[str, Any]]:
    import urllib.parse
    
    # Parse URL to separate auth token if provided
    parsed = urllib.parse.urlparse(connection_url)
    query_params = urllib.parse.parse_qs(parsed.query)
    
    auth_token = None
    if 'authToken' in query_params:
        auth_token = query_params['authToken'][0]
        # Remove authToken from query string
        clean_query = urllib.parse.urlencode({k: v for k, v in query_params.items() if k != 'authToken'}, doseq=True)
        parsed = parsed._replace(query=clean_query)
        connection_url = urllib.parse.urlunparse(parsed)
        
    # Fix sqlite schemes if needed by libsql
    url = connection_url.replace("sqlite:///", "file:")
    if url.startswith("sqlite://"):
        url = url.replace("sqlite://", "file:")
    
    try:
        if auth_token:
            conn = libsql.connect(database=url, auth_token=auth_token)
        else:
            conn = libsql.connect(database=url)
    except Exception as e:
        raise ConnectionError(f"Failed to connect to the libSQL database: {e}")

    tables_dict = {}
    
    # Extract tables
    tables_cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables_raw = tables_cur.fetchall()
    
    for row in tables_raw:
        t_name = row[0]
        if _is_excluded(t_name, exclude_tables):
            continue
        # SQLite doesn't natively support comments, so we set description to None
        tables_dict[t_name] = {"name": t_name, "description": None, "columns": [], "foreign_keys": []}
        
        # Extract columns
        cols_cur = conn.execute(f"PRAGMA table_info('{t_name}');")
        cols_raw = cols_cur.fetchall()
        # cols_raw format: (cid, name, type, notnull, dflt_value, pk)
        for col in cols_raw:
            c_name = col[1]
            c_type = col[2]
            is_not_null = col[3]
            is_pk = col[5] > 0
            
            tables_dict[t_name]["columns"].append({
                "name": c_name,
                "data_type": c_type,
                "is_nullable": not bool(is_not_null),
                "primary_key": is_pk,
                "description": None
            })
            
        # Extract foreign keys
        fks_cur = conn.execute(f"PRAGMA foreign_key_list('{t_name}');")
        fks_raw = fks_cur.fetchall()
        # fks_raw format: (id, seq, table, from, to, on_update, on_delete, match)
        for fk in fks_raw:
            f_table = fk[2]
            c_name = fk[3]
            f_col = fk[4]
            
            tables_dict[t_name]["foreign_keys"].append({
                "column_name": c_name,
                "foreign_table_name": f_table,
                "foreign_column_name": f_col
            })
            
    conn.close()
    return list(tables_dict.values())

def _extract_mysql(connection_url: str, exclude_tables: list[str]) -> list[dict[str, Any]]:
    import pymysql
    import urllib.parse
    
    parsed = urllib.parse.urlparse(connection_url)
    db_name = parsed.path.lstrip('/')
    
    try:
        conn = pymysql.connect(
            host=parsed.hostname or 'localhost',
            port=parsed.port or 3306,
            user=parsed.username or 'root',
            password=parsed.password or '',
            database=db_name
        )
    except Exception as e:
        raise ConnectionError(f"Failed to connect to the MySQL database: {e}")

    tables_query = "SELECT table_name, table_comment FROM information_schema.tables WHERE table_schema = %s AND table_type = 'BASE TABLE'"
    columns_query = "SELECT table_name, column_name, data_type, is_nullable, column_comment, column_key FROM information_schema.columns WHERE table_schema = %s ORDER BY table_name, ordinal_position"
    fk_query = "SELECT table_name, column_name, referenced_table_name, referenced_column_name FROM information_schema.key_column_usage WHERE referenced_table_name IS NOT NULL AND table_schema = %s"

    with conn.cursor() as cur:
        cur.execute(tables_query, (db_name,))
        tables_raw = cur.fetchall()
        cur.execute(columns_query, (db_name,))
        columns_raw = cur.fetchall()
        cur.execute(fk_query, (db_name,))
        fks_raw = cur.fetchall()
    conn.close()

    tables_dict = {}
    for t_name, t_desc in tables_raw:
        if _is_excluded(t_name, exclude_tables):
            continue
        tables_dict[t_name] = {"name": t_name, "description": t_desc, "columns": [], "foreign_keys": []}
        
    for t_name, c_name, c_type, is_null, c_desc, c_key in columns_raw:
        if t_name in tables_dict:
            tables_dict[t_name]["columns"].append({
                "name": c_name, "data_type": c_type, "is_nullable": is_null == 'YES',
                "primary_key": c_key == 'PRI', "description": c_desc
            })
            
    for t_name, c_name, f_table, f_col in fks_raw:
        if t_name in tables_dict:
            tables_dict[t_name]["foreign_keys"].append({
                "column_name": c_name, "foreign_table_name": f_table, "foreign_column_name": f_col
            })
            
    return list(tables_dict.values())

def _extract_oracle(connection_url: str, exclude_tables: list[str]) -> list[dict[str, Any]]:
    import oracledb
    import urllib.parse
    
    parsed = urllib.parse.urlparse(connection_url)
    username = parsed.username
    password = parsed.password
    host = parsed.hostname
    port = parsed.port or 1521
    service_name = parsed.path.lstrip('/')
    
    try:
        conn = oracledb.connect(user=username, password=password, dsn=f"{host}:{port}/{service_name}")
    except Exception as e:
        raise ConnectionError(f"Failed to connect to the Oracle database: {e}")

    schema = (username.upper() if username else "")

    tables_query = "SELECT table_name, comments FROM all_tab_comments WHERE owner = :schema"
    columns_query = "SELECT c.table_name, c.column_name, c.data_type, c.nullable, m.comments FROM all_tab_columns c LEFT JOIN all_col_comments m ON c.owner = m.owner AND c.table_name = m.table_name AND c.column_name = m.column_name WHERE c.owner = :schema ORDER BY c.table_name, c.column_id"
    pk_query = "SELECT constraint_name, table_name FROM all_constraints WHERE constraint_type = 'P' AND owner = :schema"
    pk_cols_query = "SELECT constraint_name, column_name FROM all_cons_columns WHERE owner = :schema"
    fk_query = """
        SELECT a.table_name AS child_table, 
               a.column_name AS child_column, 
               c_pk.table_name AS parent_table, 
               pk.column_name AS parent_column
        FROM all_cons_columns a
        JOIN all_constraints c ON a.owner = c.owner AND a.constraint_name = c.constraint_name
        JOIN all_constraints c_pk ON c.r_owner = c_pk.owner AND c.r_constraint_name = c_pk.constraint_name
        JOIN all_cons_columns pk ON c_pk.owner = pk.owner AND c_pk.constraint_name = pk.constraint_name AND a.position = pk.position
        WHERE c.constraint_type = 'R' AND a.owner = :schema
    """

    with conn.cursor() as cur:
        cur.execute(tables_query, schema=schema)
        tables_raw = cur.fetchall()
        cur.execute(columns_query, schema=schema)
        columns_raw = cur.fetchall()
        cur.execute(pk_query, schema=schema)
        pk_raw = cur.fetchall()
        cur.execute(pk_cols_query, schema=schema)
        pk_cols_raw = cur.fetchall()
        cur.execute(fk_query, schema=schema)
        fks_raw = cur.fetchall()
    conn.close()

    pk_map = {}
    constraint_to_table = {r[0]: r[1] for r in pk_raw}
    for c_name, col_name in pk_cols_raw:
        if c_name in constraint_to_table:
            t_name = constraint_to_table[c_name]
            if t_name not in pk_map:
                pk_map[t_name] = set()
            pk_map[t_name].add(col_name)

    tables_dict = {}
    for t_name, t_desc in tables_raw:
        if _is_excluded(t_name, exclude_tables):
            continue
        tables_dict[t_name] = {"name": t_name, "description": t_desc, "columns": [], "foreign_keys": []}
        
    for t_name, c_name, c_type, is_null, c_desc in columns_raw:
        if t_name in tables_dict:
            is_pk = t_name in pk_map and c_name in pk_map[t_name]
            tables_dict[t_name]["columns"].append({
                "name": c_name, "data_type": c_type, "is_nullable": is_null == 'Y',
                "primary_key": is_pk, "description": c_desc
            })
            
    for t_name, c_name, f_table, f_col in fks_raw:
        if t_name in tables_dict:
            tables_dict[t_name]["foreign_keys"].append({
                "column_name": c_name, "foreign_table_name": f_table, "foreign_column_name": f_col
            })
            
    return list(tables_dict.values())

def extract_schema(connection_url: str, exclude_tables: list[str]) -> list[dict[str, Any]]:
    """
    Connects to the database and extracts the schema metadata using native catalog queries.
    Routes to the correct extractor based on the connection scheme.
    """
    if connection_url.startswith(("postgresql://", "postgres://")):
        return _extract_postgres(connection_url, exclude_tables)
    elif connection_url.startswith(("libsql://", "https://", "http://", "sqlite://", "file:")):
        return _extract_libsql(connection_url, exclude_tables)
    elif connection_url.startswith(("mysql://", "mysql+pymysql://")):
        return _extract_mysql(connection_url, exclude_tables)
    elif connection_url.startswith(("oracle://", "oracle+oracledb://")):
        return _extract_oracle(connection_url, exclude_tables)
    else:
        raise ValueError(f"Unsupported database scheme in URL: {connection_url}")
