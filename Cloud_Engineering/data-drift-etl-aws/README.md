# DataDrift: Automated Product Data Lake with Athena SQL

## 🎯 Project Overview

DataDrift is a serverless ETL pipeline that extracts product data from the DummyJSON API, transforms it, and makes it available for SQL analytics using Amazon Athena. The entire infrastructure is defined as code using the Serverless Framework.

## 🏗️ Architecture
```
┌─────────────┐
│ Manual      │ (Invoke Extract)
│ Trigger     │
└───────┬─────┘
        │
        ▼
┌─────────┐
│ Lambda: │
│ Extract │──► Fetches products from DummyJSON API
└────────┬┘
         │
         ▼
┌─────────────────┐
│ S3 Bucket       │
│ /raw/           │──► Stores raw JSON files
└───────┬─────────┘
        │ (S3 Event Trigger)
        ▼
┌─────────────────┐
│ Lambda:         │
│ Transform       │──► Converts JSON → CSV, flattens nested fields
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ S3 Bucket       │
│ /processed/     │──► Stores cleaned CSV files
└────────┬────────┘
         │ (Glue Crawler)
         ▼
┌─────────────────┐
│ Glue Data       │
│ Catalog         │──► Creates table schema for Athena
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Amazon Athena   │──► Run SQL queries on product data
└─────────────────┘
```


## 🚀 Tech Stack

- **Compute**: AWS Lambda (Python 3.11)
- **Storage**: Amazon S3 (Data Lake)
- **Orchestration**: Manual Lambda invocation followed by an S3 event trigger
- **Catalog**: AWS Glue Data Catalog
- **Query**: Amazon Athena (Serverless SQL)
- **IaC**: Serverless Framework

## 📊 Data Schema

The transformed CSV includes the following fields:
- id, title, description, price, discount_percentage
- rating, stock, brand, category, thumbnail
- images_count, tags, sku, weight
- width, height, depth (from dimensions)
- warranty_information, shipping_information
- availability_status, return_policy
- minimum_order_quantity, created_at

## 🛠️ Prerequisites

- AWS Account with Admin credentials
- Node.js 16+ and npm
- Python 3.11+
- Serverless Framework installed globally:
  ```bash
  npm install -g serverless
  ```
- AWS CLI configured:
    ``` bash
    aws configure
    ```

## 📦 Installation & Deployment
### 1. Clone the Repository
``` bash
    git clone https://github.com/your-username/data-drift-etl-aws.git
    cd data-drift-etl-aws
```

### 2. Install Dependencies 
``` bash
    git clone https://github.com/your-username/data-drift-etl-aws.git
    cd data-drift-etl-aws
```
### 3. Deploy to AWS 
```
    # Deploy to dev stage
    npm run deploy

    # Deploy to production stage
    npm run deploy:prod
``` 
### 4. Test the Pipeline
#### Manually invoke the Extract Lambda: 
```bash 
    npm run invoke:extract
```
#### Check the logs: 
```bash 
    # Tail Extract Lambda logs
    npm run logs:extract

    # Tail Transform Lambda logs
    npm run logs:transform
```
### 5. Verify Data in S3
- Go to S3 Console → Your bucket (data-drift-dev-{accountId})
- Check `raw/` folder for JSON files
- Check `processed/` folder for CSV files
### 6. Run SQL Queries in Athena 
#### 1. Go to AWS Athena Console
#### 2. Set database to data_drift_db
#### 3. Run sample queries from athena/sample-queries.sql

## 📈 Sample SQL Queries
``` sql
-- Top 10 most expensive products
SELECT title, brand, price, rating 
FROM "data_drift_db"."products" 
ORDER BY price DESC 
LIMIT 10;

-- Count products by category
SELECT category, COUNT(*) as product_count 
FROM "data_drift_db"."products" 
GROUP BY category 
ORDER BY product_count DESC;

-- Products with high rating and low price
SELECT title, brand, price, rating, 
       ROUND(rating / price, 4) as value_score
FROM "data_drift_db"."products" 
WHERE price > 0
ORDER BY value_score DESC 
LIMIT 10;
```
##🧹 Clean Up
To remove all resources and avoid charges:
```bash 
npm run remove
```

### 📂 Project Structure
```text
data-drift-etl-aws/
├── serverless.yml              # Infrastructure as Code
├── package.json                # Serverless dependencies
├── lambdas/
│   ├── extract/
│   │   └── handler.py         # Extract Lambda
│   └── transform/
│       └── handler.py         # Transform Lambda
├── athena/
│   └── sample-queries.sql     # Example SQL queries
├── .gitignore
└── README.md
```

## 🔒 Security
- All IAM roles follow the principle of least privilege
- S3 bucket has versioning enabled
- Bucket lifecycle policy archives raw files after 30 days
- Environment variables for API endpoints and bucket names

## 📊 Cost Management
This pipeline uses AWS Always Free tier services:

- Lambda: 1M requests/month free
- S3: 5GB storage free
- Glue Data Catalog: Free
- Athena: Pay per query (minimal for this use case)

Estimated monthly cost: < $1