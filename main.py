import socket
import threading
from sqlServer import SQLServer
from decoder import MQTTDecoder
from packet_creator import (
    create_connack_packet,
    create_pingresp_packet,
)

# Server configuration
IP_ADDR = '127.0.0.1'  # IP address to host the server on (localhost in this case)
PORT = 5000  # Port number to listen for incoming connections

# Initialize the server socket
s_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s_server.bind((IP_ADDR, PORT))
s_server.listen(20)  # Server listens for up to 20 incoming connections at once

# Global dictionaries and objects
active_connections = {}  # Stores active client connections by client_id
print(f"Server listening on {IP_ADDR}:{PORT}")
db = SQLServer("mqtt_server.db")  # Initializes SQLServer instance for database operations
decoder = MQTTDecoder()  # Initializes MQTT packet decoder


def handle_client(conn, addr):
    """
    Handles communication with a connected client.

    Parameters:
        conn (socket.socket): Client's connection socket.
        addr (tuple): Address of the connected client.
    """
    print(f"Connection accepted from {addr}")
    connected_client = None  # Holds the connected client's information once authenticated

    try:
        # Main loop to handle incoming data from the client
        while True:
            try:
                data = conn.recv(512)  # Receives up to 512 bytes of data from the client
                if not data:
                    print(f"Client at {addr} disconnected")
                    break  # Exit loop if no data is received, meaning client disconnected

                # Decode the MQTT packet received from the client
                decoded_packet = decoder.decode_mqtt_packet(data)
                print(f"Decoded packet from {addr}: {decoded_packet}")

                # Handle CONNECT packet type
                if decoded_packet.get("packet_type") == "CONNECT":
                    # Authenticate and store the client in the database
                    ack_flags, reason_code = db.store_client(decoded_packet)
                    connack_packet = create_connack_packet(connect_ack_flags=ack_flags, reason_code=reason_code)
                    conn.sendall(connack_packet)  # Send the CONNACK response packet to the client

                    # If connection is successful (reason code 0x00), add to active connections
                    if reason_code == 0x00:
                        active_connections[decoded_packet.get("client_id")] = conn
                        print(f"Client '{decoded_packet.get('client_id')}' connected successfully.")
                    else:
                        print(f"Connection failed with reason code 0x{reason_code:02X}")

                # Handle PINGREQ packet type (keep-alive message from the client)
                elif decoded_packet.get("packet_type") == "PINGREQ":
                    print(f"Received PINGREQ from client {addr}")
                    pingresp_packet = create_pingresp_packet()  # Create a PINGRESP packet
                    conn.sendall(pingresp_packet)  # Respond with PINGRESP to maintain connection
                    print(f"Sent PINGRESP to client {addr}")

            except socket.timeout:
                print(f"Connection to {addr} timed out")
                break  # Close connection if a timeout occurs
            except socket.error as e:
                print(f"Socket error with {addr}: {e}")
                break  # Handle any socket-related error
            except Exception as e:
                print(f"Error processing packet from {addr}: {e}")
                break  # Handle any other unexpected error

    finally:
        # Cleanup actions when a client disconnects
        if connected_client and connected_client.client_id:
            db.update_disconnect_time(connected_client.client_id)  # Update disconnect time in the database
            print(f"Updated disconnect time for client '{connected_client.client_id}'")
        conn.close()  # Close the client connection
        if connected_client and connected_client.client_id in active_connections:
            active_connections.pop(connected_client.client_id, None)  # Remove from active connections
        print(f"Connection closed with {addr}")


# Main loop to accept incoming client connections
while True:
    s_conn, client_addr = s_server.accept()  # Accept a new client connection
    # Start a new thread to handle the connected client
    client_thread = threading.Thread(target=handle_client, args=(s_conn, client_addr))
    client_thread.start()
