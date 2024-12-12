import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QTabWidget, QListWidget, QListWidgetItem, QTextEdit, QHBoxLayout,
    QPushButton, QLineEdit, QTreeWidget, QTreeWidgetItem, QHeaderView
)
from PyQt5.QtCore import QTimer, QThread
import sqlite3
from datetime import datetime
from server import MQTT5Server

class ServerThread(QThread):
    def __init__(self, server_instance):
        super().__init__()
        self.server_instance = server_instance

    def run(self):
        self.server_instance.server_start()

class MQTTGUI(QMainWindow):
    def __init__(self, db_name="mqtt_server.db"):
        super().__init__()
        self.db_name = db_name
        self.setWindowTitle("MQTT Broker Dashboard")
        self.setGeometry(100, 100, 1000, 600)

        self.server_instance = MQTT5Server()
        self.server_thread = None

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.topic_history_tab = QWidget()
        self.last_messages_tab = QWidget()
        self.connected_clients_tab = QWidget()  # New Tab
        self.subscribed_clients_tab = QWidget()
        self.qos_messages_tab = QWidget()

        self.tabs.addTab(self.topic_history_tab, "Topic History")
        self.tabs.addTab(self.last_messages_tab, "Last 10 Messages")
        self.tabs.addTab(self.connected_clients_tab, "Connected Clients")  # Add the new tab
        self.tabs.addTab(self.subscribed_clients_tab, "Subscribed Clients")
        self.tabs.addTab(self.qos_messages_tab, "QoS 1/2 Messages")

        self.init_topic_history_tab()
        self.init_last_messages_tab()
        self.init_connected_clients_tab()  # Initialize the new tab
        self.init_subscribed_clients_tab()
        self.init_qos_messages_tab()

        self.init_server_controls()

        # Set up timers for refreshing data
        self.refresh_interval = 5000  # milliseconds
        self.setup_timers()

    def _get_connection(self):
        return sqlite3.connect(self.db_name)

    def setup_timers(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_all_tabs)
        self.timer.start(self.refresh_interval)

    def refresh_all_tabs(self):
        self.load_topic_history()
        self.load_connected_clients()  # Refresh connected clients
        self.load_subscribed_clients()
        self.load_qos_messages()

    # Server Controls
    def init_server_controls(self):
        control_layout = QHBoxLayout()

        self.start_server_button = QPushButton("Start Server")
        self.start_server_button.clicked.connect(self.start_server)

        self.stop_server_button = QPushButton("Stop Server")
        self.stop_server_button.clicked.connect(self.stop_server)
        self.stop_server_button.setEnabled(False)

        control_layout.addWidget(self.start_server_button)
        control_layout.addWidget(self.stop_server_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(control_layout)
        self.server_control_widget = QWidget()
        self.server_control_widget.setLayout(main_layout)

        self.tabs.addTab(self.server_control_widget, "Server Controls")

    def start_server(self):
        if not self.server_thread or not self.server_thread.isRunning():
            self.server_instance.shutdown_event.clear()
            self.server_thread = ServerThread(self.server_instance)

            self.server_thread.start()

            self.start_server_button.setEnabled(False)

            self.stop_server_button.setEnabled(True)

    def stop_server(self):
        if self.server_thread and self.server_thread.isRunning():
            #self.server_instance.server_stop()
            #self.server_thread.wait()
            #self.server_thread = None
            self.server_instance.shutdown_event.set()
            self.server_thread.wait()
            (self.start_server_button.setEnabled(True))
            self.stop_server_button.setEnabled(False)

    # Topic History Tab
    def init_topic_history_tab(self):
        layout = QVBoxLayout()
        self.topic_list = QListWidget()
        layout.addWidget(self.topic_list)
        self.topic_history_tab.setLayout(layout)
        self.load_topic_history()

    def load_topic_history(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT full_path FROM topics ORDER BY full_path")
            topics = cursor.fetchall()
            self.topic_list.clear()
            for topic in topics:
                self.topic_list.addItem(topic[0])

    # Last 10 Messages Tab
    def init_last_messages_tab(self):
        layout = QVBoxLayout()

        # Topic selection
        h_layout = QHBoxLayout()
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("Enter topic...")
        self.fetch_button = QPushButton("Fetch Messages")
        self.fetch_button.clicked.connect(self.fetch_last_messages)
        h_layout.addWidget(self.topic_input)
        h_layout.addWidget(self.fetch_button)
        layout.addLayout(h_layout)

        # Messages display
        self.messages_display = QTextEdit()
        self.messages_display.setReadOnly(True)
        layout.addWidget(self.messages_display)

        self.last_messages_tab.setLayout(layout)

    def fetch_last_messages(self):
        topic = self.topic_input.text()
        if not topic:
            self.messages_display.setPlainText("Please enter a topic.")
            return

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT payload, published_at FROM messages
                JOIN topics ON messages.topic_id = topics.id
                WHERE topics.full_path = ?
                ORDER BY published_at DESC
                LIMIT 10
            """, (topic,))
            messages = cursor.fetchall()
            if messages:
                display_text = ""
                for payload, published_at in messages:
                    display_text += f"[{published_at}] {payload}\n"
                self.messages_display.setPlainText(display_text)
            else:
                self.messages_display.setPlainText("No messages found for this topic.")

    # Connected Clients Tab
    def init_connected_clients_tab(self):
        layout = QVBoxLayout()
        self.clients_tree = QTreeWidget()
        self.clients_tree.setHeaderLabels(["Connected Clients", "Subscriptions"])
        self.clients_tree.header().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.clients_tree)
        self.connected_clients_tab.setLayout(layout)
        self.load_connected_clients()

    def load_connected_clients(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT client_id FROM clients
                WHERE connected = 1
                ORDER BY client_id
            """)
            clients = cursor.fetchall()
            self.clients_tree.clear()
            for (client_id,) in clients:
                client_item = QTreeWidgetItem([client_id])
                # Get subscriptions for this client
                cursor.execute("""
                    SELECT topic_filter, qos FROM subscriptions
                    WHERE client_id = ? AND topic_filter IS NOT NULL
                """, (client_id,))
                wildcard_subs = cursor.fetchall()
                cursor.execute("""
                    SELECT topics.full_path, subscriptions.qos
                    FROM subscriptions
                    JOIN topics ON subscriptions.topic_id = topics.id
                    WHERE subscriptions.client_id = ? AND subscriptions.topic_id IS NOT NULL
                """, (client_id,))
                direct_subs = cursor.fetchall()
                # Combine subscriptions
                all_subs = []
                for topic_filter, qos in wildcard_subs:
                    all_subs.append((topic_filter, qos))
                for full_path, qos in direct_subs:
                    all_subs.append((full_path, qos))
                if all_subs:
                    for topic, qos in all_subs:
                        sub_item = QTreeWidgetItem([topic, f"QoS: {qos}"])
                        client_item.addChild(sub_item)
                else:
                    sub_item = QTreeWidgetItem(["No subscriptions"])
                    client_item.addChild(sub_item)
                self.clients_tree.addTopLevelItem(client_item)
            self.clients_tree.expandAll()

    # Subscribed Clients Tab
    def init_subscribed_clients_tab(self):
        layout = QVBoxLayout()
        self.subscriptions_tree = QTreeWidget()
        self.subscriptions_tree.setHeaderLabels(["Topic", "Subscribed Clients"])
        self.subscriptions_tree.header().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.subscriptions_tree)
        self.subscribed_clients_tab.setLayout(layout)
        self.load_subscribed_clients()

    def load_subscribed_clients(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Get all topics
            cursor.execute("SELECT id, full_path FROM topics ORDER BY full_path")
            topics = cursor.fetchall()
            self.subscriptions_tree.clear()
            for topic_id, full_path in topics:
                topic_item = QTreeWidgetItem([full_path])
                # Get clients subscribed to this topic
                cursor.execute("""
                    SELECT clients.client_id
                    FROM subscriptions
                    JOIN clients ON subscriptions.client_id = clients.client_id
                    WHERE subscriptions.topic_id = ?
                """, (topic_id,))
                clients = cursor.fetchall()
                for client in clients:
                    client_item = QTreeWidgetItem([client[0]])
                    topic_item.addChild(client_item)
                self.subscriptions_tree.addTopLevelItem(topic_item)
            self.subscriptions_tree.expandAll()

    # QoS Messages Tab
    def init_qos_messages_tab(self):
        layout = QVBoxLayout()
        self.qos_messages_list = QListWidget()
        layout.addWidget(self.qos_messages_list)
        self.qos_messages_tab.setLayout(layout)
        self.load_qos_messages()

    def load_qos_messages(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT messages.payload, topics.full_path, messages.qos, messages.published_at
                FROM messages
                JOIN topics ON messages.topic_id = topics.id
                WHERE messages.qos IN (1, 2)
                ORDER BY messages.published_at DESC
            """)
            messages = cursor.fetchall()
            self.qos_messages_list.clear()
            for payload, topic, qos, published_at in messages:
                item_text = f"[{published_at}] Topic: {topic}, QoS: {qos}, Message: {payload}"
                self.qos_messages_list.addItem(item_text)


def main():
    app = QApplication(sys.argv)
    gui = MQTTGUI()
    gui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
