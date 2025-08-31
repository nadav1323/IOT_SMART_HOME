import os
import sys
import PyQt5
import random
import json
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import paho.mqtt.client as mqtt
from mqtt_init import *
from MonitorGUI import Mqtt_client as Mqtt_Client_Monitor # Import the Mqtt_client class from MonitorGUI.py

# Creating Client name - should be unique
r = random.randrange(1, 1000000)
clientname = "MOBILE_APP_CLIENT-" + str(r)
alert_topic = 'baby_monitor/mobile_alerts'

class MobileAppWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.mc = Mqtt_Client_Monitor()
        self.mc.set_clientName(clientname)
        self.mc.set_broker(broker_ip)
        self.mc.set_port(int(broker_port))
        
        # Set a dummy function for on_connected_to_form to prevent the TypeError
        self.mc.set_on_connected_to_form(self.on_connected_placeholder)
        
        # Connect the signal from the MQTT client to a method in this window
        self.mc.message_signal.connect(self.handle_incoming_message)
        
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.setGeometry(800, 200, 300, 500)
        self.setWindowTitle('התראות - טלפון נייד')
        
        # UI Elements
        self.status_label = QLabel("מחכה להתראות...")
        self.status_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: white; background-color: darkblue;")

        self.alert_text_area = QTextEdit()
        self.alert_text_area.setReadOnly(True)
        self.alert_text_area.setStyleSheet("background-color: black; color: yellow;")
        
        # Main Layout
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.status_label)
        layout.addWidget(self.alert_text_area)
        self.setCentralWidget(central_widget)
        
        # Connect to MQTT and subscribe
        self.mc.connect_to()
        self.mc.client.subscribe(alert_topic, qos=0)
        self.mc.start_listening()
        self.show()

    def handle_incoming_message(self, topic, payload):
        if topic == alert_topic:
            try:
                # The payload is already a dictionary from MonitorGUI.py
                message = payload
                alert_text = message.get("message", "התראה לא מזוהה")
                timestamp = message.get("timestamp", "")
                
                # Update the text area with the new alert
                current_text = self.alert_text_area.toPlainText()
                new_text = f"[{timestamp}] - {alert_text}\n" + current_text
                self.alert_text_area.setPlainText(new_text)

                self.status_label.setText("התראה חדשה התקבלה!")
                self.status_label.setStyleSheet("background-color: darkred; color: yellow")
                
                # Reset status after a few seconds
                QTimer.singleShot(5000, lambda: self.status_label.setStyleSheet("color: white; background-color: darkblue;"))
            
            except Exception as e:
                print(f"An error occurred while handling the alert message: {e}")

    def on_connected_placeholder(self):
        # This function exists to satisfy the on_connected_to_form requirement
        # It does nothing, as the MobileApp does not have a "Connect" button
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MobileAppWindow()
    sys.exit(app.exec_())