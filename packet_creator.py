import struct

def encode_remaining_length(length):
    # Encodes the remaining length for an MQTT packet using variable-length encoding.
    encoded = bytearray()
    while True:
        byte = length % 128
        length //= 128
        # Set the continuation bit (MSB) if more bytes are needed
        if length > 0:
            byte |= 0x80
        encoded.append(byte)
        # Break if the entire length has been encoded
        if length == 0:
            break
    return encoded

def create_connack_packet(
        connect_ack_flags=0,
        reason_code=0,
        session_expiry_interval=None,
        receive_maximum=None,
        maximum_qos=None,
        retain_available=None,
        maximum_packet_size=268435456, # 256 MB default
        assigned_client_identifier=None,
        server_keep_alive=None,
        response_information=None,
        server_reference=None
):
    # Set the packet type for CONNACK
    packet_type = 0x20  # CONNACK packet type

    # Variable header includes connect acknowledgment flags and reason code
    variable_header = bytes([connect_ack_flags, reason_code])

    # Properties for the CONNACK packet
    properties = bytearray()

    # Encode each property if provided
    if session_expiry_interval is not None:
        properties.extend([0x11])  # Property identifier for session expiry interval
        properties.extend(session_expiry_interval.to_bytes(4, 'big'))

    if receive_maximum is not None:
        properties.extend([0x21])  # Property identifier for receive maximum
        properties.extend(receive_maximum.to_bytes(2, 'big'))

    if maximum_qos is not None:
        properties.extend([0x24])  # Property identifier for maximum QoS
        properties.append(maximum_qos)

    if retain_available is not None:
        properties.extend([0x25])  # Property identifier for retain available
        properties.append(1 if retain_available else 0)

    if maximum_packet_size is not None:
        properties.extend([0x27])  # Property identifier for maximum packet size
        properties.extend(maximum_packet_size.to_bytes(4, 'big'))

    if assigned_client_identifier is not None:
        properties.extend([0x12])  # Property identifier for assigned client identifier
        identifier_bytes = assigned_client_identifier.encode('utf-8')
        properties.extend(len(identifier_bytes).to_bytes(2, 'big'))
        properties.extend(identifier_bytes)

    if server_keep_alive is not None:
        properties.extend([0x13])  # Property identifier for server keep alive
        properties.extend(server_keep_alive.to_bytes(2, 'big'))

    if response_information is not None:
        properties.extend([0x1A])  # Property identifier for response information
        response_bytes = response_information.encode('utf-8')
        properties.extend(len(response_bytes).to_bytes(2, 'big'))
        properties.extend(response_bytes)

    if server_reference is not None:
        properties.extend([0x1C])  # Property identifier for server reference
        reference_bytes = server_reference.encode('utf-8')
        properties.extend(len(reference_bytes).to_bytes(2, 'big'))
        properties.extend(reference_bytes)

    # Add property length to the start of the properties section
    properties_length = encode_remaining_length(len(properties))
    properties = properties_length + properties

    # Calculate Remaining Length for the packet
    remaining_length = len(variable_header) + len(properties)
    fixed_header = bytearray([packet_type]) + encode_remaining_length(remaining_length)

    # Combine Fixed Header, Variable Header, and Properties to form the complete packet
    return fixed_header + variable_header + properties

def create_pingresp_packet():
    # Constructs a PINGRESP packet with zero remaining length
    return bytearray([0xD0, 0x00])  # PINGRESP packet type with zero remaining length

def create_disconnect_packet(reason_code=0x00):
    # Set the packet type for DISCONNECT
    packet_type = 0xE0  # DISCONNECT packet type
    # Variable header includes only the reason code
    variable_header = bytes([reason_code])

    # Calculate Remaining Length for the packet
    remaining_length = len(variable_header)
    fixed_header = bytearray([packet_type]) + encode_remaining_length(remaining_length)

    # Combine Fixed Header and Variable Header to form the complete packet
    return fixed_header + variable_header
