# Stack Exchange Data Pipeline

This project implements a data pipeline that fetches top posts from Stack Exchange API and processes them using Google Cloud Pub/Sub.

## Components

- **Producer**: Fetches top posts from Stack Exchange API and publishes them to a Pub/Sub topic
- **Consumer**: Subscribes to the Pub/Sub topic and processes incoming messages

## Prerequisites

- Google Cloud SDK
- Docker
- Access to Google Cloud Project
- Configured gcloud authentication

## Local Development

1. Build the Docker images:
```bash
# Build producer
cd producer
docker build -t lab1-producer .

# Build consumer
cd ../consumer
docker build -t lab1-consumer .
```

2. Run locally with Docker:
```bash
# Create network
docker network create stackexchange-network

# Run producer
docker run -v $HOME/.config/gcloud:/root/.config/gcloud \
           -v $HOME/.config/application_default_credentials.json:/root/.config/application_default_credentials.json \
           -e PROJECT_ID=your-project-id \
           -e PUBSUB_TOPIC=your-topic \
           lab1-producer

# Run consumer
docker run -v $HOME/.config/gcloud:/root/.config/gcloud \
           -v $HOME/.config/application_default_credentials.json:/root/.config/application_default_credentials.json \
           -e PROJECT_ID=your-project-id \
           -e PUBSUB_SUBSCRIPTION=your-subscription \
           lab1-consumer
```

## Deployment to Cloud Run

1. Tag and push images to Artifact Registry:
```bash
# Producer
docker tag lab1-producer $GCP_REGION-docker.pkg.dev/$PROJECT_ID/stack-exchange-repo/lab1-producer:latest
docker push $GCP_REGION-docker.pkg.dev/$PROJECT_ID/stack-exchange-repo/lab1-producer:latest

# Consumer
docker tag lab1-consumer $GCP_REGION-docker.pkg.dev/$PROJECT_ID/stack-exchange-repo/lab1-consumer:latest
docker push $GCP_REGION-docker.pkg.dev/$PROJECT_ID/stack-exchange-repo/lab1-consumer:latest
```

2. Create secrets in Secret Manager:
```bash
# Create secrets from .env file
gcloud secrets create stack-exchange-secrets --data-file=.env
```

3. Deploy to Cloud Run:
```bash
# Deploy producer
gcloud run deploy lab1-producer \
  --image=$GCP_REGION-docker.pkg.dev/$PROJECT_ID/stack-exchange-repo/lab1-producer:latest \
  --region=$GCP_REGION \
  --set-secrets=STACK_EXCHANGE_API_KEY=stack-exchange-secrets:latest

# Deploy consumer
gcloud run deploy lab1-consumer \
  --image=$GCP_REGION-docker.pkg.dev/$PROJECT_ID/stack-exchange-repo/lab1-consumer:latest \
  --region=$GCP_REGION \
  --set-secrets=STACK_EXCHANGE_API_KEY=stack-exchange-secrets:latest
```

## Environment Variables

- `PROJECT_ID`: Google Cloud Project ID
- `PUBSUB_TOPIC`: Pub/Sub topic name
- `PUBSUB_SUBSCRIPTION`: Pub/Sub subscription name
- `STACK_EXCHANGE_API_KEY`: Stack Exchange API key (stored in Secret Manager)

## Security

- Secrets are managed using Google Cloud Secret Manager
- Service accounts with minimal permissions are used
- Environment variables are securely passed through Cloud Run