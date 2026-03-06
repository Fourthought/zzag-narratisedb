#!/bin/bash
# Fetch reconstructed full text for a document and save to a .txt file
# Usage: ./scripts/get-full-text.sh <document-id>

set -e

API_URL="${API_URL:-http://localhost:8000}"
DOC_ID="${1:?Usage: $0 <document-id>}"
OUTPUT_FILE="output/${DOC_ID}.txt"

mkdir -p output

curl -s "$API_URL/documents/$DOC_ID/full" -o "$OUTPUT_FILE"
echo "Saved to $OUTPUT_FILE"
