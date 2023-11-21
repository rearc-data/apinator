"""Shared code for interacting with external API's"""
import logging
from typing import Any, Generic, TypeVar

import requests
from pydantic import StringConstraints, validate_arguments, validate_call
from requests import Response

from apinator.common import Request, PathStr
from typing_extensions import Annotated

log = logging.getLogger(__name__)
M = TypeVar("M")


class ApiBase(Generic[M]):
    @validate_call
    def __init__(
        self,
        *,
        host: Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9.-]+$")],
        scheme: Annotated[str, StringConstraints(pattern=r"^http|https$")] = "https",
        path_prefix: Annotated[str, StringConstraints(pattern=r"\S*")] = "",
        append_trailing_slash: bool = False,
        urlencode_kwargs: dict = None,
    ):
        self.scheme = scheme
        self.host = host
        self.path_prefix = PathStr(path_prefix)
        self.append_trailing_slash = append_trailing_slash
        self.urlencode_kwargs = urlencode_kwargs or {}

        self.session = requests.Session()

    def get_headers(self):
        return {}

    def process_response(self, response: Response, _request: Request) -> M:
        response.raise_for_status()

        return response

    def request(self, request: Request) -> M:
        request = request.with_options(
            scheme=self.scheme,
            host=self.host,
            path=self.path_prefix / request.path,
            headers=self.get_headers(),
            append_trailing_slash=self.append_trailing_slash,
            urlencode_kwargs=self.urlencode_kwargs,
        )

        log.debug(f"{type(self).__name__} Request: {request}")
        response = request.call_with_requests(self.session)
        response = self.process_response(response, request)
        return response


class JsonApiBase(ApiBase[Any]):
    def process_response(self, response: Response, _request: Request) -> Any:
        response = super().process_response(response, _request)
        return response.json()
