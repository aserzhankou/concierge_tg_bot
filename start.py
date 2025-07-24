#!/usr/bin/env python3
"""
Render-optimized start script for the Telegram bot.
Handles graceful shutdowns and deployment conflicts.
"""

import os
import sys
import signal
import asyncio
import logging
from bot import main

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    sys.exit(0)

def main_wrapper():
    """Main wrapper with better error handling for cloud deployments"""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Set deployment-specific environment variables
    os.environ['DEPLOYMENT_PLATFORM'] = 'render'
    
    try:
        logger.info("🚀 Starting Telegram bot on Render...")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        # Add a small delay to ensure any previous instances are fully terminated
        import time
        time.sleep(2)
        
        main()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main_wrapper() 