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
import time
import datetime
from mqtt_init import *

# Creating Client name - should be unique
global clientname
r = random.randrange(1, 10000000)
clientname = "CAR_WINDOW_CLIENT-" + str(r)
control_topic = 'car_monitor/control'

class Mqtt_client(QObject):
    # Signals for safely updating the GUI from a different thread
    message_signal = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.broker = ''
        self.port = ''
        self.clientname = ''
        self.on_connected_to_form = ''
        self.client = None
        
    def set_on_connected_to_form(self, on_connected_to_form):
        self.on_connected_to_form = on_connected_to_form

    def set_broker(self, value):
        self.broker = value

    def set_port(self, value):
        self.port = value

    def set_clientName(self, value):
        self.clientname = value

    def on_log(self, client, userdata, level, buf):
        print("log: " + buf)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to broker OK")
            self.on_connected_to_form()
            self.client.subscribe(control_topic) 
        else:
            print("Bad connection Returned code=", rc)

    def on_disconnect(self, client, userdata, flags, rc=0):
        print("Disconnected result code " + str(rc))

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
        except json.JSONDecodeError:
            print(f"Failed to decode JSON from topic {msg.topic}: {msg.payload.decode('utf-8')}")
            return
            
        self.message_signal.emit(payload)

    def connect_to(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, self.clientname, clean_session=True)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_log = self.on_log
        self.client.on_message = self.on_message
        self.client.connect(self.broker, self.port)

    def start_listening(self):
        self.client.loop_start()

    def publish_to(self, topic, message):
        self.client.publish(topic, message)

class ConnectionDock(QDockWidget):
    def __init__(self, mc):
        QDockWidget.__init__(self)
        
        self.mc = mc
        self.mc.set_on_connected_to_form(self.on_connected)
        
        self.eHostInput = QLineEdit()
        self.eHostInput.setText(broker_ip)
        
        self.ePort = QLineEdit()
        self.ePort.setValidator(QIntValidator())
        self.ePort.setText(broker_port)
        
        self.eClientID = QLineEdit()
        self.eClientID.setText(clientname)
        
        self.eConnectbtn = QPushButton("Connect to Broker")
        self.eConnectbtn.clicked.connect(self.on_button_connect_click)
        
        self.eConnectbtn.setStyleSheet("background-color: red")

        formLayot = QFormLayout()
        formLayot.addRow("Host", self.eHostInput)
        formLayot.addRow("Port", self.ePort)
        formLayot.addRow("Client ID", self.eClientID)
        formLayot.addRow("Connect", self.eConnectbtn)
        
        widget = QWidget(self)
        widget.setLayout(formLayot)
        self.setTitleBarWidget(widget)
        self.setWidget(widget)
        self.setWindowTitle("Connect")

    def on_connected(self):
        self.eConnectbtn.setStyleSheet("background-color: green")

    def on_button_connect_click(self):
        self.mc.set_broker(self.eHostInput.text())
        self.mc.set_port(int(self.ePort.text()))
        self.mc.set_clientName(self.eClientID.text())
        self.mc.connect_to()
        self.mc.start_listening()

class CarWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.mc = Mqtt_client()
        self.mc.message_signal.connect(self.handle_incoming_message)
        
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.setGeometry(300, 200, 300, 200)
        self.setWindowTitle('חלון רכב')
        
        central_widget = QWidget()
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # Status Label
        self.eStatusLabel = QLabel("חלון סגור")
        self.eStatusLabel.setFont(QFont("Arial", 16, QFont.Bold))
        self.eStatusLabel.setAlignment(Qt.AlignCenter)
        self.eStatusLabel.setStyleSheet("background-color: lightgray")
        
        # Close Button - added to enable manual control
        self.eClosebtn = QPushButton("סגור חלון")
        self.eClosebtn.clicked.connect(self.on_close_button_click)
        
        layout.addWidget(self.eStatusLabel)
        layout.addWidget(self.eClosebtn)
        
        # Initial connection dock
        self.connectionDock = ConnectionDock(self.mc)
        self.addDockWidget(Qt.TopDockWidgetArea, self.connectionDock)
        
        self.show()

    @pyqtSlot(object)
    def handle_incoming_message(self, payload):
        status = payload.get("status")
        
        if status == "open":
            self.eStatusLabel.setText("חלון פתוח")
            self.eStatusLabel.setStyleSheet("background-color: lightgreen; color: black")
        elif status == "close":
            self.eStatusLabel.setText("חלון סגור")
            self.eStatusLabel.setStyleSheet("background-color: lightgray; color: black")
            
    def on_close_button_click(self):
        message = {"status": "close"}
        self.mc.publish_to(control_topic, json.dumps(message))

# Main entry point if this script is run directly
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = CarWindow()
    sys.exit(app.exec_())
