
import logging
from dotenv import load_dotenv

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from utils.db import Db
from utils.waha_client import WAHA_CLIENT

logger = logging.getLogger(__name__)


class Sender():
    """
        main class
    """
    def __init__(self):   
        load_dotenv()     
        self.db = Db()
        self.waha_client = WAHA_CLIENT()
    
    def queue_messages(self):
        query = text("""
            WITH to_send AS(
                SELECT c.id AS contact_id, t.id AS template_id
                FROM contacts c
                CROSS JOIN templates t
            ),            
            queued AS(
                SELECT m.id, m.contact_id, m.template_id, m.status
                FROM messages m
                WHERE m.status IN ('PENDING', 'SENT', 'DELIVERED', 'READ')
            ),
            to_queue AS (
                SELECT a.contact_id, a.template_id
                FROM to_send a
                LEFT JOIN queued q ON q.contact_id = a.contact_id AND q.template_id = a.template_id
                WHERE q.id IS NULL  -- Only get combinations that don't have a message yet                
            )
            INSERT INTO messages (contact_id, template_id)
            SELECT contact_id, template_id
            FROM to_queue
        """)
        
        try:
            with self.db.engine.begin() as conn:  # Auto-commit + rollback on error
                inserted = conn.execute(query)
                logger.info("Queued %d new messages", inserted.rowcount)
        except SQLAlchemyError as e:
            logger.error("Error queuing messages: %s", e)


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
                
        except SQLAlchemyError as e:
            logger.error("Error fetching pending messages: %s", e)
            return []
        
        