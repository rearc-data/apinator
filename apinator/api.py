"""Shared code for interacting with external API's"""
import logging
from typing import Any, Generic, TypeVar

import requests
from pydantic import constr, validate_arguments
from requests import Response

from apinator.common import Request

log = logging.getLogger(__name__)
M = TypeVar("M")


class ApiBase(Generic[M]):
    @validate_arguments
    def __init__(
        self,
        *,
        scheme: constr(regex=r"^http|https$") = "https",
        host: constr(regex=r"^[a-zA-Z0-9.-]+$"),
        path_prefix: constr(regex=r"\S*") = "",
        append_trailing_slash: bool = False,
        urlencode_kwargs: dict = None,
    ):
        self.scheme = scheme
        self.host = host
        self.path_prefix = path_prefix.strip("/")
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
