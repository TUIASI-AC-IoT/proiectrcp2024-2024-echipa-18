# main.py - Broker MQTT5

`main.py` este fișierul principal al proiectului și implementează un broker MQTT5 simplu. Acesta gestionează conexiunile clienților prin TCP, autentificarea acestora și menține conexiunile active folosind mesaje `PINGREQ` și `PINGRESP`. Fișierul utilizează modulele auxiliare `sqlServer`, `decoder`, și `packet_creator` pentru a lucra cu baza de date și a procesa pachetele MQTT.

## Funcționalități principale

- Configurarea și pornirea unui server TCP care ascultă pe un IP și un port specific.
- Gestionarea conexiunilor multiple simultane ale clienților prin fire de execuție (threads).
- Decodarea pachetelor MQTT primite și gestionarea pachetelor de tip `CONNECT` și `PINGREQ`.
- Autentificarea clienților și stocarea acestora în baza de date folosind `SQLServer`.
- Răspuns cu pachete `CONNACK` și `PINGRESP` în funcție de cerințele MQTT5.
- Monitorizarea și actualizarea timpului de deconectare al clienților.

## Configurarea Serverului

În `main.py`, serverul este configurat să ruleze pe adresa IP `127.0.0.1` și portul `5000`. Aceste valori pot fi modificate la începutul fișierului:

```python
# Configurarea serverului
IP_ADDR = '127.0.0.1'  # Adresa IP a serverului (localhost în acest caz)
PORT = 5000  # Portul pe care serverul ascultă pentru conexiuni
```

## Utilizare

Pentru a porni serverul, rulează următoarea comandă:

```bash
python main.py
```

Serverul va începe să asculte pentru conexiuni și va permite până la 20 de clienți simultan. La fiecare conexiune nouă, serverul va crea un fir de execuție pentru a gestiona interacțiunile cu acel client.

## Funcții și Fluxul Programului

### Inițializarea Serverului

1. **Crearea socket-ului serverului**: Se creează un socket TCP, se configurează adresa și portul, iar serverul intră în modul de ascultare pentru conexiuni noi.
2. **Initializarea obiectelor globale**:
   - `active_connections`: Dictionar pentru stocarea conexiunilor active.
   - `db`: Obiect `SQLServer` pentru gestionarea bazei de date a clienților.
   - `decoder`: Obiect `MQTTDecoder` pentru decodificarea pachetelor MQTT.

### Funcția `handle_client(conn, addr)`

Această funcție gestionează comunicarea cu un client conectat, incluzând:
  
- **Recepționarea datelor**: Primește date de la client în blocuri de 512 bytes.
- **Decodarea pachetelor MQTT**: Decodifică pachetele primite de la client și identifică tipul acestora (`CONNECT`, `PINGREQ`).
- **Procesarea pachetelor CONNECT**:
  - Autentifică clientul și stochează informațiile în baza de date.
  - Creează și trimite un pachet `CONNACK` ca răspuns.
  - Adaugă clientul în `active_connections` dacă conexiunea este autorizată.
- **Procesarea pachetelor PINGREQ**:
  - Trimite un pachet `PINGRESP` pentru a confirma conexiunea și a o menține activă.
- **Gestionarea erorilor**: Dacă apare o eroare (timeout sau eroare de socket), conexiunea este închisă și eliminată din lista de conexiuni active.

### Deconectarea și Curățarea Conexiunii

Când un client se deconectează:
- Se actualizează ora de deconectare în baza de date.
- Conexiunea este eliminată din `active_connections`.
- Socket-ul este închis pentru a elibera resursele.

### Acceptarea Conexiunilor

Bucla principală din `main.py` acceptă conexiunile clienților și creează câte un fir de execuție pentru fiecare client nou, apelând funcția `handle_client` pentru gestionarea fiecărei conexiuni.

## Module și Funcții Utilizate

Acest fișier folosește următoarele module și funcții:
- **`SQLServer`**: Clasa din `sqlServer.py` care gestionează operațiile cu baza de date.
- **`MQTTDecoder`**: Clasa din `decoder.py` pentru decodificarea pachetelor MQTT.
- **`create_connack_packet`** și **`create_pingresp_packet`**: Funcții din `packet_creator.py` pentru crearea pachetelor de răspuns.

