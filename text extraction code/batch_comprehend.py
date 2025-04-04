import boto3
import json
import os

# AWS Configuration
s3_client = boto3.client('s3')
comprehend_client = boto3.client('comprehend')

bucket_name = "resume-pro-bucket-1"  # Change to your actual S3 bucket name
input_folder = "extracted_resumes"  # Folder where resumes are stored
output_folder = "redacted-resumes"  # Folder to save redacted resumes

# Function to redact PII using AWS Comprehend
def redact_pii(text):
    response = comprehend_client.detect_pii_entities(Text=text, LanguageCode='en')
    
    pii_entities = response.get("Entities", [])
    redacted_text = text

    # Replace detected PII with "[REDACTED]"
    for entity in pii_entities:
        redacted_text = redacted_text.replace(
            text[entity["BeginOffset"]:entity["EndOffset"]], "[REDACTED]"
        )

    return redacted_text

# Function to process all resumes from S3
def process_resumes():
    print(f"Checking for files in s3://{bucket_name}/{input_folder}/...")
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=input_folder)

    if 'Contents' not in response:
        print("No files found in S3. Please check if they are uploaded.")
        return

    for obj in response['Contents']:
        file_name = os.path.basename(obj['Key'])
        if file_name.endswith(".txt"):
            print(f"Processing: {file_name}")

            # Download the resume text from S3
            s3_object = s3_client.get_object(Bucket=bucket_name, Key=obj['Key'])
            resume_text = s3_object['Body'].read().decode('utf-8')

            # Redact PII from the resume
            redacted_text = redact_pii(resume_text)

            # Save the redacted file back to S3
            redacted_file_key = f"{output_folder}/{file_name}"
            s3_client.put_object(
                Bucket=bucket_name, Key=redacted_file_key, Body=redacted_text.encode('utf-8')
            )

            print(f"Redacted file saved: s3://{bucket_name}/{redacted_file_key}")

# Run the batch processing
process_resumes()
