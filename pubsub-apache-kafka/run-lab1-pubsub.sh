#!/bin/bash

# Function to wait for user input
pause() {
    read -p "Press Enter to continue..."
}

# Get container ID or start emulator if not running
CONTAINER_ID=$(docker compose ps -q pubsub-emulator)
if [ -z "$CONTAINER_ID" ]; then
    echo "Starting Pub/Sub emulator..."
    docker compose up -d pubsub-emulator
    sleep 5
    CONTAINER_ID=$(docker compose ps -q pubsub-emulator)
fi

# Function to run gcloud commands in container
run_cmd() {
    docker exec $CONTAINER_ID gcloud "$@"
}

echo "Task 1: Creating multiple subscriptions on a topic"
echo "------------------------------------------------"
run_cmd pubsub topics create input-topic
run_cmd pubsub subscriptions create input-subscription --topic=input-topic
run_cmd pubsub subscriptions create input-subscription-backup --topic=input-topic
echo "Check both subscriptions exist:"
run_cmd pubsub subscriptions list
pause

echo "Task 2: Publishing messages with different key attributes"
echo "-----------------------------------------------------"
run_cmd pubsub topics publish input-topic --message="Message 1" --attribute=key=A
run_cmd pubsub topics publish input-topic --message="Message 2" --attribute=key=A
run_cmd pubsub topics publish input-topic --message="Message 3" --attribute=key=B
run_cmd pubsub topics publish input-topic --message="Message 4" --attribute=key=B
run_cmd pubsub topics publish input-topic --message="Message 5" --attribute=key=C
run_cmd pubsub topics publish input-topic --message="Message 6" --attribute=key=C
echo "6 messages published with different keys"
pause

echo "Task 3: Testing message acknowledgment"
echo "-----------------------------------"
echo "Pulling messages without auto-ack:"
run_cmd pubsub subscriptions pull input-subscription --limit=3
pause

echo "Task 4: Creating second subscription and testing message distribution"
echo "----------------------------------------------------------------"
run_cmd pubsub subscriptions create input-subscription-2 --topic=input-topic
run_cmd pubsub topics publish input-topic --message="New Message" --attribute=key=X
echo "Pulling from first subscription:"
run_cmd pubsub subscriptions pull input-subscription --limit=1
echo "Pulling from second subscription:"
run_cmd pubsub subscriptions pull input-subscription-2 --limit=1
pause

echo "Task 5: Testing filtered subscription"
echo "---------------------------------"
run_cmd pubsub subscriptions create filtered-subscription --topic=input-topic --message-filter='attributes.key="A"'
run_cmd pubsub topics publish input-topic --message="Should be filtered" --attribute=key=B
run_cmd pubsub topics publish input-topic --message="Should appear" --attribute=key=A
echo "Pulling from filtered subscription:"
run_cmd pubsub subscriptions pull filtered-subscription --limit=1
pause

echo "Task 6: Testing message redelivery"
echo "-------------------------------"
echo "Pulling messages without acknowledging:"
run_cmd pubsub subscriptions pull input-subscription --limit=2
echo "Waiting 10 seconds for ack deadline to expire..."
sleep 10
echo "Pulling again to see redelivered messages:"
run_cmd pubsub subscriptions pull input-subscription --limit=2
pause

echo "All tasks completed!"
