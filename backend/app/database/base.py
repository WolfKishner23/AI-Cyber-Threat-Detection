# Import all the models, so that Base has them registered before being
# imported by Alembic or database setup tools.
from app.database.base_class import Base  # noqa
from app.models.security_event import SecurityEvent  # noqa
from app.models.alert import Alert  # noqa
from app.models.detection_run import DetectionRun  # noqa
