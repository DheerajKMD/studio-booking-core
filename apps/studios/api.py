from django.http import HttpRequest
from ninja import Router

from apps.accounts.auth import TokenAuth
from apps.accounts.permissions import require_staff

from . import services
from .schemas import ClassIn, ClassOut, StudioIn, StudioOut, StudioUpdateIn

router = Router(tags=["studios"], auth=TokenAuth())


@router.post("/", response={201: StudioOut})
def create_studio(request: HttpRequest, payload: StudioIn) -> tuple[int, StudioOut]:
    require_staff(request.auth)  # type: ignore[attr-defined]
    studio = services.create_studio(**payload.dict())
    return 201, StudioOut.model_validate(studio, from_attributes=True)


@router.patch("/{studio_id}", response=StudioOut)
def update_studio(
    request: HttpRequest, studio_id: int, payload: StudioUpdateIn
) -> StudioOut:
    require_staff(request.auth)  # type: ignore[attr-defined]
    studio = services.update_studio(studio_id, **payload.dict(exclude_unset=True))
    return StudioOut.model_validate(studio, from_attributes=True)


@router.post("/{studio_id}/classes", response={201: ClassOut})
def schedule_class(
    request: HttpRequest, studio_id: int, payload: ClassIn
) -> tuple[int, ClassOut]:
    require_staff(request.auth)  # type: ignore[attr-defined]
    session = services.schedule_class(studio_id, **payload.dict())
    return 201, ClassOut(
        id=session.pk,
        studio_id=session.studio_id,
        title=session.title,
        starts_at=session.starts_at,
        duration_minutes=session.duration_minutes,
        capacity=session.capacity,
        credit_cost=session.credit_cost,
        spots_available=session.capacity,
    )