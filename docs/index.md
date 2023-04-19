```{toctree}
:hidden:

overview
getting_started
Reference <api/apinator>
```

# Apinator

A simple foundation for building great client-side REST API bindings.

What does a great client-side REST API look like?

```python
from apinator_myservice import MyServiceApi

api = MyServiceApi()
obj = api.some_custom_object.retrieve("key")
obj.attribute = "new value"
api.some_custom_object.update("key", body=obj)
```

Ok, but what did it take to implement that?

```python
from apinator.api import JsonApiBase
from apinator.endpoint import EndpointGroup, EndpointAction

from .models import CustomObjectModel  # a Pydantic model

class MyServiceApi(JsonApiBase):
    some_custom_object = EndpointGroup(
        url='/object',
        actions=[
            # GET /object/<id>
            EndpointAction.retrieve(CustomObjectModel),
            # POST /object
            EndpointAction.create(CustomObjectModel),
        ]
    )
```

## Installation

In general, you won't install `apinator` directly, you'll install the `apinator`-based API libraries that you want to use. However, `apinator` is available on PyPI:

```bash
pip install apinator
```

## Usage

### Using a particular API

Ideally, the specific API you use should provide simple docs around how it wraps the service of interest. However, there are some general constructs that `apinator` provides that you'll find in various API's.

*API* instances are used to manage configuration around using an API. For example, an API constructor might take credentials, or allow you to specify which API endpoint you want to target (if a service is available under multiple endpoints). All other features are accessed under an API instance.

*Endpoints* are directly callable REST methods that run against the backend API. E.g., a `GET` call to `/ping` may be exposed as `api.ping()`. Endpoints are presented as methods on the API instance, and offer positional and keyword arguments if necessary.

*EndpointGroups* are groups of endpoints, characterized by "actions" (or "verbs") associated with a particular type of object. These map internally to endpoints, particular REST calls against single endpoints.

Between Endpoint Groups (for mapping multiple verbs around a particular object type) and endpoints (for mapping individual REST paths), an API can map out the raw calls possible on a REST API. These calls can be used as-is, or wrapped by the API or endpoint groups into more useful methods (e.g., updating a remote object, combining a `GET` with a `PUT`).

### Writing an API

Writing an API is as simple as writing a class based on {py:class}`~apinator.ApiBase`, and adding either {py:class}`~apinator.DeclarativeEndpoint` or {py:class}`~apinator.EndpointGroup`s to the class. See [the getting started guide](./getting_started.md) for more details.
