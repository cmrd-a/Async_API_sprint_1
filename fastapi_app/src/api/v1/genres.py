from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException

from models.api_models import Genre
from services.genres import get_genres_service, GenresService

router = APIRouter()


@router.get("/{genre_id}", response_model=Genre)
async def genre_details(genre_id: str, genre_service: GenresService = Depends(get_genres_service)) -> Genre:
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="genre not found")
    return Genre(id=genre.id, name=genre.name)


@router.get("/", response_model=list[Genre])
async def genres_list(genre_service: GenresService = Depends(get_genres_service)) -> list[Genre]:
    genres = await genre_service.get_list()
    if not genres:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="genres not found")
    return [Genre(id=genre.id, name=genre.name) for genre in genres]
