#!/usr/bin/env python3
"""
Script to check if the required tables exist in Supabase.
"""

import asyncio
from dotenv import load_dotenv
from services.supabase import DBConnection
from utils.logger import logger

# Load environment variables
load_dotenv()

async def check_tables():
    """Check if the required tables exist in Supabase."""
    try:
        # Connect to the database
        logger.info("Connecting to Supabase...")
        db = DBConnection()
        client = await db.client
        
        # Check thread_messages table
        logger.info("Checking thread_messages table...")
        try:
            result = await client.from_("thread_messages").select("count").limit(1).execute()
            logger.info(f"thread_messages table exists: {result}")
        except Exception as e:
            logger.error(f"Error checking thread_messages table: {e}")
        
        # Check threads table
        logger.info("Checking threads table...")
        try:
            result = await client.from_("threads").select("count").limit(1).execute()
            logger.info(f"threads table exists: {result}")
        except Exception as e:
            logger.error(f"Error checking threads table: {e}")
        
        return True
    except Exception as e:
        logger.error(f"Error checking tables: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting table check...")
    success = asyncio.run(check_tables())
    if success:
        logger.info("Table check completed.")
    else:
        logger.error("Table check failed.")
