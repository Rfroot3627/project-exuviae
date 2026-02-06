from __future__ import annotations
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .adapters.http.routes import router as http_router
from .application.usecases.ingest_snapshot_upload import IngestSnapshotUpload
from .infrastructure.storage.fs_snapshot_store_adapter import FsSnapshotStoreAdapter
from .infrastructure.storage.jsonl_log_writer import JsonlLogWriter
from .infrastructure.vision.describer_stub import StubVisionDescriber
from .infrastructure.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Hub starting. Data root: {settings.DATA_ROOT}")
    yield

def create_app() -> FastAPI:
    app = FastAPI(title="Exuviae Hub", version="0.1.0", lifespan=lifespan)

    # --- DI wiring (v0.1 simple) ---
    snapshot_store = FsSnapshotStoreAdapter()
    describer = StubVisionDescriber()
    log_writer = JsonlLogWriter()

    ingest_uc = IngestSnapshotUpload(
        snapshot_store=snapshot_store,
    )

    # Patch router DI function (v0.1 simple; later replace with proper DI)
    from .adapters.http import routes as routes_module
    routes_module.get_ingest_usecase = lambda: ingest_uc  # type: ignore

    app.include_router(http_router)
    return app

app = create_app()
