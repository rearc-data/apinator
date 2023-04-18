import enum
from typing import Any, Dict, Optional, Union
from urllib.parse import urlencode, urlunparse

import requests
from pydantic import BaseModel, Extra, root_validator


class PathStr(BaseModel):
    __root__: str = ""

    @root_validator
    def clean_str(cls, values: Dict[str, Any]):
        values["__root__"] = values["__root__"].strip("/")
        return values

    class Config:
        frozen = True

    def __str__(self):
        return f"/{self.__root__}"

    def __bool__(self):
        return bool(str(self))

    def __truediv__(self, other):
        other = PathStr.parse_obj(other)
        return PathStr(__root__=f"{self.__root__}/{other.__root__}")

    def __rtruediv__(self, other):
        other = PathStr.parse_obj(other)
        return PathStr(__root__=f"{other.__root__}/{self.__root__}")

    def __getattr__(self, item):
        return getattr(str(self.__root__), item)


class StrictBaseModel(BaseModel):
    class Config:
        extra = Extra.forbid


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
    path: Union[PathStr, str] = PathStr(__root__="")
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
        new_request = self.copy()

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
