import pytest
from openapi_spec_validator.validation.exceptions import OpenAPIValidationError
from openapi_spec_validator import validate


OPENAPI_SCHEMA = None


def test_openapi_schema_is_valid(openapi_schema):
    try:
        validate(openapi_schema)
        print("\n--- Swagger: Schema structure is VALID against OpenAPI specification. ---")
    except OpenAPIValidationError as e:
        pytest.fail(f"OpenAPI Schema Validation Failed: {e}")


def test_openapi_schema_contains_expected_endpoints(openapi_schema):
    paths = openapi_schema['paths']

    assert "/devices/" in paths
    assert '/devices/status' in paths
    assert "/devices/{device_id}" in paths
    assert "/devices/{device_id}/command" in paths