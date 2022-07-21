from fastapi import APIRouter

from models.api_models import Genre

router = APIRouter()


@router.get("/{genre_id}", response_model=Genre)
async def film_details() -> Genre:
    pass


@router.get("/", response_model=list[Genre])
async def genres_list() -> list[Genre]:
    pass
