from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import database
import schema
import database_operations
import random
from openai import OpenAI
import os
from dotenv import load_dotenv
import requests
from syncS3 import upload_to_s3, write_s3_json, read_s3_json,update_by_user
from llm_placeholder import get_llm_response

os.makedirs("data", exist_ok=True)
SYSTEM_PROMPT = """
You are a meticulous healthcare-compliance analyst.
Your job is to read the text of a compliance form and decide whether it has been filled out correctly.
The user message will contain the complete form.
Sections will be separated by an html comment <!-- comment -->.
Some sections will be general instructions, others will contain fields that need to be filled out, and others should be left blank.
Your output should be in the following json format {"correct": boolean, "reasoning": string}
"""

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LANDING_AI_API_KEY = os.getenv("VISION_AGENT_API_KEY")

schema.Base.metadata.create_all(bind=database.engine)

active_tokens = {}
TOKEN_BITS = 32



def get_document_text(path: str) -> str:
    url = 'https://api.va.landing.ai/v1/tools/agentic-document-analysis'
    files = {'pdf': open(path, 'rb')}
    data = {
        'include_marginalia': 'true',
        'include_metadata_in_markdown': 'true',
    }
    headers = {
        'Authorization': f'Basic {LANDING_AI_API_KEY}'
    }

    response = requests.post(url, files=files, data=data, headers=headers)
    return response.json()


def get_token(user: schema.User):
    token = random.getrandbits(TOKEN_BITS)
    active_tokens[token] = user.id
    return token

def create_user_folder(user: schema.User, session: Session):
    folder = schema.Folder(
        name=f"{user.first_name} {user.last_name}",
        organization_id=user.organization_id,
        user_id=user.id
    )
    session.add(folder)
    session.commit()

# Use sqlalchemy asyncio in future
def get_session():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_staff(token: int = Header(..., alias="token"), session: Session = Depends(get_session)) -> schema.User:
    if token in active_tokens:
        return database_operations.get_user(session, active_tokens[token])
    raise HTTPException(status_code=403, detail="Invalid token.")

def get_admin(token: int = Header(..., alias="token"), session: Session = Depends(get_session)) -> schema.User:
    if token in active_tokens:
        user = database_operations.get_user(session, active_tokens[token])
        if user.permission == schema.Permission.ADMIN:
            return user
        raise HTTPException(status_code=403, detail="User does not have admin privileges")
    raise HTTPException(status_code=403, detail="Invalid token.")

@asynccontextmanager
async def load_demo_data(app: FastAPI):
    database.Base.metadata.drop_all(bind=database.engine)
    database.Base.metadata.create_all(bind=database.engine)
    organization = schema.Organization(name="Demo Organization")
    admin = schema.User(
        first_name="Alice",
        last_name="Scott",
        email="alice@example.com",
        password="password",
        role=schema.Role.ADMIN,
        permission=schema.Permission.ADMIN,
        organization=organization
    )
    staff1 = schema.User(
        first_name="Max",
        last_name="Smith",
        email="max@example.com",
        password="password",
        role=schema.Role.STAFF,
        permission=schema.Permission.STAFF,
        organization=organization
    )
    staff2 = schema.User(
        first_name="Jamie",
        last_name="Garcia",
        email="jamie@example.com",
        password="password",
        role=schema.Role.STAFF,
        permission=schema.Permission.STAFF,
        organization=organization
    )
    folder1 = schema.Folder(
        name=f"{admin.first_name} {admin.last_name}",
        organization=organization,
        user=admin
    )
    folder2 = schema.Folder(
        name=f"{staff1.first_name} {staff1.last_name}",
        organization=organization,
        user=staff1
    )
    folder3 = schema.Folder(
        name=f"{staff2.first_name} {staff2.last_name}",
        organization=organization,
        user=staff2
    )
    doc1 = schema.Document(
        name="Max's Training Certificate",
        link="http://example.com/max_training.pdf",
        organization=organization,
        folder=folder2,
    )
    doc2 = schema.Document(
        name="Jamie's Background Check",
        link="http://example.com/jamie_background_check.pdf",
        organization=organization,
        folder=folder3,
        document_type=schema.DocumentType.BACKGROUND_CHECK,
    )
    doc3 = schema.Document(
        name="Jamie's Training Certificate",
        link="http://example.com/jamie_training.pdf",
        organization=organization,
        folder=folder3,
    )
    session = database.SessionLocal()
    session.add_all([organization, admin, staff1, staff2, folder1, folder2, folder3, doc1, doc2, doc3])
    session.commit()
    session.close()
    yield

app = FastAPI(lifespan=load_demo_data)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Welcome to the CareLumi backend api!"}

@app.post("/auth/login")
async def login(request: schema.LoginRequest, session: Session = Depends(get_session)):
    user = database_operations.get_user_by_email(session, email=request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.password == request.password:
        token = get_token(user)
        return {"status": True, "session_token": token}
    else:
        return {"status": False}

@app.post("/registration/staff")
async def register_staff(staff: schema.StaffRegistration, session: Session = Depends(get_session)):
    if staff.password != staff.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    if not staff.agree_to_terms:
        raise HTTPException(status_code=400, detail="You must agree to the terms and conditions")
    organization = database_operations.get_organization(session, organization_id=staff.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    user = schema.User(
        first_name=staff.first_name,
        last_name=staff.last_name,
        email=staff.email,
        password=staff.password,
        role=staff.role,
        permission=schema.Permission.STAFF,
        organization_id=staff.organization_id
    )
    
    update_by_user(user)

    session.add(user)
    session.commit()
    create_user_folder(user, session)
    return JSONResponse(status_code=201, content={"status": True, "user": user.to_dict()})

@app.post("/registration/admin")
async def register_admin(staff: schema.AdminRegistration, session: Session = Depends(get_session)):
    if staff.password != staff.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    if not staff.agree_to_terms:
        raise HTTPException(status_code=400, detail="You must agree to the terms and conditions")
    organization = schema.Organization(name=staff.organization_name)
    session.add(organization)
    session.commit()
    user = schema.User(
        first_name=staff.first_name,
        last_name=staff.last_name,
        email=staff.email,
        password=staff.password,
        role=staff.role,
        permission=schema.Permission.ADMIN,
        organization=organization
    )
    
    update_by_user(user)

    session.add(user)
    session.commit()

    
    create_user_folder(user, session)
    return JSONResponse(status_code=201, content={"status": True, "user": user.to_dict()})

# User can only upload to their own folder for now
@app.post("/organization/document/upload_document")
async def upload_document(
    name: str,
    document_type: schema.DocumentType,
    file: UploadFile,
    user: schema.User = Depends(get_staff),
    session: Session = Depends(get_session)
):
    # in production, need to validate file isn't malicious and is valid pdf
    document = schema.Document(
        name=name,
        link="",
        organization_id=user.organization_id,
        folder=user.folder,
        status=schema.DocumentStatus.PENDING,
        document_type=document_type
    )
    session.add(document)
    session.commit()
    with open(f"data/{document.id}.pdf", "wb") as f:
        # https://fastapi.tiangolo.com/reference/uploadfile/#fastapi.UploadFile.file
        f.write(file.file.read())

    file.file.seek(0)
    #reset the file pointer

    bucket_name = "carelumi-data"
    s3_key = f"organization/{user.organization_id}/{user.id}/raw_documents/{document.id}.pdf"
    s3_path = upload_to_s3(file.file, bucket_name, s3_key)
    document.s3_key = s3_path
    session.commit()
    #upload the files to S3 and update the new s3_key attribute of document to keep track of things.

    document_text = get_document_text(f"data/{document.id}.pdf")


    processed_key = f"organization/{user.organization_id}/{user.id}/processed_documents/{document.id}.json"
    document.processed_key = processed_key

    upload_to_s3(document_text, bucket_name, processed_key)
    session.commit()
    #upload the extracted text to S3

    llm_response = get_llm_response(document_text)
    return JSONResponse(status_code=201, content={"message": "Document uploaded successfully", "llm_response": llm_response.json()})

@app.get("/organization/document/all")
async def get_all_documents(
    user: schema.User = Depends(get_admin),
    session: Session = Depends(get_session)
):
    return database_operations.get_documents_by_organization(session, organization_id=user.organization_id)

@app.get("/organization/folder/all")
async def get_all_folders(
    user: schema.User = Depends(get_admin),
    session: Session = Depends(get_session)
):
    return database_operations.get_folders_by_organization(session, organization_id=user.organization_id)

# Only admin can access documents from a specific folder or specific document
@app.get("/organization/folder/{folder_id}")
async def get_folder(
    folder_id: str,
    user: schema.User = Depends(get_admin),
    session: Session = Depends(get_session)
):
    documents = database_operations.get_documents_by_folder(session, folder_id=folder_id)
    return [document.to_dict() for document in documents]

# for implementation, return pre-signed url to S3 instead of actual file
@app.get("/organization/document/{document_id}")
async def get_document(
    document_id: str,
    user: schema.User = Depends(get_admin),
    session: Session = Depends(get_session)
):
    document = database_operations.get_document(session, document_id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@app.get("/organization/dashboard/overview")
async def get_dashboard_overview(
    user: schema.User = Depends(get_admin),
    session: Session = Depends(get_session)
):
    if user.permission == schema.Permission.ADMIN:
        return schema.DashboardResponse(
            hours_saved=3,
            documentation_completeness=50,
            staff_documentation_status=90,
            training_compliance_status=30,
            background_check_status=10
        )
    raise HTTPException(status_code=403, detail="User does not have access to dashboard")

@app.get("/organization/compliance-folders")
async def get_compliance_folders(
    user: schema.User = Depends(get_admin),
    session: Session = Depends(get_session)
):
    return database_operations.get_compliance_folder_response(session, organization_id=user.organization_id)

# View all data for testing purposes
@app.get("/dump")
async def dump(session: Session = Depends(get_session)):
    orgs = database_operations.get_all_organizations(session)
    users = database_operations.get_all_users(session)
    folders = database_operations.get_all_folders(session)
    documents = database_operations.get_all_documents(session)
    return {"organizations": orgs, "users": users, "folders": folders, "documents": documents}

@app.get("/reset_database")
async def reset_database():
    database.Base.metadata.drop_all(bind=database.engine)
    database.Base.metadata.create_all(bind=database.engine)
    return {"message": "Database reset successfully."}
