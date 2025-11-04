#!/usr/bin/env bash
set -euo pipefail

# Usage: docker-ps-json.sh <info|summary>
# - info    => prints full JSON array of containers
# - summary => prints summary JSON object

if [ "${#}" -ne 1 ]; then
  echo '{"error":"usage: docker-ps-json.sh <info|summary>"}' >&2
  exit 2
fi

mode=$1

# Produce the full JSON array of containers
json_data=$(docker ps -a --format '{
  "Name": "{{.Names}}",
  "Status": "{{.Status}}",
  "Image": "{{.Image}}",
  "Ports": "{{.Ports}}",
  "Stack": "{{.Label `com.docker.compose.project`}}",
  "Service": "{{.Label `com.docker.compose.service`}}",
  "Mounts": "{{.Mounts}}",
  "Networks": "{{.Networks}}",
  "CreatedAt": "{{.CreatedAt}}"
}' | jq -s .)

# Compute summary from the json_data
summary=$(echo "$json_data" | jq '
  group_by(.Stack) |
  map({
    stack: (.[0].Stack // "no_stack"),
    total: length,
    running: (map(select(.Status | contains("Up"))) | length)
  }) |
  {
    total_stacks: (map(.stack) | unique | length),
    healthy_stacks: (map(select(.running == .total)) | length),
    unhealthy_stacks: (map(select(.running != .total)) | length),
    error_nodes: (reduce .[] as $s (0; . + ($s.total - $s.running)))
  }
')

case "$mode" in
  info)
    # Print JSON array of containers
    echo "$json_data"
    ;;
  summary)
    # Print JSON object summary
    echo "$summary"
    ;;
  *)
    echo '{"error":"invalid mode; use info or summary"}' >&2
    exit 2
    ;;
esac
