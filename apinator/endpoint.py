from __future__ import annotations

from functools import partial
from typing import Dict, Generic, Iterable, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel, validate_arguments
from typing_extensions import Self

from apinator.api import ApiBase
from apinator.common import HttpMethod, PathStr, Request

R = TypeVar("R", bound=BaseModel)
M = TypeVar("M", bound=BaseModel)


class EndpointDefinition(BaseModel, Generic[R, M]):
    name: Optional[str] = None
    url: Union[PathStr, str]
    response_model: Optional[Type[R]] = None
    body_model: Optional[Type[M]] = None
    method: Union[HttpMethod, str] = HttpMethod.GET
    arg_names: List[str] = ()
    default_query: Dict[str, Optional[str]] = {}

    class Config:
        frozen = False


class Endpoint(BaseModel, Generic[R, M]):
    defn: EndpointDefinition[R, M]
    api: ApiBase

    class Config:
        arbitrary_types_allowed = True
        frozen = True

    def __call__(self, *args, body: Optional[M] = None, **kwargs) -> R:
        if args:
            if len(args) != len(self.defn.arg_names):
                raise ValueError(
                    f"API call to {self} requires {len(self.defn.arg_names)} arguments, "
                    f"but got {len(args)}"
                )
            url_args = dict(zip(self.defn.arg_names, args))
        else:
            url_args = {
                name: kwargs.pop(name) for name in self.defn.arg_names if name in kwargs
            }

        missing_args = set(self.defn.arg_names) - set(url_args.keys())
        if missing_args:
            raise ValueError(
                f"API call to {self} missing required arguments: " + str(missing_args)
            )

        query = dict(**self.defn.default_query, **kwargs.get("query", {}))
        for k, v in query.items():
            if v is None:
                query[k] = url_args.pop(k)

        url = self.defn.url.format(**url_args)

        request = Request(
            method=self.defn.method,
            path=url,
            query=query,
        )

        if body is not None:
            if self.defn.body_model is not None:
                body = self.defn.body_model.parse_obj(body).json()
            request = request.with_options(body=body)

        response = self.api.request(request)
        if self.defn.response_model is None:
            return response
        else:
            obj = self.defn.response_model.parse_obj(response)
            return obj


class EndpointAction(BaseModel, Generic[R, M]):
    action_name: str
    url: Union[PathStr, str] = PathStr(__root__="")
    response_model: Optional[Type[R]]
    body_model: Optional[Type[M]] = None
    method: Union[HttpMethod, str] = HttpMethod.GET
    arg_names: List[str] = ()
    default_query: Dict[str, Optional[str]] = {}

    def create_endpoint_definition(
        self, url_prefix: PathStr, url_args: List[str]
    ) -> EndpointDefinition[R, M]:
        return EndpointDefinition(
            name=self.action_name,
            url=url_prefix / self.url,
            response_model=self.response_model,
            body_model=self.body_model,
            method=self.method,
            arg_names=[*url_args, *self.arg_names],
            default_query=self.default_query,
        )

    def create_endpoint(self, api: ApiBase, *args) -> Endpoint[R, M]:
        return Endpoint(
            defn=self.create_endpoint_definition(*args),
            api=api,
        )

    @classmethod
    def list(cls, response_model: Type[BaseModel], **kwargs) -> Self:
        return cls(
            action_name="list",
            method=HttpMethod.GET,
            response_model=response_model,
            **kwargs,
        )

    @classmethod
    def create(
        cls,
        body_model: Type[BaseModel],
        **kwargs,
    ) -> Self:
        return cls(
            action_name="create",
            method=HttpMethod.POST,
            body_model=body_model,
            **kwargs,
        )

    @classmethod
    def retrieve(cls, response_model: Type[BaseModel], **kwargs) -> Self:
        return cls(
            action_name="retrieve",
            method=HttpMethod.GET,
            url="/{id}",
            response_model=response_model,
            arg_names=["id"],
            **kwargs,
        )

    @classmethod
    def head(cls, **kwargs):
        return cls(
            action_name="head",
            method=HttpMethod.HEAD,
            url="/{id}",
            arg_names=["id"],
            **kwargs,
        )

    @classmethod
    def update(
        cls,
        body_model: Type[BaseModel],
        response_model: Optional[Type[BaseModel]] = None,
        **kwargs,
    ) -> Self:
        return cls(
            action_name="update",
            method=HttpMethod.PUT,
            body_model=body_model,
            response_model=response_model,
            **kwargs,
        )

    @classmethod
    def partial_update(cls, body_model: Type[BaseModel], **kwargs) -> Self:
        return cls(
            action_name="partial_update",
            method=HttpMethod.PATCH,
            body_model=body_model,
            **kwargs,
        )

    @classmethod
    def destroy(cls, **kwargs) -> Self:
        return cls(
            action_name="destroy",
            method=HttpMethod.DELETE,
            **kwargs,
        )


# TODO: This should probably be a metaclass? Like `pydantic.Field`, this is really more of a descriptor than a real object
class EndpointGroup:
    """A quick, OOP approach to creating a group of related endpoints.

    Consider the following API:

    ```
    class MyApi(JsonApiBase):
        ...

        list_objects = DeclarativeEndpoint("GET", "/objects/", response_model=MyObjectList)
        get_object = DeclarativeEndpoint("GET", "/objects/{id}", response_model=MyObject)
        post_object = get_object.make_post(body_model=MyObject, response_model=None)

    # Simple test
    api = MyApi()
    obj = MyObject(...)
    api.post_object(obj)
    result = api.get_object(id=obj.id)
    assert obj == result
    ```

    Instead, you can create a single group for these endpoints:
    ```
    class MyApi(JsonApiBase):
        my_object = EndpointGroup(
            url='/objects',
            actions=[
                EndpointAction.list(MyObjectList),
                EndpointAction.retrieve(MyObject),
                EndpointAction.create(MyObject),
            ]
        )

    api = MyApi()
    obj = MyObject(...)
    api.my_object.create(obj)
    result = api.my_object.retrieve(id=obj.id)
    assert obj == result
    ```

    This works best for REST APIs that follow common best practices, but can be customized where needed.
    """

    @validate_arguments
    def __init__(
        self,
        url: Union[PathStr, str],
        actions: Iterable[EndpointAction],
        arg_names: Iterable[str] = (),
    ):
        # Parent API tracking
        self.name = None

        # Instance attributes
        self.url = PathStr.parse_obj(url)
        self.actions: Dict[str, EndpointAction] = {a.action_name: a for a in actions}
        self.arg_names = arg_names

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance: ApiBase, owner: Type[ApiBase]):
        if instance is None:
            return self
        else:
            assert self.name is not None
            bound_group = BoundEndpointGroup(api=instance, group=self)
            instance.__dict__[self.name] = bound_group
            return bound_group


class BoundEndpointGroup:
    def __init__(self, api: ApiBase, group: EndpointGroup):
        self._group = group
        self._endpoints = {
            action_name: action.create_endpoint(api, group.url, group.arg_names)
            for action_name, action in group.actions.items()
        }

    def __getattr__(self, item):
        if item in self._endpoints:
            return self._endpoints[item]

        # TODO: This is a mess
        setattr(self, item, partial(getattr(type(self._group), item), self))
        return getattr(self, item)


class DeclarativeEndpoint(EndpointDefinition[R, M]):
    def _make_variant(self, **kwargs) -> Self:
        d = self.dict().copy()
        d.update(kwargs)
        return self.parse_obj(d)

    def make_head(self, **kwargs) -> Self:
        return self._make_variant(
            method="HEAD",
            response_model=None,
            body_model=None,
            **kwargs,
        )

    def make_post(self, **kwargs) -> Self:
        return self._make_variant(
            method="POST",
            **kwargs,
        )

    def make_put(self, **kwargs) -> Self:
        return self._make_variant(
            method="PUT",
            **kwargs,
        )

    def make_patch(self, **kwargs) -> Self:
        return self._make_variant(
            method="PATCH",
            **kwargs,
        )

    def make_delete(self, **kwargs):
        return self._make_variant(
            method="DELETE",
            response_model=None,
            body_model=None,
            **kwargs,
        )

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance: ApiBase, owner) -> Union[Endpoint[R, M], Self]:
        if instance is None:
            return self
        else:
            assert self.name is not None
            endpoint = Endpoint(defn=self, api=instance)
            instance.__dict__[self.name] = endpoint
            return endpoint
