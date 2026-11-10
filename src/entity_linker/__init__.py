"""Entity linker: deterministic catalog-driven entity mention detection."""

from __future__ import annotations

import logging

from ._core import Catalog, Entity, LinkerError, LinkerErrorCode, Mention, link

__all__ = [
    "Catalog",
    "Entity",
    "LinkerError",
    "LinkerErrorCode",
    "Mention",
    "link",
]

__version__ = "0.1.0"

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
