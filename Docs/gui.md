
# gui.py - Interfața Grafică pentru MQTT Broker

`gui.py` implementează o interfață grafică pentru administrarea brokerului MQTT. Interfața permite pornirea și oprirea serverului, monitorizarea conexiunilor active, vizualizarea mesajelor publicate și gestionarea abonaților la topicuri.

## Funcționalități Principale

### Pornirea și Oprirea Serverului
- **Butoane**:
  - **Start Server**: Inițiază serverul MQTT folosind clasa `MQTT5Server`.
  - **Stop Server**: Oprește serverul, eliberând resursele utilizate.
- **Implementare**: Utilizează un fir de execuție separat (`ServerThread`) pentru a rula serverul într-un mod non-blocant.

### Taburi 
Interfața este organizată în mai multe taburi pentru a oferi acces facil la diferite funcționalități:

#### 1. **Topic History**
- Afișează lista completă a topicurilor utilizate.
- Informații afișate:
  - Numele complet al topicului.
- **Refresh automat**: Datele sunt reîncărcate periodic.

#### 2. **Last 10 Messages**
- Permite selectarea unui topic și afișarea ultimelor 10 mesaje publicate pe acel topic.
- Informații afișate:
  - Timpul publicării.
  - Conținutul mesajului.

#### 3. **Connected Clients**
- Listează clienții conectați și abonamentele acestora.
- Structură:
  - Fiecare client este afișat ca un nod părinte.
  - Subnoduri: Topicurile la care este abonat clientul, inclusiv QoS.

#### 4. **Subscribed Clients**
- Prezintă clienții abonați la fiecare topic.
- Structură:
  - Fiecare topic este afișat ca un nod părinte.
  - Subnoduri: Clienții care sunt abonați la acel topic.

#### 5. **QoS 1/2 Messages**
- Afișează mesaje publicate cu QoS 1 și QoS 2.
- Informații afișate:
  - Topicul.
  - QoS.
  - Conținutul mesajului.
  - Timestamp.

## Metode Principale

### `start_server(self)`
Inițiază serverul și actualizează starea interfeței grafice.
- **Comportament**:
  - Blochează butonul **Start Server**.
  - Activează butonul **Stop Server**.

### `stop_server(self)`
Oprește serverul și resetează starea interfeței grafice.
- **Comportament**:
  - Blochează butonul **Stop Server**.
  - Activează butonul **Start Server**.

### `refresh_all_tabs(self)`
Reîncarcă periodic datele afișate în toate taburile.

### `load_topic_history(self)`
Interoghează baza de date pentru a obține lista completă a topicurilor.

### `fetch_last_messages(self)`
Obține ultimele 10 mesaje pentru un topic selectat de utilizator.

### `load_connected_clients(self)`
Interoghează baza de date pentru a obține lista clienților conectați și abonamentele acestora.

### `load_subscribed_clients(self)`
Interoghează baza de date pentru a obține lista topicurilor și clienții abonați la acestea.

### `load_qos_messages(self)`
Interoghează baza de date pentru a afișa mesaje publicate cu QoS 1 și 2.

## Exemplu de Utilizare

### Pornirea Serverului
1. Rulează comanda:
   ```bash
   python gui.py
   ```
2. Apasă butonul **Start Server**.

### Vizualizarea Mesajelor
1. Selectează tabul **Last 10 Messages**.
2. Introdu topicul dorit în câmpul de text.
3. Apasă **Fetch Messages** pentru a vizualiza ultimele 10 mesaje publicate.

### Monitorizarea Clienților
1. Selectează tabul **Connected Clients** pentru a vizualiza clienții conectați și abonamentele lor.
2. Selectează tabul **Subscribed Clients** pentru a vedea clienții abonați la fiecare topic.

### Oprirea Serverului
1. Apasă butonul **Stop Server**.
2. Verifică starea serverului în consola aplicației.
