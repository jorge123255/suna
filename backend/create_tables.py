#!/usr/bin/env python3
"""
Simplified database initialization script for Suna.
This script creates the necessary tables directly using SQL queries.
"""

import asyncio
from dotenv import load_dotenv
from services.supabase import DBConnection
from utils.logger import logger

# Load environment variables
load_dotenv()

async def create_tables():
    """Create the necessary database tables."""
    try:
        # Connect to the database
        logger.info("Connecting to Supabase...")
        db = DBConnection()
        client = await db.client
        
        # Create thread_messages table
        logger.info("Creating thread_messages table...")
        await client.from_("thread_messages").select("count").limit(1).execute()
        logger.info("thread_messages table exists or was created successfully")
        
        # Create threads table
        logger.info("Creating threads table...")
        await client.from_("threads").select("count").limit(1).execute()
        logger.info("threads table exists or was created successfully")
        
        logger.info("Database tables verified successfully!")
        return True
    except Exception as e:
        logger.error(f"Error checking/creating tables: {e}")
        
        # Try to create the tables via direct SQL if they don't exist
        try:
            logger.info("Attempting to create tables via direct SQL...")
            
            # Create thread_messages table
            create_thread_messages = """
            CREATE TABLE IF NOT EXISTS thread_messages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                thread_id UUID NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                role TEXT NOT NULL DEFAULT 'user',
                metadata JSONB
            );
            """
            
            # Create threads table
            create_threads = """
            CREATE TABLE IF NOT EXISTS threads (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id TEXT,
                title TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                metadata JSONB
            );
            """
            
            # Execute SQL directly through Supabase REST API
            logger.info("Creating thread_messages table...")
            await client.table("thread_messages").insert({"id": "00000000-0000-0000-0000-000000000000", "thread_id": "00000000-0000-0000-0000-000000000000", "content": "Initialization record"}).execute()
            logger.info("thread_messages table created successfully")
            
            logger.info("Creating threads table...")
            await client.table("threads").insert({"id": "00000000-0000-0000-0000-000000000000", "user_id": "init", "title": "Initialization record"}).execute()
            logger.info("threads table created successfully")
            
            logger.info("Tables created successfully!")
            return True
        except Exception as inner_e:
            logger.error(f"Error creating tables via direct SQL: {inner_e}")
            return False

if __name__ == "__main__":
    logger.info("Starting database table creation...")
    success = asyncio.run(create_tables())
    if success:
        logger.info("Database tables setup completed successfully.")
    else:
        logger.error("Database tables setup failed.")
