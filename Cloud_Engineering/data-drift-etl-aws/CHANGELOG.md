All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to Semantic Versioning principles where applicable.

---
### ✨ Added [0.3.0] - 2026-06-06

- Add Serverless Framework configuration with S3, Lambda, Glue, EventBridge
- Implement extract Lambda to fetch product data from DummyJSON API
- Implement transform Lambda to convert JSON to CSV with flattened schema
- Set up Glue Data Catalog and Crawler for Athena queries
- Add sample SQL queries for product analytics
- Configure daily schedule at 9 PM with EventBridge cron
- Add S3 lifecycle policies for raw data retention (30 days)
- Include IAM roles with least-privilege permissions
- Add deployment scripts and documentation

Tech Stack: AWS Lambda, S3, Glue, Athena, EventBridge, Serverless Framework