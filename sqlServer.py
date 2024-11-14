import sqlite3
from typing import Tuple
import hashlib
import threading
from datetime import datetime, timedelta

class SQLServer:
    def __init__(self, db_name="mqtt_server.db", SUPPORTED_MQTT_VERSION=5.0, MAX_CONNECTIONS=10, MIN_CONNECTION_INTERVAL=1, MAX_CLIENT_ID_LENGTH=23):
        # Initialize server parameters and set up database tables
        self.db_name = db_name
        self.SUPPORTED_MQTT_VERSION = SUPPORTED_MQTT_VERSION
        self.MAX_CONNECTIONS = MAX_CONNECTIONS
        self.MIN_CONNECTION_INTERVAL = MIN_CONNECTION_INTERVAL
        self.MAX_CLIENT_ID_LENGTH = MAX_CLIENT_ID_LENGTH
        self.lock = threading.Lock()  # Ensures thread-safe operations
        self.setup_tables()  # Create database tables if they don’t exist

    def _get_connection(self):
        # Create a new database connection for each thread
        return sqlite3.connect(self.db_name, check_same_thread=False)

    def setup_tables(self):
        # Set up the required database tables for storing client information
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # SQL command to create the clients table if it does not already exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id TEXT NOT NULL UNIQUE,
                    username TEXT,  -- Username associated with the client
                    password TEXT,  -- Hashed password for security
                    banned BOOLEAN DEFAULT 0,  -- Indicates if the client is banned
                    clean_session BOOLEAN DEFAULT 1,
                    connected BOOLEAN DEFAULT 0,
                    keep_alive INTEGER DEFAULT 60,
                    session_expiry INTEGER DEFAULT 0,  -- Expiry in seconds
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()  # Save changes to the database

    def store_client(self, decoded_packet: dict) -> Tuple[int, int]:
        """
        Tries to store and authenticate the client. Returns a tuple of (connect_ack_flags, reason_code).
        """
        client_id = decoded_packet.get("client_id")
        username = decoded_packet.get("username")
        password = decoded_packet.get("password")
        protocol_level = decoded_packet.get("protocol_level")
        packet_size = decoded_packet.get("length")

        # Reject if packet size exceeds maximum allowed limit
        if packet_size > 268435456:
            return (0x00, 0x95)  # Packet too large

        # Reject if MQTT protocol version is unsupported
        if protocol_level != self.SUPPORTED_MQTT_VERSION:
            return (0x00, 0x84)  # Unsupported Protocol Version

        # Check server availability and reject if unavailable
        if not self.is_server_available():
            return (0x00, 0x88)  # Server Unavailable

        # Reject if server is too busy to handle more connections
        if self.is_server_busy():
            return (0x00, 0x89)  # Server Busy

        # Reject if client is banned
        if self.is_client_banned(client_id):
            return (0x00, 0x8A)  # Client Banned

        # Reject if client is connecting too frequently
        if self.is_connection_rate_exceeded(client_id):
            return (0x00, 0x9F)  # Connection Rate Exceeded

        # Reject if client ID is invalid or too long
        if not client_id or len(client_id) > self.MAX_CLIENT_ID_LENGTH:
            return (0x00, 0x85)  # Client Identifier Not Valid

        # Store or authenticate client in the database
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT password, username FROM clients WHERE client_id = ?", (client_id,))
                existing_record = cursor.fetchone()

                # Validate username and password if client already exists
                if existing_record:
                    stored_password_hash = existing_record[0]
                    stored_username = existing_record[1]
                    provided_password_hash = hashlib.sha256(password.encode()).hexdigest() if password else None
                    if provided_password_hash != stored_password_hash or stored_username != username:
                        return (0x00, 0x86)  # Bad Username or Password

                # Hash password if provided
                password_hash = hashlib.sha256(password.encode()).hexdigest() if password else None

                # Insert or update client record in the database
                query = """
                INSERT INTO clients (client_id, username, password, session_expiry, keep_alive, connected)
                VALUES (?, ?, ?, ?, ?, 1)
                ON CONFLICT(client_id) DO UPDATE SET
                    username=excluded.username,
                    password=excluded.password,
                    connected=1,
                    session_expiry=excluded.session_expiry,
                    keep_alive=excluded.keep_alive,
                    last_seen=CURRENT_TIMESTAMP
                """
                cursor.execute(query, (client_id, username, password_hash, decoded_packet.get("session_expiry", 0), decoded_packet.get("keep_alive", 60)))
                conn.commit()  # Save changes to the database

                return (0x00, 0x00)  # Connection Success

        except sqlite3.IntegrityError as e:
            print(f"Error storing client '{client_id}': {e}")
            return (0x00, 0x87)  # Connection Refused, Not Authorized

    def is_server_available(self) -> bool:
        """Checks if server is available for new connections."""
        return True  # Placeholder for actual server status check

    def is_server_busy(self) -> bool:
        """Checks if server is busy, e.g., using a limit on active connections."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Query count of currently connected clients
                cursor.execute("SELECT COUNT(*) FROM clients WHERE connected = 1")
                active_connections = cursor.fetchone()[0]
                # Return True if active connections exceed max allowed connections
                return active_connections >= self.MAX_CONNECTIONS
        except sqlite3.Error as e:
            print(f"Error checking server busy status: {e}")
            return True

    def is_client_banned(self, client_id: str) -> bool:
        """Checks if a client is banned by querying the banned status from the clients table."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Query the banned status for the given client_id
                cursor.execute("SELECT banned FROM clients WHERE client_id = ?", (client_id,))
                result = cursor.fetchone()

                # Return True if the client is found and banned, otherwise False
                return result is not None and result[0] == 1

        except sqlite3.Error as e:
            print(f"Error checking banned status for client '{client_id}': {e}")
            # In case of an error, assume the client is not banned to avoid disruptions
            return False

    def is_connection_rate_exceeded(self, client_id: str) -> bool:
        """Checks if a client is connecting too frequently."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT last_seen FROM clients WHERE client_id = ?", (client_id,))
                last_seen_row = cursor.fetchone()

                # Allow connection if no last seen record exists
                if not last_seen_row or not last_seen_row[0]:
                    return False

                # Calculate time since last connection attempt
                last_seen_time = datetime.strptime(last_seen_row[0], "%Y-%m-%d %H:%M:%S")
                time_since_last_seen = (datetime.now() - last_seen_time).total_seconds()

                # Reject if connection interval is too short
                if time_since_last_seen < self.MIN_CONNECTION_INTERVAL:
                    print(f"Client '{client_id}' exceeded connection rate limit.")
                    return True

                # Update last seen time in the database
                cursor.execute("UPDATE clients SET last_seen = ? WHERE client_id = ?",
                               (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), client_id))
                conn.commit()  # Save changes to the database

                return False

        except sqlite3.Error as e:
            print(f"Error checking connection rate for client '{client_id}': {e}")
            return True
