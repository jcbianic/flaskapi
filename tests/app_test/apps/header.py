"""A Test Blueprint for testing Header Params.

The corresponding test can be found in tests/test_inbound/test_header
"""

from flask_jeroboam import Blueprint
from flask_jeroboam import Header


router = Blueprint("headers_params_router", __name__, tags=["Header"])


@router.get("/headers/int")
def get_header_as_plain_int(test_header: int = Header()):
    return {"header": test_header}


@router.get("/headers/str")
def get_header_as_plain_str(test_header: str = Header()):
    return {"header": test_header}
