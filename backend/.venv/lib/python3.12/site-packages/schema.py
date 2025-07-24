import uuid
from sqlalchemy import ForeignKey, String, Enum as DBEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum
from database import Base

class LanguageModelResponse(BaseModel):
    correct: bool
    reasoning: str

class Permission(str, Enum):
    ADMIN = "admin"
    STAFF = "staff"

class Role(str, Enum):
    TEACHER = "teacher"
    ASSISTANT_TEACHER = "assistant_teacher"
    SUBSTITUTE_TEACHER = "substitute_teacher"
    TEACHER_AIDE = "teacher_aide"
    STAFF = "staff"
    COOK_KITCHEN_STAFF = "cook_kitchen_staff"
    MAINTENANCE_STAFF = "maintenance_staff"
    ADMINISTRATIVE_ASSISTANT = "administrative_assistant"
    ADMIN = "admin"
    DIRECTOR = "director"
    OTHER = "other"

class DocumentType(str, Enum):
    BACKGROUND_CHECK = "background_check"
    OTHER = "other"

class DocumentStatus(str, Enum):
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    INCORRECT = "incorrect"
    PENDING = "pending"

class LoginRequest(BaseModel):
    email: str
    password: str

class DashboardResponse(BaseModel):
    hours_saved: int
    documentation_completeness: int
    staff_documentation_status: int
    training_compliance_status: int
    background_check_status: int

class UserResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    role: Role
    permission: Permission
    organization_id: str

class FolderResponse(BaseModel):
    id: str
    name: str
    organization_id: str
    num_docs: int
    user: Optional[UserResponse] = None

class ComplianceFoldersResponse(BaseModel):
    folders: List[FolderResponse]

class StaffRegistration(BaseModel):
    first_name: str
    last_name: str
    email: str
    organization_id: str
    role: Role
    password: str
    confirm_password: str
    agree_to_terms: bool

class AdminRegistration(BaseModel):
    first_name: str
    last_name: str
    email: str
    organization_name: str
    role: Role
    password: str
    confirm_password: str
    agree_to_terms: bool

class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    users: Mapped[List["User"]] = relationship(back_populates="organization")
    folders: Mapped[List["Folder"]] = relationship(back_populates="organization")
    documents: Mapped[List["Document"]] = relationship(back_populates="organization")

class Folder(Base):
    __tablename__ = "folders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    organization: Mapped["Organization"] = relationship(back_populates="folders")
    documents: Mapped[List["Document"]] = relationship(back_populates="folder")
    user: Mapped[Optional["User"]] = relationship(back_populates="folder")

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[Role] = mapped_column(DBEnum(Role), default=Role.STAFF)
    permission: Mapped[Permission] = mapped_column(DBEnum(Permission), default=Permission.STAFF)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))

    organization: Mapped["Organization"] = relationship(back_populates="users")
    folder: Mapped[Optional["Folder"]] = relationship(back_populates="user", uselist=False)

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "role": self.role,
            "permission": self.permission,
            "organization_id": self.organization_id
        }

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    link: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(DBEnum(DocumentStatus), default=DocumentStatus.PENDING)
    document_type: Mapped[DocumentType] = mapped_column(DBEnum(DocumentType), default=DocumentType.OTHER)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    folder_id: Mapped[str] = mapped_column(ForeignKey("folders.id"))
    
    organization: Mapped["Organization"] = relationship(back_populates="documents")
    folder: Mapped["Folder"] = relationship(back_populates="documents")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "link": self.link,
            "status": self.status,
            "organization_id": self.organization_id,
            "folder_id": self.folder_id
        }

