# MQTT5 Broker

Acest proiect implementează un broker MQTT5 simplu care gestionează conexiunile clienților, autentificarea și menținerea conexiunilor printr-un server SQL pentru stocarea datelor clientului. Codul este structurat în mai multe module, fiecare având funcționalități specifice pentru decodificarea și crearea pachetelor MQTT, precum și gestionarea conexiunilor și autentificării.

## Structura Proiectului

### Fișierele Principale

- **`main.py`**: Punctul de intrare al serverului MQTT5 Broker. Configurează serverul, acceptă conexiunile și gestionează interacțiunea cu clienții.
  - [Explicație detaliată pentru `main.py`](Docs/main.md)

- **`sqlServer.py`**: Modulul care gestionează operațiile legate de baza de date, incluzând autentificarea, stocarea și actualizarea informațiilor despre clienți în baza de date SQLite.
  - [Explicație detaliată pentru `sqlServer.py`](Docs/sqlServer.md)

- **`decoder.py`**: Implementează clasa `MQTTDecoder`, care este utilizată pentru decodificarea pachetelor MQTT primite de la clienți, cum ar fi `CONNECT`, `PINGREQ` și `DISCONNECT`.
  - [Explicație detaliată pentru `decoder.py`](Docs/decoder.md)

- **`packet_creator.py`**: Conține funcțiile necesare pentru crearea pachetelor MQTT, cum ar fi `CONNACK`, `PINGRESP` și `DISCONNECT`, ce sunt trimise ca răspuns către clienți.
  - [Explicație detaliată pentru `packet_creator.py`](Docs/packet_creator.md)

## Cerințe

- Python 3.x
- Biblioteca `socket` (inclusă nativ în Python)
- Biblioteca `struct` (inclusă nativ în Python)

## Configurare Server

Serverul este configurat să ruleze pe adresa IP `127.0.0.1` (localhost) și pe portul `5000`. Aceste valori pot fi modificate în fișierul `main.py`.

## Utilizare

1. **Pornirea Serverului**:
   Pentru a porni serverul MQTT5 Broker, rulează comanda:
   ```bash
   python main.py
   ```
   Serverul va începe să asculte pe adresa IP și portul specificate și va accepta până la 20 de conexiuni simultane de la clienți.

2. **Gestionarea Conexiunilor Clientului**:
   - Clienții se conectează la server folosind protocolul MQTT5.
   - La primirea unui pachet `CONNECT`, serverul verifică dacă clientul este valid și creează un răspuns `CONNACK`.
   - Dacă un client trimite un `PINGREQ`, serverul răspunde cu un pachet `PINGRESP` pentru a menține conexiunea activă.

3. **Funcționalități Adiționale**:
   - Serverul utilizează o bază de date SQLite pentru a stoca și a autentifica clienții.
   - La deconectarea unui client, serverul actualizează ora de deconectare în baza de date și elimină clientul din lista de conexiuni active.

## Detalii Despre Module

### main.py

`main.py` este punctul principal al aplicației și gestionează conexiunile clienților folosind socket-uri și fire de execuție. Mai multe informații pot fi găsite în [documentația pentru `main.py`](Docs/main.md).

### sqlServer.py

`sqlServer.py` definește clasa `SQLServer` pentru interacțiunea cu baza de date. Acest modul gestionează autentificarea și păstrarea informațiilor despre clienți, inclusiv ora ultimei deconectări. Documentația detaliată se găsește [aici](Docs/sqlServer.md).

### decoder.py

`decoder.py` implementează clasa `MQTTDecoder` pentru decodificarea pachetelor MQTT. Aceasta interpretează pachetele primite de tip `CONNECT`, `PINGREQ` și `DISCONNECT`. Pentru o explicație detaliată, vizitează [documentația `decoder.py`](Docs/decoder.md).

### packet_creator.py

`packet_creator.py` conține funcții pentru crearea pachetelor MQTT, inclusiv:
- **`create_connack_packet`**: Creează un pachet de tip `CONNACK` pentru a confirma conexiunea cu clientul.
- **`create_pingresp_packet`**: Creează un pachet `PINGRESP` pentru a menține sesiunea activă.
- **`create_disconnect_packet`**: Creează un pachet `DISCONNECT` pentru a informa clientul că a fost deconectat.

Mai multe detalii pot fi găsite în [documentația `packet_creator.py`](Docs/packet_creator.md).

Mai multe detalii referitor la îtnregul proiect pot fi găsite în [`documentația oficiala`(Documentatie Broker MQTT.pdf).
