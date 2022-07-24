from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from models.api_models import FilmFull, FilmsRated
from services.film import FilmService, get_film_service, ApiSortOptions

router = APIRouter()


@router.get("/{film_id}", response_model=FilmFull)
async def film_details(film_id: str, film_service: FilmService = Depends(get_film_service)):
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="film not found")
    return film


@router.get("/", response_model=FilmsRated)
async def films_list(
    request: Request,
    sort: ApiSortOptions | None = Query(default=None),
    filter_genre: str | None = Query(default=None, alias="filter[genre]"),
    filter_person: str | None = Query(default=None, alias="filter[person]"),
    page_size: int = Query(default=50, alias="page[size]"),
    page_number: int = Query(default=1, alias="page[number]"),
    film_service: FilmService = Depends(get_film_service),
):
    films = await film_service.get_list(request.query_params, sort, filter_genre, filter_person, page_size, page_number)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="films not found")
    return films


@router.get("/search", response_model=FilmsRated)
async def films_search(
    query: str | None = Query(default=None),
    page_size: int = Query(default=50, alias="page[size]"),
    page_number: int = Query(default=1, alias="page[number]"),
    film_service: FilmService = Depends(get_film_service),
):
    films = await film_service.get_list(request.query_params, sort, filter_genre, filter_person, page_size, page_number)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="films not found")
    return films
