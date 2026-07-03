import json
import boto3
import csv
import os
from datetime import datetime
from io import StringIO

s3_client = boto3.client('s3')

BUCKET_NAME = os.environ['BUCKET_NAME']

def transform_product(product):
    """
    Transform a single product from nested JSON to flat structure
    """
    return {
        'id': product.get('id', ''),
        'title': product.get('title', ''),
        'description': product.get('description', '').replace('\n', ' ').replace(',', ' '),
        'price': product.get('price', 0),
        'discount_percentage': product.get('discountPercentage', 0),
        'rating': product.get('rating', 0),
        'stock': product.get('stock', 0),
        'brand': product.get('brand', ''),
        'category': product.get('category', ''),
        'thumbnail': product.get('thumbnail', ''),
        'images_count': len(product.get('images', [])),
        'tags': ','.join(product.get('tags', [])),
        'sku': product.get('sku', ''),
        'weight': product.get('weight', 0),
        'width': product.get('dimensions', {}).get('width', 0),
        'height': product.get('dimensions', {}).get('height', 0),
        'depth': product.get('dimensions', {}).get('depth', 0),
        'warranty_information': product.get('warrantyInformation', ''),
        'shipping_information': product.get('shippingInformation', ''),
        'availability_status': product.get('availabilityStatus', ''),
        'return_policy': product.get('returnPolicy', ''),
        'minimum_order_quantity': product.get('minimumOrderQuantity', 0),
        'created_at': datetime.utcnow().isoformat()
    }

def main(event, context):
    """
    Transform Lambda: Reads raw JSON from S3, transforms to CSV, and saves to processed folder
    """
    try:
        # Get the S3 event details
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            print(f"Processing file: {key} from bucket: {bucket}")
            
            # Read JSON from S3
            response = s3_client.get_object(Bucket=bucket, Key=key)
            json_content = response['Body'].read().decode('utf-8')
            data = json.loads(json_content)
            
            products = data.get('products', [])
            print(f"Found {len(products)} products to transform")
            
            if not products:
                print("No products found in the file")
                continue
            
            # Transform products to CSV format
            transformed_products = [transform_product(p) for p in products]
            
            # Write to CSV in memory
            csv_buffer = StringIO()
            fieldnames = transformed_products[0].keys()
            writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(transformed_products)
            
            # Generate timestamp for processed file
            timestamp = datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')
            processed_key = f"processed/products_{timestamp}.csv"
            
            # Upload CSV to S3
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=processed_key,
                Body=csv_buffer.getvalue(),
                ContentType='text/csv'
            )
            
            print(f"Successfully uploaded transformed data to {processed_key}")
            
            # Log metrics
            print(f"Transformation Summary:")
            print(f"  - Original file: {key}")
            print(f"  - Processed file: {processed_key}")
            print(f"  - Products transformed: {len(transformed_products)}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Transform completed successfully'
            })
        }
    
    except Exception as e:
        print(f"Error in transform: {str(e)}")
        raise e