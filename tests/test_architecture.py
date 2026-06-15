from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.docs import SCALAR_DOCS_PATH, register_api_docs
from app.api.router import api_router
from app.utils.snowflake import generate_id as legacy_generate_id
from app.utils.timezone import tz as legacy_tz
from packages.common import generate_id, utc_now


def test_scalar_docs_route_is_registered_outside_openapi_schema() -> None:
    app = FastAPI(title="Test API")
    register_api_docs(app)

    response = TestClient(app).get(SCALAR_DOCS_PATH)

    assert response.status_code == 200
    assert "Scalar" in response.text
    assert SCALAR_DOCS_PATH not in app.openapi()["paths"]


def test_openapi_schema_includes_request_and_response_descriptions() -> None:
    schema = api_router.openapi_schema if hasattr(api_router, "openapi_schema") else None
    assert schema is None

    from app.main import app

    openapi = app.openapi()
    schemas = openapi["components"]["schemas"]

    assert schemas["LoginRequest"]["properties"]["username"]["description"] == "用户名"
    assert schemas["TokenResponse"]["properties"]["expires_in"]["description"] == "访问令牌过期时间，单位秒"
    assert openapi["paths"]["/api/auth/login"]["post"]["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/TokenResponse")


def test_common_package_helpers_and_compatibility_wrappers() -> None:
    assert isinstance(generate_id(), int)
    assert isinstance(legacy_generate_id(), int)
    assert utc_now().tzinfo is not None
    assert legacy_tz.now().tzinfo is not None
