# Google Cloud Pub/Sub Lab Report

## Task 1: Multiple Subscriptions on a Topic
### Commands Used
```bash
# Create topic and subscriptions
xo pubsub topics create input-topic
xo pubsub subscriptions create input-subscription --topic=input-topic
xo pubsub subscriptions create input-subscription-backup --topic=input-topic
```

### Findings
- Multiple subscriptions can be created on the same topic
- Each subscription receives a copy of all messages published to the topic
- Subscriptions work independently - acknowledging a message in one subscription doesn't affect others
- This demonstrates the fan-out capability of Pub/Sub

## Task 2: Publishing Messages with Attributes
### Commands Used
```bash
# Publish messages with different key attributes
xo pubsub topics publish input-topic --message="Message 1" --attributes=key=A
xo pubsub topics publish input-topic --message="Message 2" --attributes=key=A
xo pubsub topics publish input-topic --message="Message 3" --attributes=key=B
xo pubsub topics publish input-topic --message="Message 4" --attributes=key=B
xo pubsub topics publish input-topic --message="Message 5" --attributes=key=C
xo pubsub topics publish input-topic --message="Message 6" --attributes=key=C
```

### Findings
- Messages with the same key are not grouped or ordered by default
- Each message is treated independently regardless of key value
- Keys serve as metadata and can be used for filtering but don't affect basic delivery

## Task 3: Message Acknowledgment Behavior
### Commands Used
```bash
# Pull messages without auto-ack
xo pubsub subscriptions pull input-subscription --limit=3
```

### Findings
- Unacknowledged messages become available for re-delivery after the ack deadline
- Default ack deadline is typically 10-60 seconds
- Messages can be pulled multiple times until acknowledged
- This ensures at-least-once delivery semantics

## Task 4: Multiple Subscriptions and Message Distribution
### Commands Used
```bash
# Create second subscription and publish new messages
xo pubsub subscriptions create input-subscription-2 --topic=input-topic
xo pubsub topics publish input-topic --message="New Message" --attributes=key=X
```

### Findings
- New subscriptions only receive messages published after their creation
- Each subscription gets its own copy of messages
- Demonstrates loose coupling:
  - Publishers don't know about subscribers
  - Subscribers don't know about each other
  - Multiple consumer groups can process same data independently

## Task 5: Filtered Subscriptions
### Commands Used
```bash
# Create filtered subscription
xo pubsub subscriptions create filtered-subscription --topic=input-topic --filter="attributes.key = \"A\""
```

### Findings
- Filtered subscriptions only receive messages matching the filter
- Filters work on message attributes
- Non-matching messages are dropped before reaching the subscription
- Filtering happens at the Pub/Sub service level, not client-side

## Task 6: Message Redelivery
### Commands Used
```bash
# Pull without auto-ack and observe redelivery
xo pubsub subscriptions pull input-subscription --limit=2
# Wait for ack deadline to expire
sleep 60
# Pull again to see redelivered messages
xo pubsub subscriptions pull input-subscription --limit=2
```

### Findings
- Unacknowledged messages return to the subscription after ack deadline
- Messages maintain their original attributes during redelivery
- Redelivery continues until message is acknowledged or expires
- This provides reliability in case of consumer failures