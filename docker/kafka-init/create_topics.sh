#!/bin/bash

KAFKA_BIN="/opt/bitnami/kafka/bin/kafka-topics.sh"
BOOTSTRAP_SERVER="kafka:9092"

echo "⏳ Waiting for Kafka to be ready..."

until $KAFKA_BIN --list --bootstrap-server $BOOTSTRAP_SERVER; do
  echo "Kafka is not ready yet... sleeping 2s"
  sleep 2
done

echo "✅ Kafka is ready! Starting topic creation..."

create_topic() {
  local topic_name=$1
  echo "Creating topic: $topic_name"
  $KAFKA_BIN --create --if-not-exists \
    --bootstrap-server $BOOTSTRAP_SERVER \
    --partitions 3 \
    --replication-factor 1 \
    --topic "$topic_name"
}

create_topic "ai.makePoints.request"
create_topic "ai.makePoints.response"
create_topic "service.errors"

echo "🎉 All topics created successfully."