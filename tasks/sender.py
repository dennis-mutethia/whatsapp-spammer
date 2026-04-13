
import logging
import os

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from utils.db import Db
from utils.sms_gate_client import SMSGateClient
from utils.waha_client import WAHA_CLIENT

logger = logging.getLogger(__name__)

SPAMMER_INTERVAL_HOURS = int(os.getenv("SPAMMER_INTERVAL_HOURS", "7")) 

class Sender():
    """
        main class
    """
    def __init__(self):   
        self.db = Db()
        self.sms_gate_client = SMSGateClient()
        self.waha_client = WAHA_CLIENT()
    
    def queue_messages(self):
        query = text("""
            WITH recent_active AS (
                -- Contacts that already got a message in the last 13 hours
                SELECT contact_id
                FROM messages
                WHERE created_at >= NOW() - INTERVAL ':interval_hours hours'
                GROUP BY contact_id
            ),
            used_templates AS (
                -- Templates already sent to each contact (to avoid repeats)
                SELECT DISTINCT contact_id, template_id
                FROM messages
                WHERE status = 'sent'
            ),
            to_send AS (
                -- Cross join contacts x templates, exclude recent and already-sent combos
                SELECT DISTINCT ON (c.id)
                    c.id AS contact_id,
                    t.id AS template_id
                FROM contacts c
                CROSS JOIN templates t
                LEFT JOIN recent_active ra ON ra.contact_id = c.id
                LEFT JOIN used_templates ut ON ut.contact_id = c.id AND ut.template_id = t.id
                WHERE ra.contact_id IS NULL   -- Not messaged in last 13 hours
                AND ut.template_id IS NULL  -- Template not previously sent to this contact
                ORDER BY c.id, RANDOM()       -- Pick a random unused template per contact
            )
            INSERT INTO messages (contact_id, template_id)
            SELECT contact_id, template_id
            FROM to_send
        """)
        
        try:
            with self.db.engine.begin() as conn:  # Auto-commit + rollback on error
                inserted = conn.execute(query, {"interval_hours": SPAMMER_INTERVAL_HOURS})
                logger.info("Queued %d new messages", inserted.rowcount)
        except SQLAlchemyError as e:
            logger.error("Error queuing messages: %s", e)


    def send_sms_message(self, msg, conn):   
        try: 
            sms_response = self.sms_gate_client.send_sms(f"+{msg.phone}", msg.content)
            logger.info("SMS Gate response: %s", sms_response)
            update_query = text("UPDATE messages SET status = 'sent' WHERE id = :id")
            conn.execute(update_query, {"id": msg.id})
                    
        except Exception as e:
            logger.error("Error sending SMS message ID %d: %s", msg.id, e)
    
    def send_waha_message(self, msg, conn):   
        try: 
            response = self.waha_client.send_text(msg.phone, msg.content)
            message_id = response.get("id").get("_serialized") if response else None
            if message_id:
                response = self.waha_client.get_message_status(msg.phone, message_id)
                status = response.get("ackName") if response else None
                logger.info("Message ID %d sent with status: %s", msg.id, status)
                
                if status:                        
                    update_query = text("UPDATE messages SET status = :status WHERE id = :id")
                    conn.execute(update_query, {"id": msg.id, "status": status})
            else:
                logger.error("Failed to send message ID %d", msg.id)
        except Exception as e:
            logger.error("Error sending waha message ID %d: %s", msg.id, e)

    def send_pending_messages(self, limit=1):
        query = text("""
            SELECT m.id, c.phone, t.content
            FROM messages m
            JOIN contacts c ON c.id = m.contact_id
            JOIN templates t ON t.id = m.template_id
            WHERE m.status = 'pending'
            ORDER BY m.created_at
            LIMIT :limit
        """)
        
        try:
            with self.db.engine.begin() as conn:  # Auto-commit + rollback on error
                result = conn.execute(query, {"limit": limit})
                messages = result.fetchall()
                logger.info("Fetched %d pending messages", len(messages))
                
                for msg in messages:
                    self.send_waha_message(msg, conn)
                    
        except SQLAlchemyError as e:
            logger.error("Error fetching pending messages: %s", e)
            return []
        
        