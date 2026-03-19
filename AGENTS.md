# AGENTS.md

## Project Overview
Ads Data Collector V1 for mobile game marketing analysis.

## Goal
Build a modular ad data collection system that extracts structured metadata from:
- TikTok Creative Center
- Facebook Ads Library

The system stores cleaned records in Postgres for downstream analysis and creative generation.

## Non-Goals
- Do not download or store video assets
- Do not build a distributed crawler in V1
- Do not implement ad delivery automation

## Tech Stack
- Python 3.10+
- Playwright
- PostgreSQL
- pytest

## Architecture
1. Scraper layer collects raw page content
2. Parser layer extracts structured fields
3. Cleaning and deduplication normalize records
4. Storage layer writes to Postgres
5. Analyzer layer prepares output for Excel or AI workflows

## Core Data Model
Target table: `ads_creative`

Fields:
- `platform`
- `game_name`
- `hook`
- `creative_type`
- `country`
- `first_seen`
- `last_seen`
- `created_at`

## Coding Rules
- Use Python 3.10+
- Use Playwright for scraping
- Use Postgres for storage
- Keep modules loosely coupled and testable
- Prefer clear, extensible interfaces over hardcoded logic
- Log all important failures and edge cases

## Constraints
- Only collect structured metadata
- Do not scrape video binary content
- Prioritize data integrity over crawl volume
- Prevent duplicate writes

## Required Modules
1. `scraper/` for browser automation and DOM collection
2. `parser/` for field extraction and normalization
3. `storage/` for Postgres access and deduplication
4. `analyzer/` for hook classification and simple trend tagging

## Deduplication
- V1 dedup key: `hook + platform`
- Prefer enforcing dedup both in application logic and database constraints

## Logging
- Log crawler start and finish
- Log page load and parse failures
- Log database write failures
- Log dedup hit counts when possible

## Testing
- Basic scraping test must collect at least 10 records
- Parsed key fields should not be empty
- System should run continuously for 30 minutes with at least 80% success rate
- Parsed text should be readable and free of garbled characters

## Implementation Tasks
1. Implement scraper
2. Implement parser
3. Implement storage
4. Ensure deduplication
5. Add basic logging
6. Add basic tests

## Recommended Project Structure
```text
ads_collector/
├── scraper/
│   └── playwright_scraper.py
├── parser/
│   └── parser.py
├── storage/
│   └── db.py
├── analyzer/
│   └── hook_classifier.py
├── config/
│   └── config.yaml
├── tests/
│   └── test_scraper.py
├── main.py
└── AGENTS.md
```

## Agent Priorities
1. Preserve data completeness
2. Record exceptions with logs
3. Never allow duplicate writes
4. Keep every module independently testable
5. Maintain extensibility for future platforms and fields
