#!/bin/bash

# Deployment script for DataDrift ETL Pipeline

set -e

echo "🚀 Deploying DataDrift ETL Pipeline..."

# Check if Serverless is installed
if ! command -v serverless &> /dev/null; then
    echo "❌ Serverless Framework not found. Installing..."
    npm install -g serverless
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Deploy
echo "📤 Deploying to AWS..."
serverless deploy

# Get deployment info
BUCKET_NAME=$(serverless info --verbose | grep -A 2 "DataDriftBucket" | grep "BucketName" | awk '{print $2}')
echo ""
echo "✅ Deployment Complete!"
echo "📊 S3 Bucket: $BUCKET_NAME"
echo "🔍 Athena Database: data_drift_db"
echo ""
echo "To test the pipeline:"
echo "  npm run invoke:extract"
echo ""
echo "To run SQL queries, go to Athena Console and select database: data_drift_db"