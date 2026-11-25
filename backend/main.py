import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.auth import router as admin_router
from backend.database import ROOT, database_path, open_database

logger = logging.getLogger('uvicorn.error')


class Health(BaseModel):
    status: Literal['ok'] = 'ok'
    database: Literal['ready'] = 'ready'
    shop_name: str


def create_app(db_path: Path | None = None, dist_dir: Path | None = None) -> FastAPI:
    path = db_path if db_path is not None else database_path()
    dist = dist_dir if dist_dir is not None else ROOT / 'frontend' / 'dist'

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.db_path = path
        app.state.engine = open_database(path)
        try:
            yield
        finally:
            app.state.engine.dispose()

    app = FastAPI(title='June OMS', version='0.1.0', lifespan=lifespan)

    @app.get('/api/health')
    def health() -> Health:
        try:
            if path.is_file():
                with app.state.engine.connect() as connection:
                    shop_name = connection.execute(
                        text('SELECT value FROM shop_settings WHERE key = :key'),
                        {'key': 'shop_name'},
                    ).scalar_one_or_none()
                if shop_name is not None:
                    return Health(shop_name=shop_name)
        except SQLAlchemyError as error:
            logger.warning('SQLite readiness check failed (%s).', type(error).__name__)
        raise HTTPException(status_code=503, detail='Database chưa sẵn sàng.')

    app.include_router(admin_router)
    if (dist / 'index.html').is_file():
        app.mount('/', StaticFiles(directory=dist, html=True), name='frontend')

    return app


app = create_app()
