"""
Test Redis connection with the updated configuration.
"""

import asyncio
import redis.asyncio as redis
import os

# Import our Redis configuration override
import redis_config

async def test_redis_connection():
    """Test the Redis connection with the updated configuration."""
    print(f"Testing Redis connection to {os.environ['REDIS_HOST']}:{os.environ['REDIS_PORT']}")
    
    # Create Redis client with the overridden configuration
    client = redis.Redis(
        host=os.environ['REDIS_HOST'],
        port=int(os.environ['REDIS_PORT']),
        password=os.environ['REDIS_PASSWORD'],
        ssl=os.environ['REDIS_SSL'].lower() == 'true',
        decode_responses=True,
        socket_timeout=5.0,
        socket_connect_timeout=5.0,
        retry_on_timeout=True,
        health_check_interval=30
    )
    
    try:
        # Test the connection
        await client.ping()
        print("✅ Successfully connected to Redis!")
        
        # Test setting and getting a value
        await client.set("test_key", "test_value")
        value = await client.get("test_key")
        print(f"✅ Successfully set and retrieved a value: {value}")
        
        # Clean up
        await client.delete("test_key")
        print("✅ Successfully cleaned up test key")
        
    except Exception as e:
        print(f"❌ Redis connection failed: {str(e)}")
    finally:
        # Close the connection
        await client.close()
        print("Connection closed")

if __name__ == "__main__":
    asyncio.run(test_redis_connection())
