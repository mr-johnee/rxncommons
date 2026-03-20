from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import engine, Base
from app.models import *

def ensure_schema_compatibility() -> None:
    """Apply small additive schema patches for existing databases."""
    compatibility_sql = (
        "ALTER TABLE datasets ADD COLUMN IF NOT EXISTS cover_image_key VARCHAR(500);",
        "ALTER TABLE dataset_versions ADD COLUMN IF NOT EXISTS archive_key VARCHAR(500);",
    )
    with engine.begin() as connection:
        for statement in compatibility_sql:
            connection.execute(text(statement))

def create_app() -> FastAPI:
    # 自动在数据库中创建所有表（生产环境建议使用 Alembic 迁移工具）
    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    # Set all CORS enabled origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # 生产环境请替换为前端实际域名
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/", include_in_schema=False)
    def redirect_to_docs():
        return RedirectResponse(url="/docs")

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
