"""Kafka Event Producer"""
import asyncio
import json
from typing import Any, Dict
from aiokafka import AIOKafkaProducer
from .schemas import EventSchema


class EventProducer:
    """Async Kafka event producer for MomentoCore."""
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        self.producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
    async def start(self):
        """Start the producer."""
        await self.producer.start()
        
    async def stop(self):
        """Stop the producer."""
        await self.producer.stop()
        
    async def publish(self, topic: str, event: EventSchema):
        """Publish an event to Kafka."""
        try:
            await self.producer.send_and_wait(
                topic,
                event.dict()
            )
        except Exception as e:
            print(f"Failed to publish event: {e}")
            raise
