from django.http import HttpRequest, HttpResponse
from ninja import NinjaAPI

from apps.accounts.api import router as accounts_router
from apps.common.exceptions import DomainError

api = NinjaAPI(title="Studio API", version="1.0.0")

api.add_router("/auth", accounts_router)


@api.exception_handler(DomainError)
def handle_domain_error(request: HttpRequest, exc: DomainError) -> HttpResponse:
    return api.create_response(
        request,
        {"code": exc.code, "detail": exc.message},
        status=exc.status_code,
    )


@api.get("/health")
def health(request: HttpRequest) -> dict[str, str]:
    return {"status": "ok"}