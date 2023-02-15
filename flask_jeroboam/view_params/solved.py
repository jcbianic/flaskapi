"""Solved Specialized Params.

Params are solved at registration time. This way we reduce indirections when
handling requests thus reducing overhead.
"""
import re
from copy import deepcopy
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Type
from typing import Union

from flask import request
from pydantic import BaseConfig
from pydantic.error_wrappers import ErrorWrapper
from pydantic.errors import MissingError
from pydantic.fields import FieldInfo
from pydantic.fields import ModelField
from werkzeug.datastructures import FileStorage
from werkzeug.datastructures import MultiDict

from flask_jeroboam.utils import is_sequence_field

from .helpers import _extract_scalar
from .helpers import _extract_sequence
from .helpers import _extract_subfields
from .parameters import ParamLocation
from .parameters import ViewParameter


empty_field_info = FieldInfo()


class SolvedParameter(ModelField):
    """Generic Solved Parameter."""

    def __init__(
        self,
        *,
        name: str,
        type_: type,
        required: bool = False,
        view_param: Optional[ViewParameter] = None,
        class_validators: Optional[Dict] = None,
        model_config: Type[BaseConfig] = BaseConfig,
        field_info: FieldInfo = empty_field_info,
        **kwargs,
    ):
        self.name = name
        self.location: ParamLocation = getattr(
            view_param, "location", ParamLocation.unknown
        )
        if self.location == ParamLocation.file:
            model_config.arbitrary_types_allowed = True
        self.required = required
        self.embed = getattr(view_param, "embed", None)
        self.in_body = getattr(view_param, "in_body", None)
        default = getattr(view_param, "default", field_info.default)
        class_validators = class_validators or {}
        kwargs["alias"] = kwargs.get("alias", getattr(view_param, "alias", None))
        super().__init__(
            name=name,
            type_=type_,
            class_validators={},
            default=default,
            required=required,
            model_config=model_config,
            field_info=view_param,
            **kwargs,
        )

    @classmethod
    def specialize(
        cls,
        *,
        name: str,
        type_: type,
        required: bool = False,
        view_param: Optional[ViewParameter] = None,
        class_validators: Optional[Dict] = None,
        model_config: Type[BaseConfig] = BaseConfig,
        field_info: FieldInfo = empty_field_info,
        **kwargs,
    ):
        """Specialize the Current class to each location."""
        location = getattr(view_param, "location", ParamLocation.unknown)
        target_class = {
            ParamLocation.query: SolvedQueryParameter,
            ParamLocation.header: SolvedHeaderParameter,
            ParamLocation.path: SolvedPathParameter,
            ParamLocation.cookie: SolvedCookieParameter,
            ParamLocation.body: SolvedBodyParameter,
            ParamLocation.file: SolvedFileParameter,
            ParamLocation.form: SolvedFormParameter,
        }.get(location, cls)

        return target_class(
            name=name,
            type_=type_,
            required=required,
            view_param=view_param,
            class_validators=class_validators,
            model_config=model_config,
            field_info=field_info,
            **kwargs,
        )

    def validate_request(self):
        """Validate the request."""
        values = {}
        errors = []
        assert self.location is not None  # noqa: S101
        inbound_values = self._get_values()
        if inbound_values is None and self.required:
            errors.append(
                ErrorWrapper(MissingError(), loc=(self.location.value, self.alias))
            )
            return values, errors
        elif inbound_values is None and not self.required:
            inbound_values = deepcopy(self.default)
        values_, errors_ = self.validate(
            inbound_values, values, loc=(self.location.value, self.alias)
        )
        if isinstance(errors_, ErrorWrapper):
            errors.append(errors_)
        else:
            values[self.name] = values_
        return values, errors

    def _get_values(
        self,
    ) -> Union[FileStorage, MultiDict, dict, Optional[str], List[Any]]:
        """The Value extraction method is specialized by location."""
        raise NotImplementedError


class SolvedPathParameter(SolvedParameter):
    """Solved Path parameter."""

    def _get_values(self) -> Union[dict, Optional[str], List[Any]]:
        source: dict = request.view_args or {}
        return _extract_scalar(source=source, alias=self.alias, name=self.name)


class SolvedHeaderParameter(SolvedParameter):
    """Solved Header parameter."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alias = re.sub(
            r"_(\w)", lambda x: f"-{x.group(1).upper()}", self.name.capitalize()
        )

    def _get_values(self) -> Union[dict, Optional[str], List[Any]]:
        source: dict = request.headers or {}
        return _extract_scalar(source=source, alias=self.alias, name=self.name)


class SolvedCookieParameter(SolvedParameter):
    """Solved Cookie parameter."""

    def _get_values(self) -> Union[dict, Optional[str], List[Any]]:
        source: dict = request.cookies or {}
        return _extract_scalar(source=source, alias=self.alias, name=self.name)


class SolvedQueryParameter(SolvedParameter):
    """Solved Query parameter."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self.type_, "__fields__"):
            self.extractor = _extract_subfields
        elif is_sequence_field(self):
            self.extractor = _extract_sequence
        else:
            self.extractor = _extract_scalar

    def _get_values(self) -> Union[dict, Optional[str], List[Any]]:
        source: MultiDict = request.args
        return self.extractor(
            source=source,
            alias=self.alias,
            name=self.name,
            fields=getattr(self.type_, "__fields__", {}),
        )


class SolvedBodyParameter(SolvedParameter):
    """Solved Scalar Query parameter."""

    def _get_values(self) -> Union[dict, Optional[str], List[Any]]:
        source: dict = request.json or {}
        return source.get(self.alias or self.name) if self.embed else source


class SolvedFileParameter(SolvedParameter):
    """Solved File Parameter."""

    def _get_values(
        self,
    ) -> Union[FileStorage, MultiDict, dict, Optional[str], List[Any]]:
        source: MultiDict = request.files or MultiDict()
        return source.get(self.alias or self.name) if self.embed else source


class SolvedFormParameter(SolvedParameter):
    """Solved Form parameter."""

    def _get_values(self) -> Union[dict, Optional[str], List[Any]]:
        source: MultiDict = request.form or MultiDict()
        return source.get(self.alias or self.name) if self.embed else source
