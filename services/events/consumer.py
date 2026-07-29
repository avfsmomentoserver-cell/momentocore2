"""Kafka Event Consumer"""
import asyncio
import json
from typing import Any, Callable, Dict, List
from aiokafka import AIOKafkaConsumer
from .schemas import EventSchema


class EventConsumer:
    """Async Kafka event consumer for MomentoCore."""
    
    def __init__(self, topics: List[str], bootstrap_servers: str = "localhost:9092"):
        self.topics = topics
        self.bootstrap_servers = bootstrap_servers
        self.consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True
        )
        self.handlers: Dict[str, Callable] = {}
        
    async def start(self):
        """Start the consumer."""
        await self.consumer.start()
        
    async def stop(self):
        """Stop the consumer."""
        await self.consumer.stop()
        
    def register_handler(self, event_type: str, handler: Callable):
        """Register a handler for specific event types."""
        self.handlers[event_type] = handler
        
    async def consume(self):
        """Consume events from Kafka."""
        try:
            async for msg in self.consumer:
                event_data = msg.value
                event_type = event_data.get("event_type")
                
                if event_type in self.handlers:
                    await self.handlers[event_type](event_data)
                else:
                    print(f"No handler for event type: {event_type}")
        except Exception as e:
            print(f"Consumer error: {e}")
            raise
