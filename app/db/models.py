from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from pydantic import BaseModel, EmailStr
from app.core.config import settings


Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    pages = relationship("Page", back_populates="author")
    contacts = relationship("Contact", back_populates="user")

    def __repr__(self):
        return f"<User {self.username}>"


class Page(Base):
    __tablename__ = "pages"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    content = Column(Text, nullable=True)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    author_id = Column(Integer, ForeignKey("users.id"))
    
    author = relationship("User", back_populates="pages")
    meta = relationship("PageMeta", back_populates="page", uselist=False)
    
    def __repr__(self):
        return f"<Page {self.slug}>"


class PageMeta(Base):
    # SEO
    __tablename__ = "page_meta"
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id"), unique=True)
    meta_title = Column(String(100), nullable=True)
    meta_description = Column(String(300), nullable=True)
    keywords = Column(String(200), nullable=True)
    
    page = relationship("Page", back_populates="meta")
    
    def __repr__(self):
        return f"<PageMeta for page {self.page_id}>"


class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    message = Column(Text, nullable=True)
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    user = relationship("User", back_populates="contacts")
    
    def __repr__(self):
        return f"<Contact from {self.name}>"


class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    password: str


class UserInDB(UserBase):
    id: int
    hashed_password: str
    is_superuser: bool
    created_at: datetime
    
    class Config:
        orm_mode = True


class PageBase(BaseModel):
    title: str
    slug: str
    content: Optional[str] = None
    is_published: bool = True


class PageCreate(PageBase):
    author_id: int


class PageInDB(PageBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class ContactBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    message: Optional[str] = None


class ContactCreate(ContactBase):
    pass


class ContactInDB(ContactBase):
    id: int
    is_processed: bool
    created_at: datetime
    
    class Config:
        orm_mode = True


def create_tables(engine):
    Base.metadata.create_all(bind=engine)
