from exuviae_hub.infrastructure.config import settings
from pathlib import Path
p = Path(settings.DATA_ROOT) / settings.LOG_SUBDIR / settings.VISION_LOG_FILENAME
print(str(p))
