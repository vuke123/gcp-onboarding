#!/bin/bash

# Container name from docker-compose.yaml
CONTAINER=kafka1

# Start Kafka and Kowl
echo "Starting Kafka and Kowl..."
docker compose up -d

echo "Waiting for Kafka to start..."
sleep 15

echo ""
echo "=== Task 1: Creating topic with 3 partitions ==="
docker exec $CONTAINER kafka-topics --bootstrap-server $CONTAINER:9092 --create --partitions 3 --topic input-topic

echo ""
echo "=== Task 2: Listing all topics ==="
docker exec $CONTAINER kafka-topics --bootstrap-server $CONTAINER:9092 --list

echo ""
echo "=== Task 3: Sending messages with keys ==="
echo "Starting producer - enter messages in format 'key:value'"
echo "Send these messages:"
echo "A:Message 1 from A"
echo "A:Message 2 from A"
echo "B:Message 1 from B"
echo "B:Message 2 from B"
echo "C:Message 1 from C"
echo "C:Message 2 from C"
echo "Type Ctrl+D when done"
docker exec --interactive --tty $CONTAINER kafka-console-producer --bootstrap-server $CONTAINER:9092 --property parse.key=true --property key.separator=: --topic input-topic

echo ""
echo "=== Task 4: Reading messages ==="
echo "Press Ctrl+C to stop reading"
docker exec --interactive --tty $CONTAINER kafka-console-consumer --bootstrap-server $CONTAINER:9092 --topic input-topic --from-beginning

echo ""
echo "=== Task 5: Check Kowl UI ==="
echo "Open http://localhost:8080 in your browser"
echo "Navigate to Topics -> input-topic to see partition assignment"

echo ""
echo "To stop services: docker compose down"
