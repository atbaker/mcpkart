#!/bin/bash
# Start Temporal server using Docker (development mode)

echo "Starting Temporal server..."
docker run -d \
    --name temporal \
    -p 7233:7233 \
    -e DB=sqlite \
    temporalio/auto-setup:latest

echo "Starting Temporal UI..."
docker run -d \
    --name temporal-ui \
    -p 8080:8080 \
    -e TEMPORAL_ADDRESS=host.docker.internal:7233 \
    --add-host=host.docker.internal:host-gateway \
    temporalio/ui:latest

echo ""
echo "Temporal server started!"
echo "  - gRPC: localhost:7233"
echo "  - Web UI: http://localhost:8080"
echo ""
echo "To stop: docker stop temporal temporal-ui && docker rm temporal temporal-ui"
