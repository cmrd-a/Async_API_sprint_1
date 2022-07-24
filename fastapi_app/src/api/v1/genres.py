from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Path

from models.api_models import GenresDescripted, GenreDescripted
from models.common import Genre
from services.genres import get_genres_service, GenresService

router = APIRouter()


@router.get("/{genre_id}", response_model=GenreDescripted, summary="Поиск жанра по id")
async def genre_details(
    genre_id: str = Path(description="UUID жанра"), genre_service: GenresService = Depends(get_genres_service)
) -> Genre:
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="genre not found")
    return Genre(id=genre.id, name=genre.name)


@router.get("/", response_model=GenresDescripted, summary="Список всех жанров")
async def genres_list(genre_service: GenresService = Depends(get_genres_service)) -> GenresDescripted:
    genres = await genre_service.get_list()
    if not genres:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="genres not found")
    return genres
