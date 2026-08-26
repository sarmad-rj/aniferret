from typing import Annotated

from pydantic import StringConstraints

CHECKPOINT_PATTERN = r"^S\d+E\d+$"
"""Canonical checkpoint format shared by all schemas, e.g. 'S1E12'."""

CheckpointStr = Annotated[str, StringConstraints(pattern=CHECKPOINT_PATTERN)]
"""Reusable annotated type for validating checkpoints inside collections, e.g. list[CheckpointStr]."""
