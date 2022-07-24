from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Path

from models.api_models import FilmFull, FilmsRated
from services.films import FilmService, get_film_service, ApiSortOptions

router = APIRouter()


@router.get("/", response_model=FilmsRated, summary="Список фильмов")
async def films_list(
    request: Request,
    sort: ApiSortOptions | None = Query(default=None, description="Сортировка"),
    filter_genre: str | None = Query(default=None, alias="filter[genre]", description="Фильтр по жанру(UUID)"),
    filter_person: str | None = Query(default=None, alias="filter[person]", description="Фильтр по персоне(UUID)"),
    page_size: int = Query(default=50, alias="page[size]", description="Размер страницы"),
    page_number: int = Query(default=1, alias="page[number]", description="Номер страницы"),
    film_service: FilmService = Depends(get_film_service),
):
    films = await film_service.get_films(
        request.query_params,
        sort=sort,
        filter_genre=filter_genre,
        filter_person=filter_person,
        page_size=page_size,
        page_number=page_number,
    )
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="films not found")
    return films


@router.get("/search", response_model=FilmsRated, summary="Поиск фильмов по названию и описанию")
async def films_search(
    request: Request,
    query: str | None = Query(default=None, description="Поисковый запрос"),
    page_size: int = Query(default=50, alias="page[size]", description="Размер страницы"),
    page_number: int = Query(default=1, alias="page[number]", description="Номер страницы"),
    film_service: FilmService = Depends(get_film_service),
):
    films = await film_service.get_films(
        request.query_params, search_str=query, page_size=page_size, page_number=page_number
    )
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="films not found")
    return films


@router.get("/{film_id}", response_model=FilmFull, summary="Информация о конкретном фильме")
async def film_details(
    film_id: str = Path(description="UUID фильма"), film_service: FilmService = Depends(get_film_service)
):
    film = await film_service.get_film(film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="film not found")
    return film
