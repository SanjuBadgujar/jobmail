from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class DashboardStats(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    total_recipients: int
    sent: int
    pending: int
    failed: int
    gmail_connected: bool
    gmail_email: str | None = None
