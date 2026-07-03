import json
import boto3
import urllib3
import os
from datetime import datetime

s3_client = boto3.client('s3')
http = urllib3.PoolManager()

BUCKET_NAME = os.environ['BUCKET_NAME']
API_URL = os.environ['API_URL']

def main(event, context):
    """
    Extract Lambda: Fetches product data from DummyJSON API and stores raw JSON in S3
    """
    print(f"Fetching data from {API_URL}")
    
    try:
        # Fetch data from API
        response = http.request('GET', API_URL)
        
        if response.status != 200:
            raise Exception(f"API returned status {response.status}")
        
        data = json.loads(response.data.decode('utf-8'))
        
        # Generate timestamp for the file
        timestamp = datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')
        file_key = f"raw/products_{timestamp}.json"
        
        # Upload to S3
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=file_key,
            Body=json.dumps(data, indent=2),
            ContentType='application/json'
        )
        
        print(f"Successfully uploaded {file_key} to {BUCKET_NAME}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Extract completed successfully',
                'file': file_key,
                'record_count': len(data.get('products', []))
            })
        }
    
    except Exception as e:
        print(f"Error in extract: {str(e)}")
        raise e