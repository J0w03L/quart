from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Dict, IO, Optional, Type, TYPE_CHECKING
from uuid import UUID

from jinja2.utils import htmlsafe_json_dumps as jinja_htmlsafe_dumps
from werkzeug.http import http_date

from ..globals import _cv_app, _cv_request, _cv_websocket, current_app, request, websocket

if TYPE_CHECKING:
    from ..app import Quart  # noqa: F401
    from ..wrappers import Response  # noqa: F401


def _dump_arg_defaults(kwargs: Dict[str, Any], app: Optional["Quart"] = None) -> Dict[str, Any]:
    json_encoder: Type[json.JSONEncoder] = JSONEncoder
    if app is None and _cv_app.get(None) is not None:  # has_app_context requires a circular import
        app = current_app._get_current_object()  # type: ignore

    if app is not None:
        json_encoder = app.json_encoder
        blueprint = None
        if _cv_request.get(None) is not None:  # has_request_context requires a circular import
            blueprint = app.blueprints.get(request.blueprint)
        if _cv_websocket.get(None) is not None:  # has_websocket_context requires a circular import
            blueprint = app.blueprints.get(websocket.blueprint)
        if blueprint is not None and blueprint.json_encoder is not None:
            json_encoder = blueprint.json_encoder
        kwargs.setdefault("ensure_ascii", app.config["JSON_AS_ASCII"])
        kwargs.setdefault("sort_keys", app.config["JSON_SORT_KEYS"])
    kwargs.setdefault("sort_keys", True)
    kwargs.setdefault("cls", json_encoder)
    return kwargs


def dumps(object_: Any, app: Optional["Quart"] = None, **kwargs: Any) -> str:
    kwargs = _dump_arg_defaults(kwargs, app)
    return json.dumps(object_, **kwargs)


def dump(object_: Any, fp: IO[str], app: Optional["Quart"] = None, **kwargs: Any) -> None:
    kwargs = _dump_arg_defaults(kwargs, app)
    json.dump(object_, fp, **kwargs)


def _load_arg_defaults(kwargs: Dict[str, Any], app: Optional["Quart"] = None) -> Dict[str, Any]:
    json_decoder: Type[json.JSONDecoder] = JSONDecoder
    if app is None and _cv_app.get(None) is not None:  # has_app_context requires a circular import
        app = current_app._get_current_object()  # type: ignore

    if app is not None:
        json_decoder = app.json_decoder
        blueprint = None
        if _cv_request.get(None) is not None:  # has_request_context requires a circular import
            blueprint = app.blueprints.get(request.blueprint)
        if _cv_websocket.get(None) is not None:  # has_websocket_context requires a circular import
            blueprint = app.blueprints.get(websocket.blueprint)
        if blueprint is not None and blueprint.json_decoder is not None:
            json_decoder = blueprint.json_decoder
    kwargs.setdefault("cls", json_decoder)
    return kwargs


def loads(object_: str, app: Optional["Quart"] = None, **kwargs: Any) -> Any:
    kwargs = _load_arg_defaults(kwargs, app)
    return json.loads(object_, **kwargs)


def load(fp: IO[str], app: Optional["Quart"] = None, **kwargs: Any) -> Any:
    kwargs = _load_arg_defaults(kwargs, app)
    return json.load(fp, **kwargs)


def htmlsafe_dumps(object_: Any, **kwargs: Any) -> str:
    return jinja_htmlsafe_dumps(object_, dumps=dumps, **kwargs)


def jsonify(*args: Any, **kwargs: Any) -> "Response":
    if args and kwargs:
        raise TypeError("jsonify() behavior undefined when passed both args and kwargs")
    elif len(args) == 1:
        data = args[0]
    else:
        data = args or kwargs

    indent = None
    separators = (",", ":")
    if current_app.config["JSONIFY_PRETTYPRINT_REGULAR"] or current_app.debug:
        indent = 2
        separators = (", ", ": ")

    body = dumps(data, indent=indent, separators=separators)
    return current_app.response_class(body, content_type=current_app.config["JSONIFY_MIMETYPE"])


class JSONEncoder(json.JSONEncoder):
    def default(self, object_: Any) -> Any:
        if isinstance(object_, date):
            return http_date(object_)
        if isinstance(object_, (Decimal, UUID)):
            return str(object_)
        if is_dataclass(object_):
            return asdict(object_)
        if hasattr(object_, "__html__"):
            return str(object_.__html__())
        return super().default(object_)


class JSONDecoder(json.JSONDecoder):
    pass
