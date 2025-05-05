"""
Redis configuration override.

This module provides a way to override the Redis configuration
without modifying the .env file directly.
"""

import os

# Set environment variables for Redis
os.environ['REDIS_HOST'] = '192.168.1.2'  # Use the actual IP address of the Redis container
os.environ['REDIS_PORT'] = '6379'
os.environ['REDIS_PASSWORD'] = ''
os.environ['REDIS_SSL'] = 'false'

print("Redis configuration overridden: host=192.168.1.2, port=6379, ssl=false")