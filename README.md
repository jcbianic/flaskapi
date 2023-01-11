<h1 align="center">Flask-Jeroboam</h1>

⚠️ Although Flask-Jeroboam has been extracted from code running in production, it is still in a very early stage and overfitted to one specific use case. So don't use it in production just yet.

<div align="center">

<i>Flask-Jeroboam is a Flask extension for request parsing, response serialization and OpenAPI auto-documentation.</i>

[![PyPI](https://img.shields.io/pypi/v/flask-jeroboam.svg)][pypi_]
[![Python Version](https://img.shields.io/pypi/pyversions/flask-jeroboam)][python version]
[![License](https://img.shields.io/github/license/jcbianic/flask-jeroboam?color=green)][license]
[![Commit](https://img.shields.io/github/last-commit/jcbianic/flask-jeroboam?color=green)][commit]

[![Read the documentation at https://flask-jeroboam.readthedocs.io/](https://img.shields.io/readthedocs/flask-jeroboam/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Maintainability](https://api.codeclimate.com/v1/badges/181b7355cee7b1316893/maintainability)](https://img.shields.io/codeclimate/maintainability/jcbianic/flask-jeroboam?color=green)
[![Test Coverage](https://api.codeclimate.com/v1/badges/181b7355cee7b1316893/test_coverage)](https://img.shields.io/codeclimate/coverage/jcbianic/flask-jeroboam?color=green)
[![Tests](https://github.com/jcbianic/flask-jeroboam/workflows/Tests/badge.svg)][tests]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi_]: https://pypi.org/project/flask-jeroboam/
[status]: https://pypi.org/project/flask-jeroboam/
[python version]: https://pypi.org/project/flask-jeroboam
[read the docs]: https://flask-jeroboam.readthedocs.io/
[tests]: https://github.com/jcbianic/flask-jeroboam/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/jcbianic/flask-jeroboam
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black
[commit]: https://img.shields.io/github/last-commit/jcbianic/flask-jeroboam

</div>

---

**Documentation**: [https://flask-jeroboam.readthedocs.io/](https://flask-jeroboam.readthedocs.io/)

**Source Code**: [https://github.com/jcbianic/flask-jeroboam](https://github.com/jcbianic/flask-jeroboam)

---

Flask-Jeroboam is a thin layer on top of Flask to make request parsing, response serialization and auto-documentation as smooth and easy as in FastAPI.

Its main features are:

- Request parsing based on typed annotations of endpoint arguments
- Response serialization facilitation
- (Planned) OpenAPI auto-Documentation based on the latters

## How to install

You can install _flask-jeroboam_ via [pip] or any other tool wired to [PyPI]:

```console
$ pip install flask-jeroboam
```

## How to use: Minimum Relevant Example

### A toy example

_flask-jeroboam_ exposes two public classes: **Jeroboam** and **APIBlueprint**. Use them to replace Flask's **Flask** and **Blueprint** classes.

```python
from flask-jeroboam import Jeroboam

app = Jeroboam()

@app.get("ping")
def ping():
    return "pong"
```

This example would behave exactly like a regular Flask app. You would start your server just like with Flask. `flask run` would do perfectly fine here.

Then hitting the endpoint with `curl localhost:5000/ping` would return the text response `pong`.

Let's try a more significant and relevant example and build a simplified endpoint to retrieve a list of wines.

### Searching for wines

```python
from typing import List, Dict
from typing import Tuple, Optional

from pydantic import BaseModel
from pydantic import Field

from flask_jeroboam import Jeroboam


app = Jeroboam(__name__)

# First we hard-code a minimal wine database. Tasty.
# In the real world this would obviously go in a proper database.
wines: List[Dict[str, str]] = [
    {
        "appellation": "Margaux",
        "domain": "Château Magaux",
        "cuvee": "Pavillon Rouge",
        "color": "Rouge",
    },
    {
        "appellation": "Meursault",
        "domain": "Domaine Comte Armand ",
        "cuvee": "Meursault",
        "color": "Blanc",
    },
    {
        "appellation": "Champagne",
        "domain": "Billecart-Salmon",
        "cuvee": "Brut - Blanc de Blancs",
        "color": "Blanc",
    },
    {
        "appellation": "Champagne",
        "domain": "Krug",
        "cuvee": "Grande Cuvée - 170ème Edition",
        "color": "Blanc",
    },
    {
        "appellation": "Champagne",
        "domain": "Maison Taittinger",
        "cuvee": "Grand Cru - Brut - Prélude",
        "color": "Blanc",
    },
]

# We then define Parser and Serialization Models.
# In the real world this would definitely go into seperate files.


class WineOut(BaseModel):
    """Serialization Model for a single wine."""

    appellation: str
    domain: str
    cuvee: str
    color: str


class WineListOut(BaseModel):
    """Serialization Model for a list of wines."""

    wines: List[WineOut]
    count: int
    total_count: int


class WineSearchIn(BaseModel):
    """The Request Model take pagination parameters and a search term."""

    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=2, ge=1, le=5)
    search: Optional[str] = Field(default=None)

    @property
    def offset(self):
        return (self.page - 1) * self.per_page


# We then define a CRUD function to use inside our endpoint.

def get_wines(wine_search: WineSearchIn) -> Tuple[List[Dict[str, str]], int]:
    """Basic READ function that take a parsed request object and return a list of matching wines."""
    if wine_search.search:
        selected_wines = [
            wine
            for wine in wines
            if wine_search.search.lower() in [value.lower() for value in wine.values()]
        ]
    else:
        selected_wines = wines
    total_count = len(selected_wines)
    max_bound = min(total_count, wine_search.offset + wine_search.per_page)
    selected_wines = selected_wines[wine_search.offset:max_bound]
    return selected_wines, total_count


# Finally we glue everything together in an endpoint.
@app.get("/wines", response_model=WineListOut)
def read_wine_list(wine_search: WineSearchIn):
    """Winelist endpoint."""
    wines, total_count = get_wines(wine_search)
    return {"wines": wines, "count": len(wines), "total_count": total_count}


if __name__ == "__main__":
    app.run()
```

You start/restart your server, then hitting the endpoint with `curl "localhost:5000/wines?page=1&per_page=2&search=Champagne"` would return:

```json
{
  "wines": [
    {
      "appellation": "Champagne",
      "domain": "Billecart-Salmon",
      "cuvee": "Brut - Blanc de Blancs",
      "color": "Blanc"
    },
    {
      "appellation": "Champagne",
      "domain": "Krug",
      "cuvee": "Grande Cuvée - 170ème Edition",
      "color": "Blanc"
    }
  ],
  "count": 2,
  "total_count": 3
}
```

See the documentation on more advanced usage: [https://flask-jeroboam.readthedocs.io/](https://flask-jeroboam.readthedocs.io/)

## Motivation

[FastAPI] has been rapidly gaining ground in Python Web Development since its inception in late 2018 ([1][survey]). Besides best-in-class performance, thanks to being based on Starlette, it brings a very compelling API for request parsing and response serialization that speed up API development by catering for Developer Experience.

While it is often compared to [Flask], ([1][ref#1], [2][ref#2] and [3][ref#3]), the comparaison feels a bit unfair. FastAPI is, in the words of its creator [@tiangolo], a thin layer on top of [Starlette], a _lightweight ASGI framework/toolkit, ... for building async web services in Python_ and [Pydantic]. To some extent, Flask seats in-between Starlette and FastAPI regarding abstraction level.

Although some excellent Flask extensions deal with request parsing, response serialization, and auto-documentation, I wanted something closer to [FastAPI]'s DX without compromises, hence **Flask - Jeroboam**.

[survey]: https://lp.jetbrains.com/python-developers-survey-2021/#FrameworksLibraries
[ref#1]: https://testdriven.io/blog/moving-from-flask-to-fastapi/
[ref#2]: https://developer.vonage.com/blog/21/08/10/the-ultimate-face-off-flask-vs-fastapi
[ref#3]: https://towardsdatascience.com/understanding-flask-vs-fastapi-web-framework-fe12bb58ee75

## A word on performance

One thing **Flask-Jeroboam** won't give you is performance improvement. Flask still handles the heavy lifting of a wsgi, so transitioning to **Flask-Jeroboam** won't speed up your app. Please remember that FastAPI's performance comes from Starlette, not FastAPI itself.

## Intended audience

The intended audience of **Flask-Jeroboam** is Flask developers who find FastAPI compelling but have excellent reasons to stick to Flask.

## License

Distributed under the terms of the [MIT license][license],
**Flask-Jeroboam** is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

The main inspiration for this project comes from [@tiangolo]'s [FastAPI].
[Flask] and [pydantic] are the two dependencies and handle the heavy lifting.
I used [@cjolowicz]'s [Hypermodern Python Cookiecutter] template to generate this project.

[@cjolowicz]: https://github.com/cjolowicz
[@tiangolo]: https://github.com/tiangolo
[fastapi]: https://fastapi.tiangolo.com/
[starlette]: https://www.starlette.io/
[flask]: https://flask.palletsprojects.com/
[pydantic]: https://pydantic-docs.helpmanual.io/
[pypi]: https://pypi.org/
[hypermodern python cookiecutter]: https://github.com/cjolowicz/cookiecutter-hypermodern-python
[file an issue]: https://github.com/jcbianic/flask-jeroboam/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/jcbianic/flask-jeroboam/blob/main/LICENSE
[contributor guide]: https://github.com/jcbianic/flask-jeroboam/blob/main/CONTRIBUTING.md
[command-line reference]: https://flask-jeroboam.readthedocs.io/en/latest/usage.html
