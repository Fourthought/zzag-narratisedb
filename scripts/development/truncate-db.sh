#!/bin/bash
# Truncate all non-reference tables and reset sequences

psql postgresql://postgres:postgres@127.0.0.1:54322/postgres -c "TRUNCATE authors, analysis, chirp_analysis_shield_codes, chirp_organisations, chirp_recommendations, chirp_accident_metadata, chirp_safety_issue_legislation, chirp_safety_issues, documents, sentences RESTART IDENTITY CASCADE;"
echo "Database truncated."
