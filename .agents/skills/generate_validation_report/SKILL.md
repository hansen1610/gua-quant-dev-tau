---
name: Generate Validation Report
description: Validates technical points in a document using web searches and generates a true/false table report.
---

# Skill: Generate Validation Report

This skill extracts technical claims or points from a given document, validates them against authoritative sources on the web, and generates a structured true/false report table.

## Context
When reading technical guides, AI-generated content, or raw exports, users often need to verify the factual accuracy of the information before trusting it. This skill automates the fact-checking process.

## Execution Steps

1. **Extraction**:
   - Read the target technical document or guide provided by the user.
   - Extract the core technical claims, definitions, or procedural steps that require validation (usually 5-10 key points).

2. **Web Search Validation**:
   - Use the `search_web` tool to query authoritative sources for each extracted point.
   - Analyze the web search results to determine if the claim is factually accurate according to industry standards or literature.

3. **Report Generation**:
   - Create a markdown table with three columns: 
     - **Poin di Panduan** (The extracted point)
     - **Status Validasi** (✅ BENAR or ❌ SALAH)
     - **Penjelasan / Bukti dari Web Search** (A brief explanation or evidence found from the search).
   - Write this table into a new artifact file named `validation_report.md` (or similar depending on user preference).
   - Ensure the report is concise and objective.

4. **Delivery**:
   - Notify the user that the validation is complete and provide a link to the generated report.
