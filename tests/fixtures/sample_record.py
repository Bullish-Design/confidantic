"""Sample Pydantic record model for integration test fixtures."""

from pydantic import BaseModel


class UserRecord(BaseModel):
    name: str
    email: str
    role: str = "user"
