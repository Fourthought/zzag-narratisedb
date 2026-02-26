#!/bin/bash
# Fetch a reconstructed document from the CHIRPdb API
# Usage: ./scripts/get-document.sh <document-id> [min-relevance]

set -e

API_URL="${API_URL:-http://localhost:8000}"

if [ -z "$1" ]; then
  echo "Usage: $0 <document-id> [min-relevance]"
  echo "Example: $0 1 1  # Get document 1, filtering out relevance 0 (TOC)"
  exit 1
fi

DOC_ID="$1"
MIN_RELEVANCE="$2"

URL="$API_URL/documents/$DOC_ID/full"
if [ -n "$MIN_RELEVANCE" ]; then
  URL="$URL?min_relevance=$MIN_RELEVANCE"
fi

echo "Fetching $URL..."
curl -s "$URL"
