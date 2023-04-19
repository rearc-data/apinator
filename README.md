[![Documentation Status](https://readthedocs.org/projects/apinator/badge/?version=latest)](https://apinator.readthedocs.io/en/latest/?badge=latest)

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

## Overview

REST API's are getting more standardized, but binding to those from code remains an obnoxious problem that still requires a good deal of custom code. To address this, code generators have arisen ([such as the excellent `datamodel-code-generator`](https://pypi.org/project/datamodel-code-generator/) project) to create code and data models based on OpenAPI specifications. To this approach, `apinator` offers the following additions:

- *Eliminate boilerplate*
- *Enhance usability*
- *Centralize and de-duplicate effort*
- *Strict typing, when appropriate*

### Eliminate Boilerplate

 Code generators often produce dependency-free libraries, but that involves duplicating boilerplate into each of those libraries. `apinator` instead provides a powerful, low-dependency core that those libraries can build on top of. This eliminates duplicate code, allows for upgrading all bindings simultaneously, and offers bugfixes and new features without re-generating code for particular APIs.

### Enhance Usability

Code generators do so much for us, we overlook how much they don't do. They generally specialize in handling the enormous variety of inputs (e.g. multiple versions of OpenAPI specs) rather than producing a highly-usable binding on the other end. `apinator` reverses this and focuses on providing highly usable API binding patterns, and ignores how those are bound to any particular API.

### Centralize and De-Duplicate Effort

Code generators are great, but ideally, for any particular API, their results would be published and saved in one central location. This would make it easier to publish official (or at least well-maintained) Python API bindings to various services without requiring a great deal of effort on the part of those services. `apinator` strives to make this process as simple as possible by letting service-specific bindings focus solely on service-specific API changes instead of on producing a well-standardized Python library around that API.


### Strict Typing, When Appropriate

Many API's are moving to JSON for moving non-trivial data in both directions. These JSON blobs generally follow a well-defined schema that's often only available from some documentation source.

`apinator` makes it easy to bind `pydantic` data models to both API request and response bodies, providing a seamless, type-checked interface for both arguments and responses. This results in the REST API feeling more like a Python function and less like a network call, and results in API calls being easy to understand by static type checkers (e.g. `mypy` or your IDE). No more wrangling arbitrary dictionaries and lists: bind your data to a model, and know what you're dealing with.

`pydantic` is a tremendous project for providing the right amount of static typing to Python. It works well with virtually every static type checker and is becoming a _de facto_ standard in strictly typed (but still flexible) data-oriented classes in Python. `pydantic` rose to fame in part for being the foundation that makes `fastapi` to fast to use and write. `apinator` leverages that same power for the other side of the network connection.

## Documentation

For further examples and explanations, [see the docs.](https://apinator.readthedocs.io/).
