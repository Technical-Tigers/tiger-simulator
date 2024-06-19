SCHEDULER_NAME=$(cd scheduler/repo && git rev-parse --abbrev-ref HEAD)
export SCHEDULER_NAME
docker compose up