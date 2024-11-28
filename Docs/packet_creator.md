# packet_creator.py - Creator de Pachete MQTT

`packet_creator.py` conține funcții pentru crearea pachetelor MQTT5 de tip `CONNACK`, `PINGRESP`, și `DISCONNECT`. Aceste pachete sunt utilizate pentru a răspunde clienților MQTT în funcție de solicitările și starea lor de conexiune.

## Funcționalități principale

- **Crearea pachetului CONNACK**: Trimite un pachet de confirmare a conexiunii către clientul care inițiază o conexiune MQTT.
- **Crearea pachetului PINGRESP**: Răspunde la pachetele PINGREQ trimise de client pentru a menține conexiunea activă.
- **Crearea pachetului DISCONNECT**: Trimite un pachet de deconectare pentru a încheia conexiunea cu un client, cu un cod de motiv opțional.

## Funcții

### `encode_remaining_length(length)`

Funcția encodează lungimea rămasă folosind codificarea cu lungime variabilă, așa cum specifică protocolul MQTT. Aceasta este folosită pentru câmpul `Remaining Length` din antetul fix al pachetelor.

- **Parametri**:
  - `length`: Lungimea de codificat.

- **Returnează**: Un `bytearray` care conține lungimea codificată.

### `create_connack_packet(...)`

Creează un pachet de tip `CONNACK`, folosit de server pentru a confirma conexiunea cu un client. Include un antet variabil cu indicatorii de confirmare și codul de motiv, urmat de un set de proprietăți opționale.

- **Parametri**:
  - `connect_ack_flags`: Indicatori de confirmare a conexiunii.
  - `reason_code`: Codul de motiv pentru confirmarea conexiunii.
  - `session_expiry_interval`: Interval de expirare a sesiunii (opțional).
  - `receive_maximum`: Numărul maxim de mesaje pe care serverul le poate trimite simultan către client (opțional).
  - `maximum_qos`: Nivelul maxim QoS suportat de server (opțional).
  - `retain_available`: Specifică dacă serverul suportă mesaje reținute (opțional).
  - `maximum_packet_size`: Dimensiunea maximă a pachetelor acceptate (implicit 256 MB).
  - `assigned_client_identifier`: ID-ul clientului asignat de server (opțional).
  - `server_keep_alive`: Timpul de menținere a conexiunii (opțional).
  - `response_information`: Informații pentru răspuns (opțional).
  - `server_reference`: Referința serverului pentru client (opțional).

- **Returnează**: Un `bytearray` care conține pachetul `CONNACK` complet.

### `create_pingresp_packet()`

Construiește un pachet de tip `PINGRESP`, care este un răspuns la `PINGREQ` primit de la client pentru a menține conexiunea activă.

- **Returnează**: Un `bytearray` care conține pachetul `PINGRESP`, cu o lungime de zero.

### `create_disconnect_packet(reason_code=0x00)`

Creează un pachet de tip `DISCONNECT`, utilizat de server pentru a încheia conexiunea cu clientul. Include un antet variabil cu un cod de motiv opțional.

- **Parametri**:
  - `reason_code`: Codul de motiv pentru deconectare (implicit 0x00).

- **Returnează**: Un `bytearray` care conține pachetul `DISCONNECT` complet.

## Exemplu de Utilizare

### Crearea unui pachet CONNACK

```python
from packet_creator import create_connack_packet

connack_packet = create_connack_packet(
    connect_ack_flags=0,
    reason_code=0,
    session_expiry_interval=60,
    receive_maximum=10,
    maximum_qos=1,
    retain_available=True,
    assigned_client_identifier="client123"
)
print(connack_packet)
```

### Crearea unui pachet PINGRESP

```python
from packet_creator import create_pingresp_packet

pingresp_packet = create_pingresp_packet()
print(pingresp_packet)
```

### Crearea unui pachet DISCONNECT

```python
from packet_creator import create_disconnect_packet

disconnect_packet = create_disconnect_packet(reason_code=0x04)
print(disconnect_packet)
```

## Descrierea Pachetelor

- **CONNACK**: Este folosit pentru a confirma conexiunea unui client. Conține `connect_ack_flags`, `reason_code`, și proprietăți opționale care detaliază capabilitățile serverului și setările de conexiune.
- **PINGRESP**: Este un pachet simplu, folosit pentru a răspunde la `PINGREQ` și a menține conexiunea activă.
- **DISCONNECT**: Închide conexiunea cu un client și poate include un cod de motiv pentru a specifica motivul deconectării.
