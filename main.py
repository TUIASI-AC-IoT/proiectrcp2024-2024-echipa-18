import socket
import threading
from client import Client
from message import Message
from sqlServer import SQLServer
from decoder import MQTTDecoder
from message_dispatcher import MessageDispatcher
from packet_creator import (
    create_connack_packet,
    create_pingresp_packet,
    create_puback_packet,
    create_pubrec_packet,
    create_pubcomp_packet,
    create_suback_packet,
    create_unsuback_packet
)

# Server setup
IP_ADDR = '127.0.0.1'
PORT = 5000
s_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s_server.bind((IP_ADDR, PORT))
s_server.listen(50)
active_connections = {}
print(f"Server listening on {IP_ADDR}:{PORT}")
db = SQLServer("mqtt_server.db")
decoder = MQTTDecoder()
dispatcher = MessageDispatcher(db)

def handle_client(conn, addr):
    # Create a new SQLServer instance for this thread
    print(f"Connection accepted from {addr}")
    connected_client = None

    try:
        while True:
            try:
                data = conn.recv(512)
                if not data:
                    print(f"Client at {addr} disconnected")
                    break
                print(data)
                decoded_packet = decoder.decode_mqtt_packet(data)
                print(f"Decoded packet from {addr}: {decoded_packet}")

                # Handle CONNECT packet`
                if decoded_packet.get("packet_type") == "CONNECT":
                    # Store client in the database and handle authentication
                    ack_flags, reason_code = db.store_client(decoded_packet)
                    connack_packet = create_connack_packet(connect_ack_flags=ack_flags, reason_code=reason_code)
                    conn.sendall(connack_packet)  # Send the CONNACK response packet to the client

                    # If connection is successful (reason code 0x00), add to active connections
                    if reason_code == 0x00:
                        connected_client = Client(
                            decoded_packet.get("client_id"),
                            decoded_packet.get("username"),
                            decoded_packet.get("password"),
                            decoded_packet.get("clean_session"),
                            decoded_packet.get("keep_alive"),
                            0,
                            decoded_packet.get("will_flag")
                        )

                        active_connections[decoded_packet.get("client_id")] = conn
                        print(f"Client '{decoded_packet.get('client_id')}' connected successfully.")
                    else:
                        print(f"Connection failed with reason code 0x{reason_code:02X}")
                        break

                # Handle PINGREQ packet
                elif decoded_packet.get("packet_type") == "PINGREQ":
                    print(f"Received PINGREQ from client {addr}")
                    pingresp_packet = create_pingresp_packet()  # Create a PINGRESP packet
                    conn.sendall(pingresp_packet)
                    print(f"Sent PINGRESP to client {addr}")

                # Handle PUBLISH packet (QoS 0 and 1)
                elif decoded_packet.get("packet_type") == "PUBLISH" and decoded_packet.get("qos") != 2:
                    print(f"Received PUBLISH from client {addr}")
                    packet_id = decoded_packet.get("packet_identifier")
                    if packet_id is None and decoded_packet.get("qos") > 0:
                        print(f"Error: No packet identifier provided for QoS {decoded_packet.get('qos')}")
                        break

                    message = Message(
                        topic=decoded_packet.get("topic_name"),
                        payload=decoded_packet.get("payload"),
                        qos=decoded_packet.get("qos"),
                        retain=decoded_packet.get("retain"),
                        packet_id=packet_id
                    )

                    # Save the message and respond with PUBACK for QoS 1
                    if db.save_message(message):
                        if message.qos == 1:
                            puback_packet = create_puback_packet(packet_id)
                            conn.sendall(puback_packet)
                            print(f"Sent PUBACK to client '{connected_client.client_id}' for packet ID '{packet_id}'")
                        dispatcher.dispatch_message(message, active_connections)



                # Handle PUBLISH packet (QoS 2)
                elif decoded_packet.get("packet_type") == "PUBLISH" and decoded_packet.get("qos") == 2:
                    packet_id = decoded_packet.get("packet_identifier")
                    if packet_id is None:
                        print("Error: Packet ID is required for QoS 2")
                        break

                    message = Message(
                        topic=decoded_packet.get("topic_name"),
                        payload=decoded_packet.get("payload"),
                        qos=decoded_packet.get("qos"),
                        retain=decoded_packet.get("retain"),
                        packet_id=packet_id
                    )

                    if db.save_message(message):
                        pubrec_packet = create_pubrec_packet(packet_id)
                        conn.sendall(pubrec_packet)


                elif decoded_packet.get("packet_type") == "PUBREL":
                    packet_id = decoded_packet.get("packet_identifier")
                    if packet_id is not None:
                        pubcomp_packet = create_pubcomp_packet(packet_id)
                        conn.sendall(pubcomp_packet)
                        print(f"Sent PUBCOMP to client for packet ID '{packet_id}'")
                        message = db.retrieve_message_by_packet_id(packet_id)

                        if message:
                            dispatcher.dispatch_message(message, active_connections)
                        else:
                            print(f"No message found with packet ID '{packet_id}'")

                # For PUBREC and PUBCOMP
                elif decoded_packet.get("packet_type") == "PUBREC":
                    packet_id = decoded_packet.get("packet_identifier")
                    print(f"Processing PUBREC for packet ID {packet_id}")
                    with dispatcher.pending_acks_lock:
                        pubrec_event = dispatcher.pending_acks.get(packet_id)
                        if pubrec_event:
                            pubrec_event.set()  # Trigger the event for PUBREC
                            print(f"Set PUBREC event for packet ID {packet_id}")
                        else:
                            print(f"No matching PUBREC event found for packet ID {packet_id}")

                elif decoded_packet.get("packet_type") == "PUBCOMP":
                    packet_id = decoded_packet.get("packet_identifier")
                    print(f"Processing PUBCOMP for packet ID {packet_id}")
                    with dispatcher.pending_acks_lock:
                        pubcomp_event = dispatcher.pending_acks.get(packet_id)
                        if pubcomp_event:
                            pubcomp_event.set()  # Trigger the event for PUBCOMP
                            print(f"Set PUBCOMP event for packet ID {packet_id}")
                        else:
                            print(f"No matching PUBCOMP event found for packet ID {packet_id}")

                elif decoded_packet.get("packet_type") == "PUBACK":
                    print(dispatcher.pending_acks)
                    packet_id = decoded_packet.get("packet_identifier")
                    print(f"Processing PUBACK for packet ID {packet_id}")
                    with dispatcher.pending_acks_lock:
                        puback_event = dispatcher.pending_acks.get(packet_id)
                        if puback_event:
                            puback_event.set()  # Trigger the event for PUBACK
                            print(f"Set PUBACK event for packet ID {packet_id}")
                        else:
                            print(f"No matching PUBACK event found for packet ID {packet_id}")



                elif decoded_packet.get("packet_type") == "SUBSCRIBE":
                    packet_id = decoded_packet.get("packet_identifier")
                    topics = decoded_packet.get("topics")
                    return_codes = []
                    for topic in topics:
                        topic_filter = topic["topic_filter"]
                        qos = topic["subscription_options"] & 0x03
                        if db.save_subscription(connected_client.client_id, topic_filter, qos):
                            return_codes.append(qos)
                        else:
                            return_codes.append(0x80)
                    suback_packet = create_suback_packet(packet_id, return_codes)
                    conn.sendall(suback_packet)
                    print(f"Sent SUBACK '{suback_packet}' to client '{connected_client.client_id}' for packet ID '{packet_id}'")

                    # Fetch and dispatch retained messages for each subscribed topic
                    for topic in topics:
                        topic_filter = topic["topic_filter"]
                        retained_messages = db.return_last_retained_messages(topic_filter)

                        for retained_message in retained_messages:
                            dispatcher.dispatch_message(retained_message, {connected_client.client_id: conn})

                elif decoded_packet.get("packet_type") == "UNSUBSCRIBE":
                    packet_id = decoded_packet.get("packet_identifier")
                    topics = decoded_packet.get("topics")

                    for topic_filter in topics:
                        if db.remove_subscription(connected_client.client_id, topic_filter):
                            print(f"Unsubscribed client '{connected_client.client_id}' from topic '{topic_filter}'")
                        else:
                            print(f"Failed to unsubscribe client '{connected_client.client_id}' from topic '{topic_filter}'")

                    unsuback_packet = create_unsuback_packet(packet_id)
                    conn.sendall(unsuback_packet)
                    print(f"Sent UNSUBACK to client '{connected_client.client_id}' for packet ID '{packet_id}'")

                elif decoded_packet.get("packet_type") == "DISCONNECT":
                    if connected_client.clean_session:
                        db.remove_all_subscriptions_for_client(connected_client.client_id)
                        print(f"Deleted all subscriptions for client '{connected_client.client_id}'")
                    print(f"Disconnected from client {addr}")
                    db.update_disconnect_time(connected_client.client_id)
                    if connected_client and connected_client.client_id in active_connections:
                        active_connections.pop(connected_client.client_id, None)
                        print(f"Connection closed with {addr}")



            except socket.timeout:
                print(f"Connection to {addr} timed out")
                break
            except socket.error as e:
                print(f"Socket error with {addr}: {e}")
                break
            except Exception as e:
                print(f"Error processing packet from {addr}: {e}")
                break

    finally:
        if connected_client and connected_client.client_id in active_connections:
            active_connections.pop(connected_client.client_id, None)
            print(f"Connection closed with {addr}")

        if connected_client and connected_client.client_id:
            db.update_disconnect_time(connected_client.client_id)
            if connected_client.isLastWill:
                last_will = db.retrieve_last_will(connected_client.client_id)
                will_message = Message(
                    topic=last_will["topic"],
                    payload=last_will["message"],
                    qos=last_will["qos"],
                    retain=last_will["retain"],
                    packet_id=None  # No specific packet ID for LWT
                )
                if db.save_message(will_message):
                    print(f"Saving message which was used as last will in the messages table")
                dispatcher.dispatch_message(will_message, active_connections)
                print(f"Dispatched Last Will for client '{connected_client.client_id}'")
                if db.remove_last_will(connected_client.client_id):
                    print(f"Removed Last Will for client '{connected_client.client_id}'")
                print(f"Updated disconnect time for client '{connected_client.client_id}'")

                if connected_client.clean_session:
                    if db.remove_all_subscriptions_for_client(connected_client.client_id):
                        print(f"Removed all subscriptions for client '{connected_client.client_id}', as per clean session")
        conn.close()


while True:
    s_conn, client_addr = s_server.accept()
    client_thread = threading.Thread(target=handle_client, args=(s_conn, client_addr))
    client_thread.start()
