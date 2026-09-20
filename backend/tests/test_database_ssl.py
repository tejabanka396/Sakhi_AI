import os
import ssl
import tempfile
import pymysql
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import text
from sqlalchemy.engine.url import make_url

from app.core.config import settings
from app.database.database import (
    resolve_ssl_ca,
    build_connect_args,
    prepare_database_url_and_connect_args,
    create_db_engine,
    check_db_connection,
)

SAMPLE_PEM_CERT = (
    "-----BEGIN CERTIFICATE-----\n"
    "MIIB/zCCAaWgAwIBAgIUQ1234567890abcdefghijklmnopqrstuvwxyzAB==\n"
    "-----END CERTIFICATE-----\n"
)

def test_default_connect_args_has_no_ssl_when_no_ca():
    """Verify that when no CA is configured, connect_args only contains connect_timeout (for local dev)."""
    args = build_connect_args(ca_path=None, timeout=5)
    assert args == {"connect_timeout": 5}
    assert "ssl" not in args

def test_build_connect_args_with_ca():
    """Verify that when a CA path is provided, strict SSL verification is configured."""
    ca_path = "/fake/path/to/aiven-ca.pem"
    args = build_connect_args(ca_path=ca_path, timeout=10)
    assert args["connect_timeout"] == 10
    assert "ssl" in args
    assert args["ssl"]["ca"] == ca_path
    assert args["ssl"]["check_hostname"] is True

def test_resolve_ssl_ca_from_file_path(tmp_path):
    """Verify resolve_ssl_ca locates a certificate from an existing file path."""
    cert_file = tmp_path / "test_aiven_ca.pem"
    cert_file.write_text(SAMPLE_PEM_CERT, encoding="utf-8")

    resolved = resolve_ssl_ca(str(cert_file))
    assert resolved is not None
    assert os.path.isfile(resolved)
    assert os.path.abspath(resolved) == os.path.abspath(str(cert_file))

def test_resolve_ssl_ca_from_raw_pem_string():
    """Verify resolve_ssl_ca writes inline PEM text into a temporary CA file and returns its path."""
    resolved = resolve_ssl_ca(SAMPLE_PEM_CERT)
    assert resolved is not None
    assert os.path.isfile(resolved)
    with open(resolved, "r", encoding="utf-8") as f:
        content = f.read()
    assert "-----BEGIN CERTIFICATE-----" in content
    assert "-----END CERTIFICATE-----" in content

def test_resolve_ssl_ca_from_escaped_newlines_pem():
    """Verify resolve_ssl_ca properly decodes escaped '\\n' strings from env variables."""
    escaped_pem = SAMPLE_PEM_CERT.replace("\n", "\\n")
    resolved = resolve_ssl_ca(escaped_pem)
    assert resolved is not None
    assert os.path.isfile(resolved)
    with open(resolved, "r", encoding="utf-8") as f:
        content = f.read()
    assert "\n" in content

def test_pymysql_ssl_context_enforces_strict_verification(tmp_path):
    """
    Verify that PyMySQL builds an SSLContext with CERT_REQUIRED and check_hostname=True.
    This guarantees SSL verification is never disabled.
    """
    cert_file = tmp_path / "valid_ca.pem"
    cert_file.write_text(SAMPLE_PEM_CERT, encoding="utf-8")

    conn = pymysql.connections.Connection(defer_connect=True)
    ssl_dict = {"ca": str(cert_file), "check_hostname": True}

    # PyMySQL _create_ssl_ctx creates an SSLContext
    # We mock load_verify_locations to prevent OpenSSL from rejecting the dummy test cert
    with patch.object(ssl.SSLContext, "load_verify_locations") as mock_load:
        ctx = conn._create_ssl_ctx(ssl_dict)
        mock_load.assert_called_once_with(str(cert_file), None, None)
        assert ctx.verify_mode == ssl.CERT_REQUIRED
        assert ctx.check_hostname is True

def test_prepare_database_url_and_connect_args_strips_ssl_mode():
    """
    Verify that unsupported CLI parameters like ?ssl-mode=REQUIRED are cleaned up
    so PyMySQL does not fail with an unexpected keyword argument.
    """
    raw_url = "mysql+pymysql://avnadmin:secret123@sakhi-mysql-sakhiai.i.aivencloud.com:12345/defaultdb?ssl-mode=REQUIRED&charset=utf8mb4"
    sanitized_url, connect_args = prepare_database_url_and_connect_args(db_url=raw_url, ca_setting=SAMPLE_PEM_CERT)

    # Ensure ssl-mode is not in the sanitized URL query
    assert "ssl-mode" not in sanitized_url.query
    assert sanitized_url.query.get("charset") == "utf8mb4"
    assert sanitized_url.host == "sakhi-mysql-sakhiai.i.aivencloud.com"

    # Ensure SSL connect_args are present
    assert "ssl" in connect_args
    assert "ca" in connect_args["ssl"]
    assert connect_args["ssl"]["check_hostname"] is True

def test_engine_connect_passes_ssl_args_to_pymysql(tmp_path):
    """Verify that SQLAlchemy engine.connect passes the exact SSL arguments to pymysql.connect."""
    cert_file = tmp_path / "aiven-ca.pem"
    cert_file.write_text(SAMPLE_PEM_CERT, encoding="utf-8")
    test_ca_path = str(cert_file)

    test_url = "mysql+pymysql://avnadmin:secret123@sakhi-mysql-sakhiai.i.aivencloud.com:12345/defaultdb"
    engine = create_db_engine(db_url=test_url, ca_setting=test_ca_path)

    with patch("pymysql.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        try:
            with engine.connect() as connection:
                pass
        except Exception:
            pass

        assert mock_connect.called
        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs.get("host") == "sakhi-mysql-sakhiai.i.aivencloud.com"
        assert call_kwargs.get("user") == "avnadmin"
        assert call_kwargs.get("password") == "secret123"
        assert call_kwargs.get("port") == 12345
        assert call_kwargs.get("connect_timeout") == 5
        assert call_kwargs.get("ssl") == {
            "ca": os.path.abspath(test_ca_path),
            "check_hostname": True
        }

def test_check_db_connection_handles_failure():
    """Verify check_db_connection returns False cleanly when connection fails."""
    with patch("app.database.database.engine.connect", side_effect=Exception("Connection refused")):
        assert check_db_connection() is False

def test_resolve_ssl_ca_with_surrounding_quotes(tmp_path):
    """Verify resolve_ssl_ca strips accidental single and double quotes from env value."""
    cert_file = tmp_path / "quoted_ca.pem"
    cert_file.write_text(SAMPLE_PEM_CERT, encoding="utf-8")

    quoted_val = f'"{cert_file}"'
    resolved = resolve_ssl_ca(quoted_val)
    assert resolved == os.path.abspath(str(cert_file))

    single_quoted_val = f"'{cert_file}'"
    resolved_single = resolve_ssl_ca(single_quoted_val)
    assert resolved_single == os.path.abspath(str(cert_file))

def test_resolve_ssl_ca_retains_explicit_path_when_not_on_disk():
    """Verify that an explicitly provided CA path is retained rather than silently dropped to None."""
    missing_path = "/etc/secrets/aiven-ca.pem"
    resolved = resolve_ssl_ca(missing_path)
    assert resolved == missing_path

def test_resolve_ssl_ca_auto_discovery_in_etc_secrets(tmp_path):
    """Verify auto-discovery of alternative CA certificate file names in /etc/secrets directory."""
    fake_secrets_dir = tmp_path / "secrets"
    fake_secrets_dir.mkdir()
    ca_file = fake_secrets_dir / "ca.pem"
    ca_file.write_text(SAMPLE_PEM_CERT, encoding="utf-8")

    orig_isfile = os.path.isfile
    orig_isdir = os.path.isdir
    mock_ca_file = os.path.normpath("/etc/secrets/ca.pem")
    mock_secrets_dir = os.path.normpath("/etc/secrets")

    with patch("os.path.isdir", side_effect=lambda d: os.path.normpath(d) == mock_secrets_dir or orig_isdir(d)), \
         patch("os.listdir", side_effect=lambda d: ["ca.pem"] if os.path.normpath(d) == mock_secrets_dir else os.listdir(d)), \
         patch("os.path.isfile", side_effect=lambda f: os.path.normpath(f) == mock_ca_file or orig_isfile(f)):
        
        # When user configured /etc/secrets/aiven-ca.pem but file is /etc/secrets/ca.pem
        resolved = resolve_ssl_ca("/etc/secrets/aiven-ca.pem")
        assert os.path.normpath(resolved) == mock_ca_file

def test_prepare_database_url_strips_all_ssl_query_params():
    """Verify all conflicting SSL query parameters are removed so connect_args has full control."""
    url = "mysql+pymysql://user:pass@sakhi-mysql-sakhiai.i.aivencloud.com:12345/defaultdb?ssl-mode=REQUIRED&ssl_mode=REQUIRED&ssl=true&ssl_disabled=false&ssl_ca=bad.pem&charset=utf8mb4"
    sanitized_url, connect_args = prepare_database_url_and_connect_args(db_url=url, ca_setting=SAMPLE_PEM_CERT)
    
    for key in ("ssl-mode", "ssl_mode", "ssl", "ssl_disabled", "ssl_ca", "ssl_verify_cert"):
        assert key not in sanitized_url.query
    assert sanitized_url.query.get("charset") == "utf8mb4"

def test_log_ssl_startup_diagnostic_safe_logging():
    """Verify diagnostic produces structured details and does not log credentials."""
    from app.database.database import log_ssl_startup_diagnostic

    with patch("app.core.config.settings.MYSQL_SSL_CA", "/etc/secrets/aiven-ca.pem"):
        diag = log_ssl_startup_diagnostic()
        assert diag["is_configured"] is True
        assert diag["ca_path"] == "/etc/secrets/aiven-ca.pem"
        assert "password" not in diag
        assert "database_url" not in diag
