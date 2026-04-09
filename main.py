import logging
import time
import signal
import sys

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz 

from tasks.sender import Sender

# Global logging configuration (applies to all modules)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'  # Optional: Custom date format (e.g., 2025-11-04 22:13:45)
)

logger = logging.getLogger(__name__)

sender = Sender()

if __name__ == "__main__":
    # Start the scheduler with explicit timezone
    scheduler = BackgroundScheduler(timezone=pytz.timezone('Africa/Nairobi'))  # EAT/UTC+3 for Meru, KE
    
    # Add jobs with explicit CronTrigger for absolute wall-clock scheduling
    scheduler.add_job(
        func=sender.queue_messages,  # Directly pass the method reference
        trigger=CronTrigger(
            hour="*",       
            minute="*/1", #every 1 minute
            second="0"
        ),
        id="queue_messages",
        replace_existing=True,
        misfire_grace_time=30,  # 30s grace for delays
        coalesce=True  # Skip missed runs if piled up
    )
            
    scheduler.add_job(
        func=sender.send_pending_messages,  # Directly pass the method reference
        trigger=CronTrigger(
            hour="*",           
            minute="*/1",  #every 1 minute 
            second="0"
        ),
        id="send_pending_messages",
        replace_existing=True,
        misfire_grace_time=30,  # 30s grace for delays
        coalesce=True  # Skip missed runs if piled up
    )
    
            
    scheduler.start()
    
    # Graceful shutdown handler
    def shutdown_handler(signum, frame):
        logger.info("Shutting down scheduler...")
        scheduler.shutdown(wait=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    # Keep the main thread alive to allow background tasks to run
    try:
        logger.info("Scheduler started. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Received interrupt. Shutting down...")
        scheduler.shutdown(wait=True)