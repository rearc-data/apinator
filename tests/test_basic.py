from typing import List

import pytest
import responses
from pydantic import BaseModel
from responses import matchers

from apinator.api import JsonApiBase
from apinator.endpoint import (
    BoundEndpointGroup,
    DeclarativeEndpoint,
    Endpoint,
    EndpointAction,
    EndpointGroup,
)


class PingResponse(BaseModel):
    result: bool = True


class SomeObject(BaseModel):
    n: int
    s: str


class SomeObjectList(BaseModel):
    objects: List[SomeObject]


class SampleApi(JsonApiBase):
    def __init__(self):
        super().__init__(
            host="www.example.com",
        )

    ping = DeclarativeEndpoint(
        url="/ping",
        response_model=PingResponse,
    )
    put_object = DeclarativeEndpoint(
        url="/object",
        method="PUT",
        response_model=None,
        body_model=SomeObject,
    )
    get_object = DeclarativeEndpoint(
        url="/object/{id}",
        method="GET",
        response_model=SomeObject,
    )
    head_object = get_object.make_head()
    post_object = get_object.make_post(body_model=SomeObject, response_model=None)
    put_objects = get_object.make_put(body_model=SomeObjectList)
    patch_object = get_object.make_patch(body_model=SomeObject, response_model=None)
    delete_object = get_object.make_delete()

    objects = EndpointGroup(
        "/object",
        actions=[
            EndpointAction.list(SomeObjectList),
            EndpointAction.retrieve(SomeObject),
            EndpointAction.create(SomeObject),
            EndpointAction.update(SomeObject),
            EndpointAction.partial_update(SomeObject),
            EndpointAction.destroy(),
            EndpointAction.head(),
        ],
    )

    get_table = DeclarativeEndpoint(
        method="GET",
        url="/table/{schema}/{name}",
        default_query={"database": None, "compact": "true"},
        arg_names=["schema", "name", "database"],
    )


@pytest.fixture
def api():
    return SampleApi()


@responses.activate
def test_ping(api):
    assert isinstance(SampleApi.ping, DeclarativeEndpoint)
    assert isinstance(api.ping, Endpoint)

    responses.get("https://www.example.com/ping", json={"result": True})

    ping_result = api.ping()
    assert ping_result.result is True


@responses.activate
def test_trailing_slash():
    api = SampleApi()
    api.append_trailing_slash = True
    responses.get("https://www.example.com/ping/", json={"result": True})

    ping_result = api.ping()
    assert ping_result.result is True


@responses.activate
def test_put_object(api):
    responses.put(
        "https://www.example.com/object",
        json={"success": True},
        match=(matchers.json_params_matcher({"n": 5, "s": "lol"}),),
    )

    obj = SomeObject(n=5, s="lol")
    assert api.put_object(body=obj) == {"success": True}


@responses.activate
def test_object_group(api):
    assert isinstance(SampleApi.objects, EndpointGroup)
    assert isinstance(api.objects, BoundEndpointGroup)

    responses.post(
        "https://www.example.com/object",
        json={"success": True},
        match=(matchers.json_params_matcher({"n": 5, "s": "lol"}),),
    )

    obj = SomeObject(n=5, s="lol")
    assert api.objects.create(body=obj) == {"success": True}

    responses.get("https://www.example.com/object/5", json=obj.dict())
    result = api.objects.retrieve(5)
    assert result == obj


def test_multiple_api_instances():
    """Test that an API can be instantiated multiple times without issue"""
    api1 = SampleApi()
    api2 = SampleApi()

    _ = api1.put_object
    _ = api2.put_object

    _ = api1.objects
    _ = api2.objects


def test_api_raises_error_if_used_wrong(api):
    with pytest.raises(ValueError):
        # Call should fail if not passed necessary arguments
        api.objects.retrieve()
    with pytest.raises(ValueError):
        # Call should fail if passed unnecessary arguments
        api.objects.retrieve(5, 10)

    with pytest.raises(AttributeError):
        # Call should fail if action is not defined
        api.objects.get()  # Should be `retrieve`


@responses.activate
def test_query_params(api):
    responses.get(
        "https://www.example.com/table/my_schema/my_table?database=my_database&compact=true",
        json={"success": True},
    )

    assert api.get_table("my_schema", "my_table", "my_database") == {"success": True}
