#!/bin/bash

# Export environment variables
export PUBSUB_EMULATOR_HOST=localhost:8085
export PUBSUB_PROJECT_ID=local-project

# Start Docker Emulator
echo "Starting Pub/Sub emulator in Docker..."
docker compose up -d pubsub-emulator

echo "Waiting 5 seconds for emulator to start..."
sleep 5

# Get container ID
CONTAINER_ID=$(docker compose ps -q pubsub-emulator)

# Config gcloud and create resources inside the container
echo "Config gcloud and creating resources..."
docker exec $CONTAINER_ID bash -c '
    gcloud config set auth/disable_credentials true &&
    gcloud config set project local-project &&
    gcloud config set api_endpoint_overrides/pubsub http://localhost:8085/ &&
    
    # Create topic if it does not exist
    if ! gcloud pubsub topics list | grep -q my-topic; then
        echo "Creating topic: my-topic..."
        gcloud pubsub topics create my-topic
    else
        echo "Topic my-topic already exists"
    fi &&
    
    # Create subscription if it does not exist
    if ! gcloud pubsub subscriptions list | grep -q my-subscription; then
        echo "Creating subscription: my-subscription..."
        gcloud pubsub subscriptions create my-subscription --topic=my-topic
    else
        echo "Subscription my-subscription already exists"
    fi
'

echo ""
echo "Emulator has started and is ready for sending messages!"
echo ""
echo "To send messages, use:"
echo "docker exec $CONTAINER_ID gcloud pubsub topics publish my-topic --message='Your message'"
echo ""
echo "To receive messages, use:"
echo "docker exec $CONTAINER_ID gcloud pubsub subscriptions pull my-subscription --auto-ack --limit=10"
echo ""
echo "To stop emulator use:"
echo "docker-compose down"

# Export container ID as a variable and create function for easier usage
export PUBSUB_CONTAINER="${CONTAINER_ID}"

# Create a function that will be available in the shell
cat << 'EOF' > ~/.xo_function
xo() {
    docker exec $PUBSUB_CONTAINER gcloud "$@"
}
EOF

# Source the function in current shell and add to .bashrc if not already there
source ~/.xo_function
if ! grep -q "source ~/.xo_function" ~/.bashrc; then
    echo "source ~/.xo_function" >> ~/.bashrc
fi

echo ""
echo "Shortcuts created!"
echo "You can now use:"
echo "xo pubsub topics publish my-topic --message='Your message'"
echo "xo pubsub subscriptions pull my-subscription --auto-ack --limit=10"
echo ""
echo "Or use PUBSUB_CONTAINER variable:"
echo "docker exec \${PUBSUB_CONTAINER} gcloud ..."

# Keep the shell open with the environment variables set    
exec $SHELL