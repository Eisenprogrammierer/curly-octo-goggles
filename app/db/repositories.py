from typing import Optional, List, TypeVar, Generic, Type, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models import Base, User, Page, Contact, PageMeta
from app.core.config import settings
from fastapi import HTTPException, status


ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db


    def get(self, id: Any) -> Optional[ModelType]:
        return self.db.query(self.model).filter(self.model.id == id).first()


    def get_multi(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        return self.db.query(self.model).offset(skip).limit(limit).all()


    def create(self, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = obj_in.dict()
        db_obj = self.model(**obj_in_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj


    def update(
        self, *, db_obj: ModelType, obj_in: UpdateSchemaType | dict[str, Any]
    ) -> ModelType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj


    def delete(self, *, id: int) -> ModelType:
        obj = self.db.query(self.model).get(id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Object not found"
            )
        self.db.delete(obj)
        self.db.commit()
        return obj


class UserRepository(BaseRepository[User, CreateSchemaType, UpdateSchemaType]):
    
    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()
    

    def authenticate(
        self, *, username: str, password: str
    ) -> Optional[User]:
        user = self.get_by_username(username=username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


    def is_active(self, user: User) -> bool:
        return user.is_active


    def is_superuser(self, user: User) -> bool:
        return user.is_superuser


class PageRepository(BaseRepository[Page, CreateSchemaType, UpdateSchemaType]):
    
    def get_by_slug(self, slug: str) -> Optional[Page]:
        return self.db.query(Page).filter(Page.slug == slug).first()


    def get_published(self) -> List[Page]:
        return (
            self.db.query(Page)
            .filter(Page.is_published == True)
            .order_by(Page.created_at.desc())
            .all()
        )


    def create_with_author(
        self, *, obj_in: CreateSchemaType, author_id: int
    ) -> Page:
        obj_in_data = obj_in.dict()
        db_obj = self.model(**obj_in_data, author_id=author_id)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj


    def update_meta(
        self, *, page_id: int, meta_in: dict[str, Any]
    ) -> PageMeta:
        page = self.get(page_id)
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        
        if not page.meta:
            meta_obj = PageMeta(page_id=page_id, **meta_in)
            self.db.add(meta_obj)
        else:
            for field, value in meta_in.items():
                setattr(page.meta, field, value)
        
        self.db.commit()
        self.db.refresh(page)
        return page.meta


class ContactRepository(BaseRepository[Contact, CreateSchemaType, UpdateSchemaType]):
    
    def get_unprocessed(self) -> List[Contact]:
        return (
            self.db.query(Contact)
            .filter(Contact.is_processed == False)
            .order_by(Contact.created_at.desc())
            .all()
        )


    def mark_as_processed(self, *, contact_id: int) -> Contact:
        contact = self.get(contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        contact.is_processed = True
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        return contact


    def create_with_user(
        self, *, obj_in: CreateSchemaType, user_id: Optional[int] = None
    ) -> Contact:
        obj_in_data = obj_in.dict()
        db_obj = self.model(**obj_in_data, user_id=user_id)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj


def get_user_repository(db: Session) -> UserRepository:
    return UserRepository(User, db)


def get_page_repository(db: Session) -> PageRepository:
    return PageRepository(Page, db)


def get_contact_repository(db: Session) -> ContactRepository:
    return ContactRepository(Contact, db)
