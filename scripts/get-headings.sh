#!/bin/bash
# Get all headings for a document
# Usage: ./scripts/get-headings.sh <document-id>

API_URL="${API_URL:-http://localhost:8000}"

if [ -z "$1" ]; then
  echo "Usage: $0 <document-id>"
  exit 1
fi

curl -s "$API_URL/documents/$1/headings" | jq -r '.[] | "\(.position): \(.text)"'
