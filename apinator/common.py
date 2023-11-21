import enum
from typing import Any, Dict, Optional, Union
from urllib.parse import urlencode, urlunparse

import requests
from pydantic import BaseModel, ConfigDict, model_validator
from pydantic.root_model import RootModel


class PathStr(RootModel[str]):
    # model_config = ConfigDict(frozen=True)

    @model_validator(mode="before")
    @classmethod
    def clean_str(cls, data: Any):
        return str(data).strip("/")

    def __str__(self):
        return f"/{self.root}"

    def __bool__(self):
        return bool(str(self))

    def __truediv__(self, other):
        other = PathStr(other)
        return PathStr(root=f"{self.root}/{other.root}")

    def __rtruediv__(self, other):
        other = PathStr(other)
        return PathStr(root=f"{other.root}/{self.root}")

    def __getattr__(self, item):
        return getattr(str(self.root), item)


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HttpScheme(enum.Enum):
    HTTPS = "https"
    HTTP = "http"


class HttpMethod(enum.Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"


class Request(BaseModel):
    scheme: Optional[HttpScheme] = None
    host: Optional[str] = None
    path: Union[PathStr, str] = PathStr(root="")
    method: Optional[HttpMethod] = None
    params: Optional[str] = None
    query: Dict[str, str] = {}
    fragment: Optional[str] = None
    headers: Dict[str, str] = {}
    body: Optional[bytes] = None
    append_trailing_slash: bool = False
    urlencode_kwargs: Dict[str, Any] = {}

    @property
    def uri(self):
        return urlunparse(
            (
                self.scheme,
                self.host,
                self.effective_path,
                self.params,
                self.encoded_query,
                self.fragment,
            )
        )

    @property
    def effective_path(self) -> str:
        path = str(self.path)
        if self.append_trailing_slash:
            path = path.rstrip("/") + "/"
        return path

    @property
    def encoded_query(self) -> str:
        return urlencode(self.query, **self.urlencode_kwargs)

    def with_options(self, **kwargs):
        new_request = self.model_copy()

        for key, value in kwargs.items():
            if hasattr(self, f"_modify_{key}"):
                current_value = getattr(self, key)
                new_value = getattr(new_request, f"_modify_{key}")(current_value, value)
            else:
                new_value = value
            setattr(new_request, key, new_value)

        return new_request

    @staticmethod
    def _modify_query(query_dict, extra_query):
        return dict(**(query_dict or {}), **extra_query)

    @staticmethod
    def _modify_headers(headers_dict, extra_headers):
        return dict(**(headers_dict or {}), **extra_headers)

    def call_with_requests(self, session: requests.Session) -> requests.Response:
        return session.request(
            str(self.method.value),
            self.uri,
            headers=self.headers,
            data=self.body,
            params=self.params,
        )
