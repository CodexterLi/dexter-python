from app.api.api import api_router as legacy_api_router
from app.api.router import api_router
from app.utils.snowflake import generate_id as legacy_generate_id
from app.utils.timezone import tz as legacy_tz
from packages.common import generate_id, utc_now


def test_api_router_compatibility_wrapper() -> None:
    assert legacy_api_router is api_router


def test_common_package_helpers_and_compatibility_wrappers() -> None:
    assert isinstance(generate_id(), int)
    assert isinstance(legacy_generate_id(), int)
    assert utc_now().tzinfo is not None
    assert legacy_tz.now().tzinfo is not None
