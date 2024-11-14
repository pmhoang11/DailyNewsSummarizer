from fastapi import APIRouter
from app.api import (
    # healthcheck,
    # login,
    # user,
    aiqueue
)
router = APIRouter()

# router.include_router(healthcheck.router, tags=["health-check"], prefix="/healthcheck")
# router.include_router(login.router, tags=["login"], prefix="/login")
# router.include_router(user.router, tags=["user"], prefix="/users")
router.include_router(aiqueue.router, tags=["aiqueue"], prefix="/aiqueue")


from app.api import (
    crawl_news,
)

router.include_router(crawl_news.router, tags=["News"], prefix="/crawl")

from app.api import (
    summary_news,
)

router.include_router(summary_news.router, tags=["News"], prefix="/summary_news")

from app.api import (
    vectordb,
)

router.include_router(vectordb.router, tags=["News"], prefix="/save_vector")
