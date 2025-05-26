import paho.mqtt.client as mqtt
import ssl
import time
import logging
import sys
from datetime import datetime

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MQTT Configuration
MQTT_BROKER = "mosquitto"
MQTT_PORT = 8883
MQTT_TOPIC = "test/topic"
HEALTH_CHECK_TOPIC = "$SYS/health"

# TLS Certificate paths
CA_CERT = "/certs/ca.crt"
CLIENT_CERT = "/certs/client.crt"
CLIENT_KEY = "/certs/client.key"

# Connection parameters
KEEPALIVE = 60
MAX_RECONNECT_ATTEMPTS = 12
RECONNECT_DELAY_START = 1  # Initial delay in seconds
RECONNECT_DELAY_MAX = 60   # Maximum delay in seconds

class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.connected = False
        self.reconnect_count = 0
        self.last_reconnect_delay = 0
        self.setup_client()

    def setup_client(self):
        # Set up TLS/SSL
        try:
            self.client.tls_set(
                ca_certs=CA_CERT,
                certfile=CLIENT_CERT,
                keyfile=CLIENT_KEY,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLSv1_2
            )
        except Exception as e:
            logger.error(f"Failed to set up TLS: {e}")
            sys.exit(1)

        # Set callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.on_publish = self.on_publish
        self.client.enable_logger(logger)

        # Set last will and testament (LWT)
        self.client.will_set(
            HEALTH_CHECK_TOPIC,
            "offline",
            qos=1,
            retain=True
        )

    def calculate_reconnect_delay(self):
        # Exponential backoff with maximum delay
        delay = min(
            RECONNECT_DELAY_START * (2 ** self.reconnect_count),
            RECONNECT_DELAY_MAX
        )
        self.last_reconnect_delay = delay
        return delay

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected successfully to MQTT broker")
            self.connected = True
            self.reconnect_count = 0
            # Subscribe to topics
            client.subscribe([(MQTT_TOPIC, 1), (HEALTH_CHECK_TOPIC, 1)])
            # Publish online status
            client.publish(HEALTH_CHECK_TOPIC, "online", qos=1, retain=True)
        else:
            logger.error(f"Connection failed with code: {rc}")
            self.connected = False

    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection. Code: {rc}")
            self.reconnect_count += 1
        else:
            logger.info("Clean disconnection")

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode()
            logger.info(f"Received message on {msg.topic}: {payload}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def on_publish(self, client, userdata, mid):
        logger.debug(f"Message {mid} published successfully")

    def connect(self):
        while True:
            try:
                if not self.connected:
                    logger.info(f"Attempting to connect to {MQTT_BROKER}:{MQTT_PORT}")
                    self.client.connect(MQTT_BROKER, MQTT_PORT, KEEPALIVE)
                    break
            except Exception as e:
                if self.reconnect_count >= MAX_RECONNECT_ATTEMPTS:
                    logger.error("Max reconnection attempts reached. Exiting.")
                    return False
                
                delay = self.calculate_reconnect_delay()
                logger.warning(f"Connection failed: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
                self.reconnect_count += 1
        
        return True

    def publish_message(self, topic, message, qos=1, retain=False):
        if not self.connected:
            logger.warning("Not connected. Message won't be published.")
            return False
        
        try:
            result = self.client.publish(topic, message, qos=qos, retain=retain)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.error(f"Failed to publish message: {mqtt.error_string(result.rc)}")
                return False
            return True
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False

    def run(self):
        if not self.connect():
            return

        self.client.loop_start()
        
        try:
            while True:
                if self.connected:
                    message = {
                        "message": "Hello MQTT with mTLS!",
                        "timestamp": datetime.now().isoformat(),
                        "client_id": self.client._client_id.decode()
                    }
                    self.publish_message(MQTT_TOPIC, str(message))
                time.sleep(5)

        except KeyboardInterrupt:
            logger.info("Shutting down...")
            # Publish offline status before disconnecting
            self.publish_message(HEALTH_CHECK_TOPIC, "offline", retain=True)
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Cleanup completed")

if __name__ == "__main__":
    mqtt_client = MQTTClient()
    mqtt_client.run()
