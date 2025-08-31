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
r = random.randrange(1, 100000)
clientname = "IOT_client-Id-" + str(r)

class Mqtt_client(QObject):
    # Signals for safely updating the GUI from a different thread
    message_signal = pyqtSignal(str, object)
    alert_signal = pyqtSignal(dict) # New signal for alerts
    
    def __init__(self):
        super().__init__()
        self.broker = ''
        self.port = ''
        self.clientname = ''
        self.username = ''
        self.password = ''
        self.on_connected_to_form = ''
        self.client = None
        self.current_temp = None
        self.current_sound = None

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
            # Subscribe to all baby monitor topics here, after a successful connection
            self.client.subscribe("baby_monitor/temperature", qos=0)
            self.client.subscribe("baby_monitor/sound", qos=0)
            self.client.subscribe("baby_monitor/motion", qos=0)
            self.client.subscribe("baby_monitor/alerts", qos=0)
            self.client.subscribe("baby_monitor/mobile_alerts", qos=0)
        else:
            print("Bad connection Returned code=", rc)

    def on_disconnect(self, client, userdata, flags, rc=0):
        print("Disconnected result code " + str(rc))

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload_str = msg.payload.decode('utf-8')
        
        try:
            payload = json.loads(payload_str)
        except json.JSONDecodeError:
            print(f"Failed to decode JSON from topic {topic}: {payload_str}")
            return
            
        # The logic here is key: send a dictionary payload regardless of the topic
        self.message_signal.emit(topic, payload)

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

class SubscriptionDock(QDockWidget):
    def __init__(self, mc):
        QDockWidget.__init__(self)
        self.mc = mc
        # Connect to message_signal only, as it now handles all topics
        self.mc.message_signal.connect(self.handle_incoming_message)

        self.eTempLabel = QLabel("טמפרטורה: N/A")
        self.eTempLabel.setFont(QFont("Arial", 16, QFont.Bold))
        self.eTempLabel.setAlignment(Qt.AlignCenter)
        
        self.eSoundLabel = QLabel("קול: N/A")
        self.eSoundLabel.setFont(QFont("Arial", 16, QFont.Bold))
        self.eSoundLabel.setAlignment(Qt.AlignCenter)
        
        self.eMotionLabel = QLabel("תנועה: N/A")
        self.eMotionLabel.setFont(QFont("Arial", 16, QFont.Bold))
        self.eMotionLabel.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.eTempLabel)
        layout.addWidget(self.eSoundLabel)
        layout.addWidget(self.eMotionLabel)
        
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setWidget(central_widget)
        self.setWindowTitle("בייבי מוניטור")

    @pyqtSlot(str, object)
    def handle_incoming_message(self, topic, payload):
        if topic == 'baby_monitor/temperature':
            if isinstance(payload, dict) and "temperature" in payload:
                temp = payload["temperature"]
                self.eTempLabel.setText(f"טמפרטורה: {temp}°C")
                if temp > 37.5:
                    self.eTempLabel.setStyleSheet("background-color: red; color: white")
                else:
                    self.eTempLabel.setStyleSheet("background-color: lightgreen; color: black")
        elif topic == 'baby_monitor/sound':
            if isinstance(payload, dict) and "status" in payload:
                status = payload["status"]
                if status == "crying":
                    self.eSoundLabel.setText(f"קול: בכי")
                    self.eSoundLabel.setStyleSheet("background-color: red; color: white")
                else:
                    self.eSoundLabel.setText(f"קול: שקט")
                    self.eSoundLabel.setStyleSheet("background-color: lightgray; color: black")
        elif topic == 'baby_monitor/motion':
            if isinstance(payload, dict) and "status" in payload:
                status = payload["status"]
                if status == "detected":
                    self.eMotionLabel.setText(f"תנועה: זוהתה")
                    self.eMotionLabel.setStyleSheet("background-color: yellow; color: black")
                else:
                    self.eMotionLabel.setText(f"תנועה: לא זוהתה")
                    self.eMotionLabel.setStyleSheet("background-color: lightgray; color: black")
        elif topic == 'baby_monitor/alerts' or topic == 'baby_monitor/mobile_alerts':
            self.handle_alert(payload)

    def handle_alert(self, payload):
        alert_type = payload.get("alert")
        if alert_type == "high_temp":
            print(f"ALERT: High temperature detected! ({payload.get('value')}°C)")
        elif alert_type == "crying":
            print("ALERT: Baby is crying!")
            # Publish a message to open the car window
            self.mc.publish_to("car_monitor/control", '{"status": "open"}')
        elif alert_type == "motion":
            print("ALERT: Motion detected!")
            # Publish a message to open the car window
            self.mc.publish_to("car_monitor/control", '{"status": "open"}')

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.mc = Mqtt_client()
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.setGeometry(30, 200, 400, 300)
        self.setWindowTitle('בייבי מוניטור')
        self.connectionDock = ConnectionDock(self.mc)
        self.addDockWidget(Qt.TopDockWidgetArea, self.connectionDock)
        self.subscribeDock = SubscriptionDock(self.mc)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.subscribeDock)
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())