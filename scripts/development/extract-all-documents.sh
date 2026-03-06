#!/bin/bash
# Fetch full text for all documents and save to output/{id}.txt
# Usage: ./scripts/extract-all-documents.sh

set -e

API_URL="${API_URL:-http://localhost:8000}"

mkdir -p output

ids=$(curl -s "$API_URL/documents" | python3 -c "
import json, sys
docs = json.load(sys.stdin)
for doc in docs:
    print(doc['id'])
")

total=$(echo "$ids" | grep -c . || true)
count=0

while IFS= read -r id; do
    count=$((count + 1))
    echo "[$count/$total] $id"
    curl -s "$API_URL/documents/$id/full" -o "output/$id.txt"
done <<< "$ids"

echo "Done. $count documents extracted to output/."
