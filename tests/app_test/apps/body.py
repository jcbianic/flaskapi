"""A Test Blueprint for testing Body Params.

The corresponding test can be found in tests/test_inbound/test_body
"""
from flask_jeroboam import Blueprint
from flask_jeroboam import Body
from tests.app_test.models.inbound import SimpleModelIn


router = Blueprint("body_params_router", __name__, tags=["Body"])


@router.post("/body/int")
def post_body_as_int(payload: int = Body(embed=True)):
    """Body Param as plain int."""
    return {"payload": payload}


@router.post("/body/str")
def post_body_as_str(payload: str = Body(embed=True)):
    """Body Param as plain str."""
    return {"payload": payload}


@router.post("/body/base_model")
def post_base_model_in_form(payload: SimpleModelIn = Body(embed=False)):
    """POST Form Parameter as pydantic BaseModel."""
    return payload.json()


@router.post("/body/multi_primitive")
def post_multi_primitive_body_arguments(
    age: int = Body(media_type="application/json"),
    name: str = Body(media_type="application/ujson"),
):
    return {"age": age, "name": name}
