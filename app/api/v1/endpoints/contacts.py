import re

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import EmailStr, BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


router = APIRouter(
    prefix="/api/v1/contacts",
    tags=["Contacts"],
    responses={404: {"description": "Not found"}}
)


class ContactBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, example="Иван Иванов")
    email: EmailStr = Field(..., example="user@example.com")
    phone: Optional[str] = Field(
        None,
        min_length=10,
        max_length=20,
        example="+79991234567",
        regex=r"^\+?[0-9\s\-\(\)]+$"
    )
    message: Optional[str] = Field(None, max_length=1000, example="Хочу связаться")


    @validator('phone')
    def validate_phone(cls, v):
        if v is None:
            return v
        cleaned = re.sub(r"[^\d+]", "", v)
        if not 10 <= len(cleaned) <= 15:
            raise ValueError("Invalid phone number length")
        return cleaned


class ContactCreate(ContactBase):
    pass


class ContactResponse(ContactBase):
    id: int
    created_at: datetime
    is_processed: bool = False

    class Config:
        orm_mode = True


class ContactStorage:
    def __init__(self):
        self.contacts = []
        self.next_id = 1

    def add_contact(self, contact: ContactCreate) -> ContactResponse:
        contact_data = contact.dict()
        contact_data["id"] = self.next_id
        contact_data["created_at"] = datetime.now()
        contact_data["is_processed"] = False
        self.contacts.append(contact_data)
        self.next_id += 1
        return contact_data

    def get_contact(self, contact_id: int) -> Optional[ContactResponse]:
        return next((c for c in self.contacts if c["id"] == contact_id), None)

    def get_all(self) -> List[ContactResponse]:
        return self.contacts

    def delete_contact(self, contact_id: int) -> bool:
        for i, contact in enumerate(self.contacts):
            if contact["id"] == contact_id:
                self.contacts.pop(i)
                return True
        return False


fake_db = ContactStorage()


def get_contact_storage():
    return fake_db


@router.post(
    "/",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Отправить контактную форму",
    response_description="Созданный контакт"
)
async def create_contact(
    contact: ContactCreate,
    storage: ContactStorage = Depends(get_contact_storage)
):
    """
    Создание нового контакта (отправка формы).
    
    - **name**: Обязательное имя (2-50 символов)
    - **email**: Валидный email
    - **phone**: Необязательный телефон (международный формат)
    - **message**: Необязательное сообщение
    """
    try:
        new_contact = storage.add_contact(contact)
        # Здесь можно добавить отправку email или уведомления
        return new_contact
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/",
    response_model=List[ContactResponse],
    summary="Получить все контакты",
    response_description="Список контактов"
)
async def read_contacts(
    storage: ContactStorage = Depends(get_contact_storage)
):
    return storage.get_all()


@router.get(
    "/{contact_id}",
    response_model=ContactResponse,
    summary="Получить контакт по ID",
    responses={404: {"description": "Контакт не найден"}}
)
async def read_contact(
    contact_id: int,
    storage: ContactStorage = Depends(get_contact_storage)
):
    contact = storage.get_contact(contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    return contact


@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить контакт",
    responses={404: {"description": "Контакт не найден"}}
)
async def delete_contact(
    contact_id: int,
    storage: ContactStorage = Depends(get_contact_storage)
):
    if not storage.delete_contact(contact_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)
