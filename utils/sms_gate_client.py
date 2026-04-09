
import json
import logging
import os

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class SMSGateClient:
    def __init__(self):
        self.url = os.getenv("SMS_GATE_URL")
        self.username = os.getenv("SMS_GATE_USERNAME")
        self.password = os.getenv("SMS_GATE_PASSWORD")
        self.timeout = int(os.getenv("SMS_GATE_TIMEOUT"))

    def send_sms(self, phone_number, message):
        try:
            response = requests.post(
                self.url,
                auth=(self.username, self.password),
                json={
                    "textMessage": {"text": message},
                    "phoneNumbers": [phone_number]
                },
                timeout=self.timeout  # Use the configured timeout for the request
            )
            
            return  json.loads(response.text)
        
        except requests.HTTPError as e:
            logger.error("HTTP error occurred: %s", e)
            raise
        except requests.RequestException as e:
            logger.error("Error sending SMS: %s", e)
            raise
        
