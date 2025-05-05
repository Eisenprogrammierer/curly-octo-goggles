from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.db.repositories import PageRepository, get_page_repository
from app.models import Page, PageMeta

from app.schemas.page import (
    PageCreate,
    PageUpdate,
    PageInDB,
    PageWithMeta,
    PageMetaCreate,
    PageMetaUpdate
)

from app.core.security import get_current_active_user
from app.models import User


class PageService:
    
    def __init__(self, page_repo: PageRepository):
        self.page_repo = page_repo


    async def get_page_by_id(self, page_id: int) -> PageInDB:
        page = self.page_repo.get(page_id)
        if not page:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Page not found"
            )
        return PageInDB.from_orm(page)
    

    async def get_page_by_slug(self, slug: str) -> PageWithMeta:
        page = self.page_repo.get_by_slug(slug)
        if not page or not page.is_published:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Page not found or not published"
            )
        return self._add_meta_to_page(page)
    

    async def list_published_pages(self) -> List[PageWithMeta]:
        pages = self.page_repo.get_published()
        return [self._add_meta_to_page(page) for page in pages]
    

    async def create_page(
        self,
        page_create: PageCreate,
        current_user: User
    ) -> PageInDB:
        existing_page = self.page_repo.get_by_slug(page_create.slug)
        if existing_page:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page with this slug already exists"
            )
        
        page = self.page_repo.create_with_author(
            obj_in=page_create,
            author_id=current_user.id
        )
        return PageInDB.from_orm(page)
    

    async def update_page(
        self,
        page_id: int,
        page_update: PageUpdate,
        current_user: User
    ) -> PageInDB:
        page = self.page_repo.get(page_id)
        if not page:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Page not found"
            )
        
        if page.author_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        updated_page = self.page_repo.update(
            db_obj=page,
            obj_in=page_update.dict(exclude_unset=True)
        )
        return PageInDB.from_orm(updated_page)
    

    async def update_page_meta(
        self,
        page_id: int,
        meta_update: PageMetaUpdate
    ) -> PageWithMeta:
        page = self.page_repo.get(page_id)
        if not page:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Page not found"
            )
        
        meta_data = meta_update.dict(exclude_unset=True)
        self.page_repo.update_meta(page_id=page_id, meta_in=meta_data)
        
        updated_page = self.page_repo.get(page_id)
        return self._add_meta_to_page(updated_page)
    

    async def delete_page(
        self,
        page_id: int,
        current_user: User
    ) -> Dict[str, Any]:
        page = self.page_repo.get(page_id)
        if not page:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Page not found"
            )
        
        if page.author_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        self.page_repo.delete(id=page_id)
        return {"message": "Page deleted successfully"}


    def _add_meta_to_page(self, page: Page) -> PageWithMeta:
        """Добавляет мета-данные к странице для ответа"""
        meta_data = {
            "meta_title": page.meta.meta_title if page.meta else None,
            "meta_description": page.meta.meta_description if page.meta else None,
            "keywords": page.meta.keywords if page.meta else None
        } if hasattr(page, 'meta') else {}
        
        page_dict = PageInDB.from_orm(page).dict()
        return PageWithMeta(**page_dict, **meta_data)


def get_page_service(
    db: Session = Depends(get_db),
    page_repo: PageRepository = Depends(get_page_repository)
) -> PageService:
    return PageService(page_repo=page_repo)
