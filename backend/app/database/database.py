import os
import tempfile
import logging
from typing import Optional, Dict, Any, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url, URL
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

logger = logging.getLogger("sakhi_ai.database")

Base = declarative_base()

DEFAULT_CA_PATHS = [
    # Render Secret Files standard locations
    "/etc/secrets/aiven-ca.pem",
    "/etc/secrets/ca.pem",
    # Relative to backend or current working directory
    os.path.join("backend", "certs", "aiven-ca.pem"),
    os.path.join("backend", "certs", "ca.pem"),
    os.path.join("certs", "aiven-ca.pem"),
    os.path.join("certs", "ca.pem"),
    # Absolute relative to this module
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "certs", "aiven-ca.pem")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "certs", "ca.pem")),
]

def resolve_ssl_ca(ca_setting: Optional[str] = None) -> Optional[str]:
    """
    Resolves the CA certificate path for PyMySQL SSL verification.
    
    1. If `ca_setting` (or MYSQL_SSL_CA / DATABASE_SSL_CA) contains raw PEM content:
       Extracts and writes it to a temporary certificate file and returns its path.
    2. If `ca_setting` is a path to an existing file:
       Returns the path to that file.
    3. If `ca_setting` points to /etc/secrets/<file> that does not exist directly:
       Checks if /etc/secrets directory contains any valid CA/PEM file and auto-recovers.
    4. If `ca_setting` is not provided:
       Checks standard default locations (e.g. /etc/secrets/aiven-ca.pem, backend/certs/aiven-ca.pem).
    5. If `ca_setting` was explicitly configured as a path but not yet on disk:
       Returns the path so PyMySQL configures SSL and reports FileNotFoundError if missing at connect time,
       preventing silent fallback to unverified SSL which fails with self-signed certificate in chain.
    """
    raw_val = (
        ca_setting
        if ca_setting is not None
        else (settings.MYSQL_SSL_CA or settings.DATABASE_SSL_CA or "")
    )
    # Strip whitespace and accidental surrounding quotes
    val = raw_val.strip().strip("'\"")

    if val:
        # Check if raw PEM certificate content was provided directly in the environment variable
        if "-----BEGIN CERTIFICATE-----" in val:
            pem_content = val.replace("\\n", "\n")
            temp_path = os.path.join(tempfile.gettempdir(), "sakhi_aiven_ca.pem")
            try:
                with open(temp_path, "w", encoding="utf-8") as f:
                    f.write(pem_content)
                logger.info(f"Loaded MySQL CA certificate from environment variable into {temp_path}")
                return temp_path
            except Exception as e:
                logger.error(f"Failed to write CA certificate to temporary file: {e}")
                return None

        # 1. Direct path (absolute or relative to current working directory)
        if os.path.isfile(val):
            return os.path.abspath(val)

        # 2. Relative to backend directory
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        candidate = os.path.join(backend_dir, val)
        if os.path.isfile(candidate):
            return os.path.abspath(candidate)

        # 3. Relative to project root
        project_dir = os.path.abspath(os.path.join(backend_dir, ".."))
        candidate_root = os.path.join(project_dir, val)
        if os.path.isfile(candidate_root):
            return os.path.abspath(candidate_root)

        # 4. If path targets /etc/secrets, inspect /etc/secrets for matching files
        norm_val = os.path.normpath(val)
        norm_secrets = os.path.normpath("/etc/secrets")
        if val.startswith("/etc/secrets") or norm_val.startswith(norm_secrets) or os.path.isdir("/etc/secrets"):
            if os.path.isdir("/etc/secrets"):
                try:
                    available = os.listdir("/etc/secrets")
                    # Check common filenames
                    for fallback_name in ["aiven-ca.pem", "ca.pem", "mysql-ca.pem", "aiven.pem", "ca.crt"]:
                        fpath = os.path.join("/etc/secrets", fallback_name)
                        if os.path.isfile(fpath) or os.path.isfile(os.path.normpath(fpath)):
                            logger.info(f"Auto-discovered alternate CA file in /etc/secrets: {fpath}")
                            return fpath
                    # Check any .pem or .crt in /etc/secrets
                    for fname in available:
                        if fname.endswith((".pem", ".crt")):
                            fpath = os.path.join("/etc/secrets", fname)
                            if os.path.isfile(fpath) or os.path.isfile(os.path.normpath(fpath)):
                                logger.info(f"Auto-discovered CA file in /etc/secrets: {fpath}")
                                return fpath
                except Exception as e:
                    logger.warning(f"Error inspecting /etc/secrets directory: {e}")

        # If explicitly configured path does not exist on disk right now, DO NOT drop it to None.
        # Returning it ensures PyMySQL configures SSL for that path.
        logger.warning(
            f"Configured MySQL SSL CA path '{val}' not currently found on filesystem. "
            f"Retaining configured path for PyMySQL connection."
        )
        return val

    # Check default file paths if not explicitly configured in env
    for candidate_path in DEFAULT_CA_PATHS:
        if os.path.isfile(candidate_path):
            abs_path = os.path.abspath(candidate_path)
            logger.info(f"Found default MySQL CA certificate at: {abs_path}")
            return abs_path

    # Check /etc/secrets directory for any .pem or .crt if present on Render
    if os.path.isdir("/etc/secrets"):
        try:
            for fname in os.listdir("/etc/secrets"):
                if fname.endswith((".pem", ".crt")):
                    fpath = os.path.join("/etc/secrets", fname)
                    if os.path.isfile(fpath):
                        logger.info(f"Discovered CA certificate in /etc/secrets: {fpath}")
                        return fpath
        except Exception:
            pass

    return None

def build_connect_args(ca_path: Optional[str] = None, timeout: int = 5) -> Dict[str, Any]:
    """
    Builds connect_args for PyMySQL with strict SSL certificate verification when a CA is present.
    Never disables SSL verification.
    """
    connect_args: Dict[str, Any] = {
        "connect_timeout": timeout
    }
    if ca_path:
        connect_args["ssl"] = {
            "ca": ca_path,
            "check_hostname": True
        }
    return connect_args

def prepare_database_url_and_connect_args(
    db_url: Optional[str] = None,
    ca_setting: Optional[str] = None
) -> Tuple[URL, Dict[str, Any]]:
    """
    Sanitizes DATABASE_URL and constructs PyMySQL connect_args with proper SSL settings.
    - Strips all SSL-related query parameters from DATABASE_URL so they cannot interfere
      with the explicitly constructed PyMySQL SSL connect_args.
    - Configures PyMySQL `connect_args['ssl']` with strict CA verification.
    """
    url_str = db_url or settings.DATABASE_URL
    url_obj = make_url(url_str)
    
    # Check if ssl_ca was passed in query params
    query = dict(url_obj.query)
    query_ssl_ca = query.get("ssl_ca")
    
    # Strip ALL SSL-related query params so they do not conflict with connect_args['ssl']
    ssl_query_keys = ("ssl-mode", "ssl_mode", "ssl", "ssl_disabled", "ssl_ca", "ssl_cert", "ssl_key", "ssl_verify_cert")
    cleaned_query = {k: v for k, v in query.items() if k not in ssl_query_keys}
    sanitized_url = url_obj.set(query=cleaned_query)

    # Resolve CA path
    ca_path = resolve_ssl_ca(ca_setting or query_ssl_ca)
    
    # Log helpful guidance if Aiven host is detected without CA
    host = sanitized_url.host or ""
    if "aivencloud.com" in host and not ca_path:
        logger.warning(
            "Detected Aiven MySQL host in DATABASE_URL, but no SSL CA certificate was configured or found! "
            "Please configure the MYSQL_SSL_CA environment variable or place 'aiven-ca.pem' in 'backend/certs/'."
        )

    connect_args = build_connect_args(ca_path=ca_path, timeout=5)
    return sanitized_url, connect_args

def log_ssl_startup_diagnostic() -> Dict[str, Any]:
    """
    Safe startup diagnostic that logs ONLY:
    - whether MYSQL_SSL_CA is configured
    - whether the CA file exists
    - the CA file path
    - whether SSL connect_args are being configured
    NEVER logs certificate contents, DATABASE_URL, password, API keys, or JWT secret.
    """
    raw_env = (settings.MYSQL_SSL_CA or settings.DATABASE_SSL_CA or "").strip()
    is_configured = bool(raw_env)
    ca_path = resolve_ssl_ca()
    file_exists = bool(ca_path and os.path.isfile(ca_path))
    file_size = os.path.getsize(ca_path) if file_exists else 0
    ssl_configured = bool(ca_path)

    logger.info("================== Sakhi AI Database SSL Diagnostic ==================")
    logger.info(f"MYSQL_SSL_CA configured in env: {is_configured}")
    logger.info(f"Resolved CA certificate path: {ca_path or 'None'}")
    logger.info(f"CA certificate file exists on disk: {file_exists} (size: {file_size} bytes)")
    logger.info(f"SSL connect_args enabled: {ssl_configured}")

    if os.path.isdir("/etc/secrets"):
        try:
            secrets_files = os.listdir("/etc/secrets")
            logger.info(f"Render /etc/secrets contents: {secrets_files}")
        except Exception as e:
            logger.warning(f"Could not inspect /etc/secrets directory: {e}")

    logger.info("======================================================================")

    return {
        "is_configured": is_configured,
        "ca_path": ca_path,
        "file_exists": file_exists,
        "file_size": file_size,
        "ssl_configured": ssl_configured,
    }

def create_db_engine(db_url: Optional[str] = None, ca_setting: Optional[str] = None):
    """
    Creates the SQLAlchemy engine with connection pooling and SSL settings.
    """
    url, connect_args = prepare_database_url_and_connect_args(db_url=db_url, ca_setting=ca_setting)
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=10,
        max_overflow=20,
        connect_args=connect_args
    )

# Primary application engine
engine = create_db_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connection() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning(f"Database connection check returned: {e}")
        return False

def get_database_migration_info() -> Dict[str, Any]:
    """
    Safely inspects existing tables and current Alembic revision in the connected database.
    Never exposes secrets, credentials, or connection strings.
    """
    try:
        from sqlalchemy import inspect as sa_inspect
        with engine.connect() as connection:
            inspector = sa_inspect(connection)
            tables = sorted(inspector.get_table_names())
            
            revision = None
            if "alembic_version" in tables:
                result = connection.execute(text("SELECT version_num FROM alembic_version")).fetchone()
                if result:
                    revision = result[0]
            
            return {
                "connected": True,
                "tables": tables,
                "table_count": len(tables),
                "alembic_revision": revision,
            }
    except Exception as e:
        logger.warning(f"Failed to inspect database migration info: {e}")
        return {
            "connected": False,
            "error": str(e),
            "tables": [],
            "table_count": 0,
            "alembic_revision": None,
        }

