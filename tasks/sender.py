
import logging
from dotenv import load_dotenv

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from utils.db import Db
from utils.sms_gate_client import SMSGateClient

logger = logging.getLogger(__name__)


class Sender():
    """
        main class
    """
    def __init__(self):   
        load_dotenv()     
        self.db = Db()
        self.sms_gate_client = SMSGateClient()
    
    def queue_messages(self):
        query = text("""
            WITH recent_active AS (
                -- Contacts that already got a message in the last 13 hours
                SELECT contact_id
                FROM messages
                WHERE created_at >= NOW() - INTERVAL '13 hours'
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
                inserted = conn.execute(query)
                logger.info("Queued %d new messages", inserted.rowcount)
        except SQLAlchemyError as e:
            logger.error("Error queuing messages: %s", e)


    def send_pending_messages(self):
        query = text("""
            SELECT m.id, c.phone, t.content
            FROM messages m
            JOIN contacts c ON c.id = m.contact_id
            JOIN templates t ON t.id = m.template_id
            WHERE m.status = 'pending'
            ORDER BY m.created_at
        """)
        
        try:
            with self.db.engine.begin() as conn:  # Auto-commit + rollback on error
                result = conn.execute(query)
                messages = result.fetchall()
                logger.info("Fetched %d pending messages", len(messages))
                
                for msg in messages:
                    sms_response = self.sms_gate_client.send_sms(f"+{msg.phone}", msg.content)
                    logger.info("SMS Gate response: %s", sms_response)
                    update_query = text("UPDATE messages SET status = 'sent' WHERE id = :id")
                    conn.execute(update_query, {"id": msg.id})
                    
        except SQLAlchemyError as e:
            logger.error("Error fetching pending messages: %s", e)
            return []
        
        