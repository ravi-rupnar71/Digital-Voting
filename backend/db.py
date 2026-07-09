import mysql.connector
from mysql.connector import IntegrityError as MySQLIntegrityError

from .config import DB_CONFIG


INTEGRITY_ERRORS = (MySQLIntegrityError,)


class CursorWrapper:
    def __init__(self, cursor, dictionary=False):
        self._cursor = cursor
        self._dictionary = dictionary

    def execute(self, operation, params=()):
        self._cursor.execute(operation, params)
        return self

    def executemany(self, operation, seq_of_params):
        self._cursor.executemany(operation, seq_of_params)
        return self

    def fetchone(self):
        row = self._cursor.fetchone()
        if self._dictionary and row is not None and hasattr(row, "keys"):
            return dict(row)
        return row

    def fetchall(self):
        rows = self._cursor.fetchall()
        if self._dictionary:
            return [dict(row) if row is not None and hasattr(row, "keys") else row for row in rows]
        return rows

    def close(self):
        return self._cursor.close()

    def __getattr__(self, item):
        return getattr(self._cursor, item)


class ConnectionWrapper:
    def __init__(self, connection):
        self._connection = connection

    def cursor(self, dictionary=False):
        cursor = self._connection.cursor(dictionary=dictionary)
        return CursorWrapper(cursor, dictionary=dictionary)

    def commit(self):
        return self._connection.commit()

    def close(self):
        return self._connection.close()

    def __getattr__(self, item):
        return getattr(self._connection, item)


def get_db_connection():
    conn = mysql.connector.connect(**DB_CONFIG)
    return ConnectionWrapper(conn)


def ensure_column(conn, table_name, column_name, column_definition):
    cursor = conn.cursor()
    cursor.execute(f"SHOW COLUMNS FROM `{table_name}` LIKE %s", (column_name,))
    if cursor.fetchone() is None:
        cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN {column_definition}")
    cursor.close()


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            party VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) DEFAULT '',
            votes INT NOT NULL DEFAULT 0,
            is_verified INT NOT NULL DEFAULT 0,
            verification_otp VARCHAR(10) DEFAULT '',
            verification_expires_at VARCHAR(255) DEFAULT ''
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voters (
            id INT AUTO_INCREMENT PRIMARY KEY,
            voter_id VARCHAR(255) NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            has_voted INT NOT NULL DEFAULT 0,
            is_verified INT NOT NULL DEFAULT 0,
            verification_otp VARCHAR(10) DEFAULT '',
            verification_expires_at VARCHAR(255) DEFAULT ''
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            voter_id VARCHAR(255) NOT NULL,
            candidate_id INT NOT NULL,
            UNIQUE(voter_id, candidate_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL DEFAULT 'admin@example.com'
        )
    """)

    ensure_column(conn, "candidates", "password", "`password` VARCHAR(255) DEFAULT ''")
    ensure_column(conn, "candidates", "is_verified", "is_verified INT NOT NULL DEFAULT 0")
    ensure_column(conn, "candidates", "verification_otp", "verification_otp VARCHAR(10) DEFAULT ''")
    ensure_column(conn, "candidates", "verification_expires_at", "verification_expires_at VARCHAR(255) DEFAULT ''")
    ensure_column(conn, "voters", "is_verified", "is_verified INT NOT NULL DEFAULT 0")
    ensure_column(conn, "voters", "verification_otp", "verification_otp VARCHAR(10) DEFAULT ''")
    ensure_column(conn, "voters", "verification_expires_at", "verification_expires_at VARCHAR(255) DEFAULT ''")
    ensure_column(conn, "admin", "email", "email VARCHAR(255) NOT NULL DEFAULT 'admin@example.com'")

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM admin WHERE username = %s", ("admin",))
    admin_user = cursor.fetchone()

    if admin_user is None:
        cursor.execute(
            "INSERT INTO admin (username, password, email) VALUES (%s, %s, %s)",
            ("admin", "admin123", "admin@example.com"),
        )
    else:
        password_value = admin_user["password"] if isinstance(admin_user, dict) else admin_user[2]
        if password_value != "admin123":
            cursor.execute(
                "UPDATE admin SET password = %s WHERE id = %s",
                ("admin123", admin_user["id"] if isinstance(admin_user, dict) else admin_user[0]),
            )

    conn.commit()
    cursor.close()
    conn.close()


def reset_votes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE candidates SET votes = 0")
    cursor.execute("UPDATE voters SET has_voted = 0")
    cursor.execute("DELETE FROM votes")
    conn.commit()
    cursor.close()
    conn.close()
