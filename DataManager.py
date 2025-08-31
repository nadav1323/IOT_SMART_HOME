import paho.mqtt.client as mqtt
import json
import sqlite3
import datetime
import sys
import os
from mqtt_init import *

# Creating Client name - should be unique
clientname = "DATA_MANAGER_CLIENT"
sub_topic = 'baby_monitor/#'
# Use the user-provided absolute path
base_dir = r'C:\Users\dell\Desktop\IOT\Nadav\Assignment2\-IOT_SMART_HOME-main (1)\-IOT_SMART_HOME-main\project'
db_file_name = os.path.join(base_dir, 'baby_monitor.db')
log_file_name = os.path.join(base_dir, 'baby_monitor.log')

# Use global variables for the database connection and log file
conn = None
c = None
log_file = None

class Mqtt_client():
    def __init__(self):
        self.broker = broker_ip
        self.port = int(broker_port)
        self.clientname = clientname
        self.client = None

    def on_log(self, client, userdata, level, buf):
        print("log: " + buf)
        write_to_log_file("log: " + buf)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to broker OK")
            write_to_log_file("Connected to broker OK")
            self.client.subscribe(sub_topic)
        else:
            print("Bad connection Returned code=", rc)
            write_to_log_file(f"Bad connection Returned code= {rc}")

    def on_disconnect(self, client, userdata, flags, rc=0):
        print("Disconnected result code " + str(rc))
        write_to_log_file("Disconnected result code " + str(rc))

    def on_message(self, client, userdata, msg):
        global conn, c
        if conn is None or c is None:
            write_to_log_file("ERROR: Database connection is not available. Message ignored.")
            return

        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
        except json.JSONDecodeError:
            write_to_log_file(f"Failed to decode JSON from topic {topic}: {msg.payload.decode('utf-8')}")
            return

        timestamp = datetime.datetime.now().isoformat()
        
        # Save data to database
        if topic == 'baby_monitor/temperature':
            temp = payload.get("temperature")
            hum = payload.get("humidity")
            c.execute("INSERT INTO sensor_data (timestamp, topic, value) VALUES (?, ?, ?)", (timestamp, 'temperature', temp))
            c.execute("INSERT INTO sensor_data (timestamp, topic, value) VALUES (?, ?, ?)", (timestamp, 'humidity', hum))
            log_message = f"Data for temperature and humidity saved to DB."
            print(log_message)
            write_to_log_file(log_message)
            
            # Check for high temperature alert
            if temp > 37.5:
                alert_message = {"alert": "high_temp", "value": temp}
                client.publish('baby_monitor/alerts', json.dumps(alert_message))
                alert_log = "ALERT: High temperature detected!"
                print(alert_log)
                write_to_log_file(alert_log)
                # Send alert to mobile app
                mobile_alert = {"message": f"התראה: טמפרטורה גבוהה התגלתה! ({temp}°C)", "timestamp": timestamp}
                client.publish('baby_monitor/mobile_alerts', json.dumps(mobile_alert))


        elif topic == 'baby_monitor/sound':
            status = payload.get("status")
            c.execute("INSERT INTO sensor_data (timestamp, topic, status) VALUES (?, ?, ?)", (timestamp, 'sound', status))
            log_message = f"Data for sound saved to DB."
            print(log_message)
            write_to_log_file(log_message)

            # Check for baby crying alert
            if status == "crying":
                alert_message = {"alert": "crying", "value": "crying"}
                client.publish('baby_monitor/alerts', json.dumps(alert_message))
                alert_log = "ALERT: Baby is crying!"
                print(alert_log)
                write_to_log_file(alert_log)
                # Send alert to mobile app
                mobile_alert = {"message": f"התראה: בכי התגלה!", "timestamp": timestamp}
                client.publish('baby_monitor/mobile_alerts', json.dumps(mobile_alert))

        
        elif topic == 'baby_monitor/motion':
            status = payload.get("status")
            c.execute("INSERT INTO sensor_data (timestamp, topic, status) VALUES (?, ?, ?)", (timestamp, 'motion', status))
            log_message = f"Data for motion saved to DB."
            print(log_message)
            write_to_log_file(log_message)
            
            # Check for motion alert
            if status == "detected":
                alert_message = {"alert": "motion", "value": "detected"}
                client.publish('baby_monitor/alerts', json.dumps(alert_message))
                alert_log = "ALERT: Motion detected!"
                print(alert_log)
                write_to_log_file(alert_log)
                # Send alert to mobile app
                mobile_alert = {"message": f"התראה: תנועה התגלתה!", "timestamp": timestamp}
                client.publish('baby_monitor/mobile_alerts', json.dumps(mobile_alert))

        conn.commit()

    def connect_to(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, self.clientname, clean_session=True)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_log = self.on_log
        self.client.on_message = self.on_message
        print("Connecting to broker ", self.broker)
        write_to_log_file("Connecting to broker " + self.broker)
        self.client.connect(self.broker, self.port)

    def start_listening(self):
        self.client.loop_forever()

def write_to_log_file(message):
    global log_file
    if log_file:
        timestamp = datetime.datetime.now().isoformat()
        log_file.write(f"[{timestamp}] {message}\n")

if __name__ == "__main__":
    try:
        # Create the directory if it doesn't exist
        os.makedirs(base_dir, exist_ok=True)

        # Database setup
        print("Attempting to connect to database...")
        conn = sqlite3.connect(db_file_name)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                topic TEXT,
                value REAL,
                status TEXT
            )
        ''')
        conn.commit()
        print(f"Database file '{db_file_name}' ready.")
        
        # Log file setup
        print("Opening log file...")
        log_file = open(log_file_name, 'a', encoding='utf-8')
        print(f"Log file '{log_file_name}' ready. Writing logs to file...")

        dm_client = Mqtt_client()
        dm_client.connect_to()
        dm_client.start_listening()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Ensure files are closed properly
        if conn:
            conn.close()
            print("Database connection closed.")
        if log_file:
            log_file.close()
            print("Log file closed.")