
import logging
import os

from dotenv import load_dotenv
import requests

# Configure logging for debugging and monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv() 

class WAHA_CLIENT():
    def __init__(self):
        self.base_url = os.getenv("WAHA_HOST")
        self.timeout = int(os.getenv("WAHA_TIMEOUT", "10"))
        self.headers = {
            'Content-Type': 'application/json',
            'accept': 'application/json',
            'X-Api-Key': f'{os.getenv("WAHA_API_KEY")}'
        }   
     
    def send_text(self, phone, message):
        url = f'{self.base_url}/api/sendText'

        # Prepare the data to be sent
        data={ 
            "chatId": f'{phone}@c.us',
            "text": message,
            "linkPreview": True,
            "linkPreviewHighQuality": True,
            "session": "default"
        }
        try:
            # Make the POST request with a timeout to avoid hanging indefinitely
            response = requests.post(url, headers=self.headers, json=data, timeout=self.timeout)

            response.raise_for_status()
            response_json = response.json()
            logger.info(response_json)
            return response_json

        except requests.exceptions.Timeout as e:
            logger.error("Request timed out: %s", e)
            return None
        except requests.exceptions.RequestException as e:
            logger.error("Request failed: %s", e)
            return None
        except Exception as e:
            logger.error(e)
            return None  
    
    
    def get_message_status(self, chat_id, message_id):
        #http://localhost:3000/api/default/chats/254105565532%40c.us/messages/true_55951025512511%40lid_3EB02FA21F8054885DFC3B_out?downloadMedia=true&merge=true
        url = f'{self.base_url}/api/default/chats/{chat_id}/messages/{message_id}'
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout as e:
            logger.error("Request timed out: %s", e)
            return None
        except requests.exceptions.RequestException as e:
            logger.error("Request failed: %s", e)
            return None
        except Exception as e:
            logger.error(e)
            return None