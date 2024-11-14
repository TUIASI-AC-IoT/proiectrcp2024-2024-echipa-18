# sqlServer.py - SQL Server pentru Gestionarea Clienților MQTT

`sqlServer.py` este un modul care implementează clasa `SQLServer`, utilizată pentru a gestiona baza de date SQLite a clienților care se conectează la un server MQTT5. Acest modul gestionează operații precum autentificarea clienților, gestionarea ratei de conexiune, verificarea restricțiilor și păstrarea datelor despre clienți.

## Funcționalități principale

- **Inițializarea și configurarea bazei de date**: Creează automat tabelele necesare dacă acestea nu există deja.
- **Stocarea și autentificarea clienților**: Stochează informațiile despre clienți și gestionează verificarea acreditărilor de autentificare.
- **Verificarea ratei de conexiune și a limitelor de conexiuni**: Impune limite pe baza frecvenței conexiunilor și a numărului maxim de conexiuni simultane.
- **Verificarea restricțiilor**: Verifică dacă un client este interzis să se conecteze.

## Metode

### `__init__(self, db_name="mqtt_server.db", SUPPORTED_MQTT_VERSION=5.0, MAX_CONNECTIONS=10, MIN_CONNECTION_INTERVAL=1, MAX_CLIENT_ID_LENGTH=23)`

Constructorul clasei `SQLServer` inițializează parametrii serverului și creează tabelele bazei de date dacă acestea nu există.

- **Parametri**:
  - `db_name`: Numele fișierului bazei de date SQLite.
  - `SUPPORTED_MQTT_VERSION`: Versiunea MQTT acceptată de server.
  - `MAX_CONNECTIONS`: Numărul maxim de conexiuni simultane permise.
  - `MIN_CONNECTION_INTERVAL`: Intervalul minim între conexiuni succesive (în secunde).
  - `MAX_CLIENT_ID_LENGTH`: Lungimea maximă permisă a identificatorului clientului.

### `_get_connection(self)`

Creează o conexiune nouă la baza de date SQLite. Este utilizată pentru a asigura o conexiune independentă per fir de execuție.

### `setup_tables(self)`

Creează tabelul `clients` în baza de date dacă acesta nu există. Tabelul include câmpuri pentru `client_id`, `username`, `password`, și diverse alte atribute ale clientului, cum ar fi timpul ultimei conectări (`last_seen`) și statutul de interdicție (`banned`).

### `store_client(self, decoded_packet: dict) -> Tuple[int, int]`

Încearcă să stocheze și să autentifice un client în baza de date. Returnează un tuple cu `connect_ack_flags` și `reason_code`, indicând succesul sau eșecul autentificării.

- **Parametri**:
  - `decoded_packet`: Un dicționar ce conține informațiile decodate ale pachetului MQTT, cum ar fi `client_id`, `username`, `password`, și `protocol_level`.

- **Returnează**: Un tuple `(connect_ack_flags, reason_code)` care indică dacă autentificarea a fost reușită sau de ce a eșuat.

### `is_server_available(self) -> bool`

Verifică dacă serverul este disponibil pentru conexiuni noi. (În prezent, este doar un punct de control, dar poate fi extins pentru a verifica alte criterii de disponibilitate.)

### `is_server_busy(self) -> bool`

Verifică dacă serverul a atins limita de conexiuni simultane (`MAX_CONNECTIONS`).

- **Returnează**: `True` dacă numărul de conexiuni active este egal sau mai mare decât `MAX_CONNECTIONS`, altfel `False`.

### `is_client_banned(self, client_id: str) -> bool`

Verifică dacă un client este interzis să se conecteze. Consultă statutul de interdicție din baza de date.

- **Parametri**:
  - `client_id`: Identificatorul clientului.

- **Returnează**: `True` dacă clientul este interzis, `False` în caz contrar.

### `is_connection_rate_exceeded(self, client_id: str) -> bool`

Verifică dacă un client se conectează prea frecvent, conform intervalului minim de conexiune (`MIN_CONNECTION_INTERVAL`).

- **Parametri**:
  - `client_id`: Identificatorul clientului.

- **Returnează**: `True` dacă clientul a depășit limita de frecvență a conexiunilor, `False` în caz contrar.

## Structura Tabelului `clients`

Tabelul `clients` include următoarele câmpuri:

- **`id`**: ID unic, auto-incrementat pentru fiecare client.
- **`client_id`**: Identificator unic al clientului (unic în baza de date).
- **`username`**: Numele de utilizator asociat clientului.
- **`password`**: Parola clientului, stocată ca hash pentru securitate.
- **`banned`**: Boolean, indică dacă clientul este interzis.
- **`clean_session`**: Boolean, specifică dacă clientul utilizează sesiuni curate.
- **`connected`**: Boolean, indică dacă clientul este conectat în prezent.
- **`keep_alive`**: Intervalul de păstrare a conexiunii.
- **`session_expiry`**: Durata de expirare a sesiunii (în secunde).
- **`last_seen`**: Data și ora ultimei activități a clientului.

## Exemple de utilizare

### Crearea unei instanțe de `SQLServer`

```python
from sqlServer import SQLServer

db = SQLServer("mqtt_server.db")
```

### Autentificarea și stocarea unui client

```python
decoded_packet = {
    "client_id": "client123",
    "username": "user123",
    "password": "pass123",
    "protocol_level": 5.0,
    "length": 256
}
ack_flags, reason_code = db.store_client(decoded_packet)
print(f"Ack flags: {ack_flags}, Reason code: {reason_code}")
```

### Verificarea dacă un client este interzis

```python
client_id = "client123"
is_banned = db.is_client_banned(client_id)
print(f"Clientul {client_id} este interzis: {is_banned}")
```

### Verificarea ratei de conexiune a unui client

```python
client_id = "client123"
rate_exceeded = db.is_connection_rate_exceeded(client_id)
print(f"Clientul {client_id} a depășit rata de conexiune: {rate_exceeded}")
```
