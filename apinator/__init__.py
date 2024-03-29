"""Library for building type-checked bindings to external REST APIs"""

__version__ = "0.1.1"

from .api import ApiBase, JsonApiBase
from .endpoint import DeclarativeEndpoint, EndpointAction, EndpointGroup

__all__ = (
    "ApiBase",
    "JsonApiBase",
    "EndpointGroup",
    "EndpointAction",
    "DeclarativeEndpoint",
)
