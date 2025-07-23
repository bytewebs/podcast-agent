import pytest
from unittest.mock import Mock, patch
from messaging.kafka_producer import KafkaProducerClient
from messaging.kafka_consumer import KafkaConsumerClient
from messaging.topics import KafkaTopics

class TestMessaging:
    
    @patch('messaging.kafka_producer.KafkaProducer')
    def test_producer_initialization(self, mock_producer):
        """Test producer initialization"""
        mock_producer.return_value = Mock()
        
        client = KafkaProducerClient()
        assert client.producer is not None
    
    @patch('messaging.kafka_producer.KafkaProducer')
    def test_send_message(self, mock_producer):
        """Test message sending"""
        mock_producer_instance = Mock()
        mock_producer.return_value = mock_producer_instance
        
        # Mock successful send
        mock_future = Mock()
        mock_future.get.return_value = Mock(offset=123)
        mock_producer_instance.send.return_value = mock_future
        
        client = KafkaProducerClient()
        result = client.send_message("test_topic", {"test": "message"})
        
        assert result is True
        mock_producer_instance.send.assert_called_once()
    
    @patch('messaging.kafka_consumer.KafkaConsumer')
    def test_consumer_initialization(self, mock_consumer):
        """Test consumer initialization"""
        mock_consumer.return_value = Mock()
        
        topics = [KafkaTopics.OUTLINE_GENERATION]
        client = KafkaConsumerClient(topics)
        
        assert client.consumer is not None
        assert len(client.handlers) == 0
