import struct

class MQTTDecoder:
    def decode_mqtt_packet(self, data):
        # Extracts the packet type from the first byte
        packet_type = data[0] >> 4
        # Decodes the packet based on its type
        if packet_type == 1:  # CONNECT
            return self._decode_connect(data)
        elif packet_type == 12:  # PINGREQ
            return {"packet_type": "PINGREQ"}
        elif packet_type == 14:  # DISCONNECT
            return self._decode_disconnect(data)
        else:
            raise ValueError("Unsupported packet type (yet)")

    def _decode_remaining_length(self, data, index):
        # Decodes the variable length field for MQTT packets
        multiplier = 1
        value = 0
        while True:
            encoded_byte = data[index]
            index += 1
            value += (encoded_byte & 127) * multiplier
            if (encoded_byte & 128) == 0:  # Stop if the MSB is 0
                break
            multiplier *= 128
        return value, index

    def _decode_string(self, data, index):
        # Decodes a UTF-8 string from the data starting at index
        str_len = struct.unpack("!H", data[index:index + 2])[0]  # Read the length of the string
        index += 2
        return data[index:index + str_len].decode("utf-8"), index + str_len

    def _decode_properties(self, data, index):
        # Decodes properties field from MQTT packet, as defined by MQTT v5
        properties = {}
        prop_length, index = self._decode_remaining_length(data, index)  # Decode property length
        end_index = index + prop_length

        while index < end_index:
            prop_id = data[index]  # Property identifier
            index += 1

            # Specific property handling
            if prop_id == 17:  # Session Expiry Interval
                properties["session_expiry_interval"] = struct.unpack("!I", data[index:index + 4])[0]
                index += 4
            elif prop_id == 21:  # Authentication Method
                properties["authentication_method"], index = self._decode_string(data, index)

        return properties, index

    def _decode_connect(self, data):
        # Decodes a CONNECT packet
        remaining_length, index = self._decode_remaining_length(data, 1)  # Remaining length

        # Decode the protocol name
        protocol_name, index = self._decode_string(data, index)
        protocol_level = data[index]
        index += 1
        connect_flags = data[index]
        index += 1
        keep_alive = struct.unpack("!H", data[index:index + 2])[0]
        index += 2

        # Decode properties
        properties, index = self._decode_properties(data, index)

        # Decode Client ID
        client_id, index = self._decode_string(data, index)

        # Check for Username and Password in the flags
        username = None
        password = None
        if connect_flags & 0x80:  # Username flag (bit 7)
            username, index = self._decode_string(data, index)

        if connect_flags & 0x40:  # Password flag (bit 6)
            password, index = self._decode_string(data, index)

        # Extract the clean_session flag (bit 1 of connect_flags)
        clean_session = bool(connect_flags & 0x02)

        length = len(data)  # Total length of packet data

        # Return decoded packet data as a dictionary
        return {
            "packet_type": "CONNECT",
            "protocol_name": protocol_name,
            "protocol_level": protocol_level,
            "connect_flags": connect_flags,
            "clean_session": clean_session,
            "keep_alive": keep_alive,
            "properties": properties,
            "client_id": client_id,
            "username": username,
            "password": password,
            "length": length
        }

    def _decode_disconnect(self, data):
        # Decodes a DISCONNECT packet
        remaining_length, index = self._decode_remaining_length(data, 1)  # Remaining length

        # Decode properties if any are present
        properties = {}
        if remaining_length > 0:
            properties, _ = self._decode_properties(data, index)

        return {
            "packet_type": "DISCONNECT",
            "properties": properties
        }
