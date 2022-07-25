from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request

from local.detail_messages import FILM_DETAILS_NOT_FOUND, PERSON_NOT_FOUND, PERSONS_NOT_FOUND
from models.api_models import PersonSearch, PersonWithFilms, FilmsByPerson
from services.persons import PersonsService, get_persons_service

router = APIRouter()


@router.get(
    "/{person_id}/film",
    response_model=FilmsByPerson,
    summary="Детали фильмов по персоне",
    deprecated=True,
    description="Used for old android devices",
)
async def film_details_by_person(
    person_id: str = Path(description="UUID персоны"), person_service: PersonsService = Depends(get_persons_service)
):
    film_details = await person_service.get_film_detail_by_person(person_id=person_id)
    if not film_details:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=FILM_DETAILS_NOT_FOUND)
    return film_details


@router.get("/search", response_model=PersonSearch, summary="Поиск актера по подстроке имени")
async def persons_search(
    query: str,
    person_service: PersonsService = Depends(get_persons_service),
    page_size: int = Query(default=50, alias="page[size]", description="Размер страницы", lt=0, gt=100),
    page_number: int = Query(default=1, alias="page[number]", description="Номер страницы", lt=0, gt=1000),
) -> PersonSearch:
    person = await person_service.search(
        search_str=query,
        page_size=page_size,
        page_number=page_number,
    )
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=PERSONS_NOT_FOUND)
    return person


@router.get("/{person_id}", response_model=PersonWithFilms, summary="Детали фильма по персоне")
async def person_by_id(
    person_id: str = Path(description="UUID персоны"), person_service: PersonsService = Depends(get_persons_service)
) -> PersonWithFilms:
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=PERSON_NOT_FOUND)
    return person
