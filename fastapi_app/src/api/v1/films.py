from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query, Path

from local.detail_messages import FILM_NOT_FOUND, FILMS_NOT_FOUND
from models.api_models import FilmFull, FilmsRated
from services.films import FilmService, get_film_service, ApiSortOptions

router = APIRouter()


@router.get("/", response_model=FilmsRated, summary="Список фильмов")
async def films_list(
    sort: ApiSortOptions | None = Query(default=None, description="Сортировка"),
    filter_genre: str | None = Query(default=None, alias="filter[genre]", description="Фильтр по жанру(UUID)"),
    filter_person: str | None = Query(default=None, alias="filter[person]", description="Фильтр по персоне(UUID)"),
    page_size: int = Query(default=50, alias="page[size]", description="Размер страницы", gt=0, lt=100),
    page_number: int = Query(default=1, alias="page[number]", description="Номер страницы", gt=0, lt=1000),
    film_service: FilmService = Depends(get_film_service),
):
    films = await film_service.get_films(
        sort=sort,
        filter_genre=filter_genre,
        filter_person=filter_person,
        page_size=page_size,
        page_number=page_number,
    )
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=FILMS_NOT_FOUND)
    return films


@router.get("/search", response_model=FilmsRated, summary="Поиск фильмов по названию и описанию")
async def films_search(
    query: str = Query(min_length=3, description="Поисковый запрос"),
    page_size: int = Query(default=50, alias="page[size]", description="Размер страницы", gt=0, lt=100),
    page_number: int = Query(default=1, alias="page[number]", description="Номер страницы", gt=0, lt=1000),
    film_service: FilmService = Depends(get_film_service),
):
    films = await film_service.get_films(
        search_str=query, page_size=page_size, page_number=page_number
    )
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=FILMS_NOT_FOUND)
    return films


@router.get("/{film_id}", response_model=FilmFull, summary="Информация о конкретном фильме")
async def film_details(
    film_id: str = Path(description="UUID фильма"), film_service: FilmService = Depends(get_film_service)
):
    film = await film_service.get_film(film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=FILM_NOT_FOUND)
    return film
