from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query

from models.api_models import Film, FilmByPerson
from services.film import FilmService, get_film_service


router = APIRouter()


@router.get("/{film_id}", response_model=Film)
async def film_details(film_id: str, film_service: FilmService = Depends(get_film_service)) -> Film:
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="film not found")
    return Film(id=film.id, title=film.title)


@router.get("/", response_model=list[Film])
async def films_list(
    sort: str | None = Query(default=None),
    filter_genre: str | None = Query(default=None, alias="filter[genre]"),
    filter_person: str | None = Query(default=None, alias="filter[person]"),
    page_size: int = Query(default=50, alias="page[size]"),
    page_number: int = Query(default=1, alias="page[number]"),
    film_service: FilmService = Depends(get_film_service),
) -> list[Film]:
    films = await film_service.get_list(sort, filter_genre, filter_person, page_size, page_number)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="films not found")
    return [Film(id=film.id, title=film.title) for film in films]


@router.get("/search", response_model=list[FilmByPerson])
async def films_search(
    query: str | None = Query(default=None),
    page_size: int = Query(default=50, alias="page[size]"),
    page_number: int = Query(default=1, alias="page[number]"),
) -> FilmByPerson:
    pass
