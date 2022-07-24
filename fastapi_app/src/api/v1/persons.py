from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query

from models.api_models import Person, FilmByPerson
from services.persons import PersonsService, get_persons_service

router = APIRouter()


@router.get("/{person_id}/film", response_model=FilmByPerson)
async def film_details_by_person() -> FilmByPerson:
    pass


@router.get("/{person_id}", response_model=Person)
async def person_by_id(person_id: str, person_service: PersonsService = Depends(get_persons_service)) -> Person:
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="person not found")
    return person


@router.get("/search", response_model=list[Person])
async def persons_search(
    query: str | None = Query(default=None),
    page_size: int = Query(default=50, alias="page[size]"),
    page_number: int = Query(default=1, alias="page[number]"),
) -> Person:
    pass
