
# decoder.py - Decodor pentru Pachete MQTT

`decoder.py` implementează clasa `MQTTDecoder`, care decodifică pachetele MQTT5 primite, extrăgând informații esențiale din pachete de tip `CONNECT`, `PINGREQ`, și `DISCONNECT`. Această clasă este esențială pentru procesarea datelor primite de la clienți în cadrul unui broker MQTT.

## Funcționalități principale

- **Decodificarea pachetelor CONNECT**: Extrage informații precum numele protocolului, nivelul protocolului, ID-ul clientului, username, parola, și proprietăți specifice MQTT5.
- **Gestionarea pachetelor PINGREQ și DISCONNECT**: Identifică aceste tipuri de pachete și extrage proprietăți, acolo unde sunt disponibile.
- **Decodificarea câmpurilor de lungime variabilă și a șirurilor de caractere**: Asigură interpretarea corectă a câmpurilor cu lungime variabilă, conform specificațiilor MQTT.

## Metode

### `decode_mqtt_packet(self, data)`

Aceasta este metoda principală pentru decodificarea pachetelor MQTT. Determină tipul de pachet și apelează metoda corespunzătoare de decodificare.

- **Parametri**:
  - `data`: Datele brute ale pachetului MQTT în format `bytes`.
  
- **Returnează**: Un dicționar cu datele decodate ale pachetului, inclusiv tipul pachetului (`CONNECT`, `PINGREQ`, sau `DISCONNECT`).

### `_decode_remaining_length(self, data, index)`

Decodifică câmpul de lungime variabilă specific MQTT, folosit în pachetele MQTT pentru a indica lungimea părții variabile a pachetului.

- **Parametri**:
  - `data`: Datele brute ale pachetului.
  - `index`: Indexul de la care începe decodificarea lungimii.

- **Returnează**: Un tuple cu lungimea decodificată și noul index în datele pachetului.

### `_decode_string(self, data, index)`

Decodifică un șir UTF-8 din pachetul MQTT, pornind de la un index specificat.

- **Parametri**:
  - `data`: Datele brute ale pachetului.
  - `index`: Indexul de la care începe decodificarea șirului.

- **Returnează**: Un tuple cu șirul decodat și noul index.

### `_decode_properties(self, data, index)`

Decodifică secțiunea de proprietăți din pachetul MQTT5, conform standardului. Proprietățile pot include, de exemplu, `session_expiry_interval` și `authentication_method`.

- **Parametri**:
  - `data`: Datele brute ale pachetului.
  - `index`: Indexul de la care începe secțiunea de proprietăți.

- **Returnează**: Un tuple cu un dicționar al proprietăților decodate și noul index.

### `_decode_connect(self, data)`

Decodifică pachetele de tip `CONNECT`, extrăgând informații despre protocol, nivelul protocolului, ID-ul clientului, username, parola, și alte proprietăți. 

- **Parametri**:
  - `data`: Datele brute ale pachetului `CONNECT`.

- **Returnează**: Un dicționar cu datele decodate ale pachetului `CONNECT`.

### `_decode_disconnect(self, data)`

Decodifică pachetele de tip `DISCONNECT`, incluzând secțiunea de proprietăți, dacă aceasta este prezentă.

- **Parametri**:
  - `data`: Datele brute ale pachetului `DISCONNECT`.

- **Returnează**: Un dicționar cu datele decodate ale pachetului `DISCONNECT`.

## Exemplu de utilizare

```python
from decoder import MQTTDecoder

# Instanțierea decodorului
decoder = MQTTDecoder()

# Exemplu de pachet CONNECT primit (în format bytes)
data = b'\x10\x13\x00\x04MQTT\x05\x02\x00<\x00\x05my_id\x00\x06myuser\x00\x08mypassword'

# Decodificarea pachetului
decoded_packet = decoder.decode_mqtt_packet(data)
print(decoded_packet)
```

## Dicționarul decodat al unui pachet `CONNECT`

Un pachet `CONNECT` decodat arată astfel:

```python
{
    "packet_type": "CONNECT",
    "protocol_name": "MQTT",
    "protocol_level": 5,
    "connect_flags": 2,
    "clean_session": True,
    "keep_alive": 60,
    "properties": {
        "session_expiry_interval": 0,  # exemplu de proprietate
    },
    "client_id": "my_id",
    "username": "myuser",
    "password": "mypassword",
    "length": 19
}
```

Acest exemplu oferă o privire de ansamblu asupra informațiilor extrase și a structurii pachetului decodat.

## Erori de Decodare

Dacă este întâlnit un tip de pachet neacceptat, metoda `decode_mqtt_packet` va arunca o excepție `ValueError` cu mesajul "Unsupported packet type (yet)".

