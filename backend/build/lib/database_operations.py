import schema
from sqlalchemy.orm import Session

def get_user(db: Session, user_id: int):
    return db.query(schema.User).filter(schema.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(schema.User).filter(schema.User.email == email).first()

def get_organization(db: Session, organization_id: str):
    return db.query(schema.Organization).filter(schema.Organization.id == organization_id).first()

def get_folder(db: Session, folder_id: str):
    return db.query(schema.Folder).filter(schema.Folder.id == folder_id).first()

def get_documents_by_organization(db: Session, organization_id: str):
    return db.query(schema.Document).filter(schema.Document.organization_id == organization_id).all()

def get_folders_by_organization(db: Session, organization_id: str):
    return db.query(schema.Folder).filter(schema.Folder.organization_id == organization_id).all()

def get_documents_by_folder(db: Session, folder_id: str):
    return db.query(schema.Document).filter(schema.Document.folder_id == folder_id).all()

def get_document(db: Session, document_id: str):
    return db.query(schema.Document).filter(schema.Document.id == document_id).first()

def get_all_organizations(db: Session):
    return db.query(schema.Organization).all()

def get_all_users(db: Session):
    return db.query(schema.User).all()

def get_all_folders(db: Session):
    return db.query(schema.Folder).all()

def get_all_documents(db: Session):
    return db.query(schema.Document).all()

def get_compliance_folder_response(db: Session, organization_id: str) -> schema.ComplianceFoldersResponse:
    folders = db.query(schema.Folder).filter(schema.Folder.organization_id == organization_id).all()
    folder_responses = []
    for folder in folders:
        folder_responses.append(schema.FolderResponse(
            id=folder.id,
            name=folder.name,
            organization_id=folder.organization_id,
            num_docs=len(folder.documents),
            user=schema.UserResponse(
                id=folder.user.id,
                first_name=folder.user.first_name,
                last_name=folder.user.last_name,
                email=folder.user.email,
                role=folder.user.role,
                permission=folder.user.permission,
                organization_id=folder.user.organization_id
            ) if folder.user else None
        ))
    return schema.ComplianceFoldersResponse(folders=folder_responses)

