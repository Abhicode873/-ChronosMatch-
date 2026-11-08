
"""Request and response schemas for the ChronosMatch API."""

from pydantic import BaseModel, Field


class SimulationRunRequest(BaseModel):
    """Configuration for one finite market simulation."""

    order_count: int = Field(default=1000, ge=1, le=100_000)
    seed: int | None = None
    interval_seconds: float = Field(default=0.0, ge=0.0, le=1.0)
    buffer_capacity: int = Field(default=64, ge=1, le=4096)
