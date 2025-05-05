from fastapi import APIRouter, Depends, HTTPException
from app.services.page_service import PageService
from app.schemas.page import PageResponse, PageCreate
from typing import List


router = APIRouter(prefix="/pages", tags=["Pages"])


@router.get("/", response_model=List[PageResponse])
async def get_all_pages(service: PageService = Depends()):
    return service.get_all()


@router.get("/{page_slug}", response_model=PageResponse)
async def get_page(page_slug: str, service: PageService = Depends()):
    page = service.get_by_slug(page_slug)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@router.post("/", response_model=PageResponse)
async def create_page(page_data: PageCreate, service: PageService = Depends()):
    return service.create(page_data)
