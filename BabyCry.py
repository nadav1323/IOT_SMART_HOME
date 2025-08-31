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
clientname = "SOUND_SENSOR-" + str(r)
sound_topic = 'baby_monitor/sound'

class Mqtt_client():
    def __init__(self):
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
            print("connected OK")
            self.on_connected_to_form()
        else:
            print("Bad connection Returned code=", rc)

    def on_disconnect(self, client, userdata, flags, rc=0):
        print("DisConnected result code " + str(rc))

    def on_message(self, client, userdata, msg):
        pass

    def connect_to(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, self.clientname, clean_session=True)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_log = self.on_log
        self.client.on_message = self.on_message
        print("Connecting to broker ", self.broker)
        self.client.connect(self.broker, self.port)

    def start_listening(self):
        self.client.loop_start()

    def publish_to(self, topic, message):
        if self.client:
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
        self.ePort.setText(str(broker_port))
        self.eClientID = QLineEdit()
        self.eClientID.setText(clientname)
        self.eConnectbtn = QPushButton("Connect", self)
        self.eConnectbtn.clicked.connect(self.on_button_connect_click)
        self.eConnectbtn.setStyleSheet("background-color: red")
        self.eCryingbtn = QPushButton("Simulate Crying", self)
        self.eCryingbtn.clicked.connect(self.on_button_crying_click)
        self.eCryingbtn.setStyleSheet("background-color: lightgray")
        self.eTopic = QLineEdit()
        self.eTopic.setText(sound_topic)

        formLayot = QFormLayout()
        formLayot.addRow("Connect to Broker", self.eConnectbtn)
        formLayot.addRow("Pub topic", self.eTopic)
        formLayot.addRow("Status", self.eCryingbtn)
        widget = QWidget(self)
        widget.setLayout(formLayot)
        self.setTitleBarWidget(widget)
        self.setWidget(widget)
        self.setWindowTitle("Sound Sensor")

    def on_connected(self):
        self.eConnectbtn.setStyleSheet("background-color: green")

    def on_button_connect_click(self):
        self.mc.set_broker(self.eHostInput.text())
        self.mc.set_port(int(self.ePort.text()))
        self.mc.set_clientName(self.eClientID.text())
        self.mc.connect_to()
        self.mc.start_listening()

    def on_button_crying_click(self):
        message = {"status": "crying"}
        self.mc.publish_to(sound_topic, json.dumps(message))
        self.eCryingbtn.setStyleSheet("background-color: yellow")
        QTimer.singleShot(1000, lambda: self.eCryingbtn.setStyleSheet("background-color: lightgray"))

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.mc = Mqtt_client()
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.setGeometry(30, 300, 300, 200)
        self.setWindowTitle('Sound Sensor')
        self.connectionDock = ConnectionDock(self.mc)
        self.addDockWidget(Qt.TopDockWidgetArea, self.connectionDock)

app = QApplication(sys.argv)
mainwin = MainWindow()
mainwin.show()
app.exec_()
