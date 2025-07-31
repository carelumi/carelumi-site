import requests

def notify_data_extraction(ec2_url: str, org_id: str, user_id: str, doc_id: str):
    payload = {
        "organization_id": org_id,
        "user_id": user_id,
        "document_id": doc_id
    }
    try:
        resp = requests.post(f"{ec2_url}/extract", json=payload)
        print(f"Triggered extraction: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Failed to notify second EC2: {e}")
