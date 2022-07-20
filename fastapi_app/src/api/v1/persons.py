from fastapi import APIRouter, Query

from models.api_models import Person, FilmByPerson

router = APIRouter()


@router.get("/{person_id}/film", response_model=FilmByPerson)
async def film_details_by_person() -> FilmByPerson:
    pass


@router.get("/{person_id}", response_model=Person)
async def person_by_id() -> Person:
    pass


@router.get("/search", response_model=list[Person])
async def persons_search(
    query: str | None = Query(default=None),
    page_size: int = Query(default=50, alias="page[size]"),
    page_number: int = Query(default=1, alias="page[number]"),
) -> Person:
    pass
