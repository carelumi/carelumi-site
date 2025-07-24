import boto3
from pathlib import Path
import io
import json
from botocore.exceptions import NoCredentialsError
import schema


s3 = boto3.client('s3')
local_json_base_path = "data/organization_jsons/"

BUCKET_NAME = "carelumi-data"


def upload_to_s3(file_obj, bucket_name: str, s3_key: str):
    """
    Uploads a file-like object to a private S3 bucket and returns the internal S3 path.
    """

    if isinstance(file_obj, dict):
        obj = io.BytesIO(json.dumps(obj).encode("utf-8"))
    #Handle text exratcion .json type(dict type)

    file_obj.seek(0)
    s3.upload_fileobj(file_obj, bucket_name, s3_key)

    return f"s3://{bucket_name}/{s3_key}"

def get_s3_json_key(organization_id: str) -> str:
    # This creates the S3 path for the queried organization 
    return f"organization/{organization_id}/admin_metadata.json"

def read_s3_json(organization_id: str) -> list:
    """ Read the JSON file from S3 if it exists, otherwise return an empty list. """
    
    s3_key = get_s3_json_key(organization_id)
    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        json_data = response['Body'].read().decode('utf-8')
        return json.loads(json_data)
    except s3.exceptions.NoSuchKey:
        empty_data = []
        s3.put_object(Body=json.dumps(empty_data, indent=4), Bucket=BUCKET_NAME, Key=s3_key)
        return empty_data
    except NoCredentialsError:
        raise Exception("Credentials not available for accessing S3.")
    except Exception as e:
        raise Exception(f"Error reading from S3: {str(e)}")

def write_s3_json(organization_id: str, data: list):
    """ Write the updated JSON data to the S3 bucket under the organization's directory. """
    s3_key = get_s3_json_key(organization_id)
    try:
        json_data = json.dumps(data, indent=4)
        s3.put_object(Body=json_data, Bucket=BUCKET_NAME, Key=s3_key)
    except NoCredentialsError:
        raise Exception("Credentials not available for accessing S3.")
    except Exception as e:
        raise Exception(f"Error uploading to S3: {str(e)}")

def update_by_user(user: schema.User):
    try:
        admin_data = read_s3_json(user.organization_id)

        # Prepare the new staff data to append
        new_staff_data = {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "role": user.role,
            "permission": user.permission,
            "organization_id": user.organization_id
        }

        # Append the new staff data
        admin_data.append(new_staff_data)

        # Write the updated data back to S3
        write_s3_json(user.organization_id, admin_data)
    except Exception as e:
        raise Exception(f"Error updating new user data in S3: {str(e)}")


    