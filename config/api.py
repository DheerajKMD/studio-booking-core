from django.http import HttpRequest, HttpResponse
from ninja import NinjaAPI
from apps.studios.api import router as studios_router

from apps.accounts.api import router as accounts_router
from apps.common.exceptions import DomainError

api = NinjaAPI(title="Studio API", version="1.0.0")
from apps.credits.api import router as credits_router
api.add_router("/auth", accounts_router)
api.add_router("/studios", studios_router)
api.add_router("/credits", credits_router)

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