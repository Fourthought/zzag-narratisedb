#!/bin/bash
# Ingest MAIB reports from docs/maib_links.json
# Usage: ./scripts/ingest-from-links.sh [limit]
# Default limit: 10

set -e

API_URL="${API_URL:-http://localhost:8000}"
LIMIT="${1:-10}"
LINKS_FILE="docs/maib_links.json"

urls=$(python3 -c "
import json, sys
with open('$LINKS_FILE') as f:
    links = json.load(f)
for link in links[:$LIMIT]:
    print(link['url'])
")

total=$(echo "$urls" | wc -l | tr -d ' ')
count=0

while IFS= read -r url; do
    count=$((count + 1))
    echo "[$count/$total] $url"
    response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/documents/from-url" \
        -H "Content-Type: application/json" \
        -d "{\"url\": \"$url\"}")
    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | head -1)
    if [ "$http_code" = "200" ]; then
        title=$(echo "$body" | python3 -c "import json,sys; print(json.load(sys.stdin)['title'][:60])" 2>/dev/null || echo "?")
        echo "  OK: $title"
    elif [ "$http_code" = "409" ]; then
        echo "  SKIP: already exists"
    else
        echo "  ERROR $http_code: $body"
    fi
    echo
done <<< "$urls"

echo "Done. $count reports processed."
