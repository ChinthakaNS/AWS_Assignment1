# handler.py
import os
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb').Table(os.environ['DYNAMODB_TABLE_NAME'])

def process_message(event, context):
    try:
        logger.info("Received event: %s", event)

        if 'body' not in event or not event['body']:
            raise ValueError('Invalid request format: Body is missing.')

        message = json.loads(event['body'])

        # Validate the message
        if not validate_message(message):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid message format'}),
            }

        # Save to S3
        save_to_s3(message)

        # Save to DynamoDB
        save_to_dynamodb(message)

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Message processed successfully'}),
        }
    except ValueError as ve:
        logger.error("ValueError: %s", ve)
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(ve)}),
        }
    except Exception as e:
        logger.error("Error processing message: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal Server Error'}),
        }

def validate_message(message):
    # Implement your validation logic here
    return (
        message and
        message.get('metadata') and
        message['metadata'].get('message_time') and
        message['metadata'].get('company_id') and
        message['metadata'].get('message_id')
    )

def save_to_s3(message):
    try:
        bucket_name = f'{os.environ["S3_BUCKET_NAME"]}'
        key = f'{message["metadata"]["message_id"]}.json'
        s3.put_object(Body=json.dumps(message), Bucket=bucket_name, Key=key)
        logger.info("Saved message to S3: %s", key)
    except Exception as e:
        logger.error("Error saving message to S3: %s", str(e))
        raise

def save_to_dynamodb(message):
    try:
        dynamodb.put_item(
            Item={
                'message_id': message['metadata']['message_id'],
                'company_id': message['metadata']['company_id'],
                # Add other metadata fields as needed
            }
        )
        logger.info("Saved message to DynamoDB: %s", message['metadata']['message_id'])
    except Exception as e:
        logger.error("Error saving message to DynamoDB: %s", str(e))
        raise
