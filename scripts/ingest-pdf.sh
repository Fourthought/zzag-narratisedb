#!/bin/bash
# Ingest a PDF document via the CHIRPdb API
# Usage: ./scripts/ingest-pdf.sh <path-to-pdf>

set -e

API_URL="${API_URL:-http://localhost:8000}"

if [ -z "$1" ]; then
  echo "Usage: $0 <path-to-pdf>"
  exit 1
fi

PDF_PATH="$1"

if [ ! -f "$PDF_PATH" ]; then
  echo "Error: File not found: $PDF_PATH"
  exit 1
fi

echo "Truncating database..."
psql postgresql://postgres:postgres@127.0.0.1:54322/postgres -c "TRUNCATE authors, chirp_analysis, chirp_analysis_shield_codes, chirp_organisations, chirp_recommendations, chirp_report_metadata, chirp_safety_issue_sentences, chirp_safety_issues, documents, sections, sentences RESTART IDENTITY CASCADE;"

echo "Uploading $PDF_PATH to $API_URL/documents..."
curl -X POST "$API_URL/documents" \
  -F "file=@$PDF_PATH"
