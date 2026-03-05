#!/bin/bash
# Ingest all PDFs in the samples folder

set -e

for pdf in samples/*.pdf; do
  echo "--- Ingesting $pdf ---"
  ./scripts/ingest-pdf.sh "$pdf" || true
  echo
done
