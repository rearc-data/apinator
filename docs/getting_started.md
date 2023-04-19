# Getting Started

```{mermaid}
sequenceDiagram
    participant User Code
    participant Endpoint
    participant API
    participant External Service

    User Code ->> API: api = Api(...)
    alt If setup is required
        API -->> External Service: Hi!
        External Service -->> API: Hello!
    end
    API ->> User Code: api
    User Code ->> Endpoint: api.put_object(obj)
    Endpoint -->> Endpoint: Validate obj against body model, generate request
    Endpoint -->> API: api.request(request_obj)
    API -->> API: Validate and complete request
    API -->> External Service: PUT /object
    External Service -->> API: 200 Response
    API -->> API: Validate response, perform any common cleanup
    API -->> Endpoint: response_obj
    Endpoint -->> Endpoint: Validate returned data against response model
    Endpoint ->> User Code: Instance of response model
```

## Writing the API

All API's inherit from {py:class}`~apinator.ApiBase`, which provides a basic interface for issuing requests. {py:class}`~apinator.JsonApiBase` can be used for services that exclusively return JSON data, and provides JSON extraction as an automatic cleanup step for all responses.

```python
from apinator import JsonApiBase

class MyApi(JsonApiBase):
    def __init__(self, ...):
        super().__init__(
            scheme="HTTPS",
            host="example.com",
            path_prefix="/api",
        )
```

We can then add endpoints to our API.

```python
from apinator import JsonApiBase, DeclarativeEndpoint

class MyApi(JsonApiBase):
    ...

    list_gizmos = DeclarativeEndpoint(method="GET", url="/gizmo")
    get_gizmo = DeclarativeEndpoint(method="GET", url="/gizmo/{id}", arg_names=["id"])
    post_gizmo = DeclarativeEndpoint(method="POST", url="/gizmo")
```

These endpoints can now be accessed as instance methods:

```python
api = MyApi()
objs = api.list_gizmos()
```

At this point, there's no data validation, so the return result is just whatever JSON object was returned from our service. Let's improve that:

```python
from apinator import JsonApiBase, DeclarativeEndpoint
from pydantic import BaseModel, AnyUrl
from typing import List, Optional

class MyGizmo(BaseModel):
    key: str
    value: str

class MyGizmoList(BaseModel):
    gizmos: List[MyGizmo]
    next_page: Optional[AnyUrl]

class MyApi(JsonApiBase):
    ...

    list_gizmos = DeclarativeEndpoint(method="GET", url="/gizmo", response_model=MyGizmoList)
    get_gizmo = DeclarativeEndpoint(method="GET", url="/gizmo/{id}", arg_names=["id"], response_model=MyGizmo)
    post_gizmo = DeclarativeEndpoint(method="POST", url="/gizmo", body_model=MyGizmo)
```

Now our API will automatically validate all data, and return well-typed gizmos instead of arbitrary JSON objects:

```python
api = MyApi()
objs: MyGizmoList = api.list_gizmos()
```

Finally, let's notice that we seem to have a variety of endpoints that all relate to a single concept: gizmo's. {py:class}`~apinator.EndpointGroup`s provide a concise way to put all these endpoints together, and {py:class}`~apinator.EndpointAction`s provide easy templates for common URL and HTTP Method structures available for such REST endpoint groups:

```python
from apinator import JsonApiBase, EndpointGroup, EndpointAction
from pydantic import BaseModel, AnyUrl
from typing import List, Optional

class MyGizmo(BaseModel):
    key: str
    value: str

class MyGizmoList(BaseModel):
    gizmos: List[MyGizmo]
    next_page: Optional[AnyUrl]

class MyApi(JsonApiBase):
    ...

    gizmo = EndpointGroup(
        url="/gizmo",
        actions=[
            # GET /object -> MyGizmoList.parse_obj(response.json())
            EndpointAction.list(MyGizmoList),
            # GET /object/{id} -> MyGizmo.parse_obj(response.json())
            EndpointAction.retrieve(MyGizmo),
            # MyGizmo.parse_obj(body).json() -> POST /object
            EndpointAction.create(MyGizmo),
        ]
    )
```

```python
api = MyApi()
objs: MyGizmoList = api.gizmo.list()
some_obj: MyGizmo = api.gizmo.retrieve("old_key")
api.gizmo.create(MyGizmo(key="my_key", value="my_value"))
```

## Going beyond basic endpoints

While the basic base classes provided by {py:mod}`apinator` are a quick way to get started, ideally an API binding should be customized for the particular ways an external service is likely to be used. Expanding on the above example, let's say it's common to append values to existing keys, but that this isn't provided as a single REST command on the back-end. Let's implement this as a helper method by customizing {py:class}`~apinator.EndpointGroup`:

```python
from apinator import JsonApiBase, EndpointGroup, EndpointAction

class GizmoGroup(EndpointGroup):
    def __init__(self):
        super().__init__(
            url="/gizmo",
            actions=[
                # GET /object -> MyGizmoList.parse_obj(response.json())
                EndpointAction.list(MyGizmoList),
                # GET /object/{id} -> MyGizmo.parse_obj(response.json())
                EndpointAction.retrieve(MyGizmo),
                # MyGizmo.parse_obj(body).json() -> PUT /object
                EndpointAction.update(MyGizmo),
            ]
        )

    def append_value(self, key, suffix):
        gizmo: MyGizmo = self.retrieve(key)
        gizmo.value += suffix
        self.update(gizmo)

class MyApi(JsonApiBase):
    ...

    gizmo = GizmoGroup()

api = MyApi()
api.gizmo.append_value("key", "_modified")
```

A common use case might be to add functionality for supporting paginated list operations:

```python
from apinator import JsonApiBase, EndpointGroup, EndpointAction
from typing import Iterable

class PaginatedEndpointGroup(EndpointGroup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert 'list' in self.actions

    def iterate(self):
        current_list = self.list(0)
        yield from current_list.results
        while current_list.next_page is not None:
            current_list = self.list(1)
            yield from current_list.results

class MyApi(JsonApiBase):
    ...

    gizmo = PaginatedEndpointGroup(
        url="/gizmo",
        actions=[
            EndpointAction.list(MyGizmoList, default_query={"page": None})
        ]
    )

api = MyApi()
objs: Iterable[MyGizmo] = api.gizmo.iterate()
```

Similarly, we could provide helper methods on the API definition itself:

```python
from apinator import JsonApiBase, DeclarativeEndpoint
from pydantic import BaseModel
from requests import HTTPError

class PingResponse(BaseModel):
    success: bool

class MyApi(JsonApiBase):
    ...

    ping = DeclarativeEndpoint(url='/ping', response_model=PingResponse)

    def is_alive(self) -> bool:
        try:
            return self.ping().success
        except HTTPError:
            return False
```
