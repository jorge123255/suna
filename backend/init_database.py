#!/usr/bin/env python3
"""
Database initialization script for Suna.
This script connects to Supabase and executes the SQL in db_init.sql to create necessary tables.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
from services.supabase import DBConnection
from utils.logger import logger

# Load environment variables
load_dotenv()

async def init_database():
    """Initialize the database by creating necessary tables."""
    try:
        # Connect to the database
        logger.info("Connecting to Supabase...")
        db = DBConnection()
        client = await db.client
        
        # Read the SQL file
        logger.info("Reading SQL initialization file...")
        sql_path = os.path.join(os.path.dirname(__file__), "db_init.sql")
        with open(sql_path, "r") as f:
            sql = f.read()
        
        # Execute the SQL
        logger.info("Executing SQL to create tables...")
        # Split the SQL into individual statements
        statements = sql.split(";")
        for statement in statements:
            if statement.strip():
                try:
                    # Execute each statement
                    await client.rpc("exec_sql", {"sql": statement}).execute()
                    logger.info(f"Executed: {statement[:50]}...")
                except Exception as e:
                    logger.error(f"Error executing SQL: {e}")
                    logger.error(f"Statement: {statement}")
        
        logger.info("Database initialization completed successfully!")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting database initialization...")
    success = asyncio.run(init_database())
    if success:
        logger.info("Database setup completed successfully.")
        sys.exit(0)
    else:
        logger.error("Database setup failed.")
        sys.exit(1)
