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

def test_post_put_have_request_body(openapi_schema):
    for path, methods in openapi_schema["paths"].items():
        for method, op in methods.items():
            if method.lower() not in {"post", "put", "patch"}:
                continue

            assert "requestBody" in op, f"{method.upper()} {path} missing requestBody"

            content = op["requestBody"].get("content", {})
            assert "application/json" in content
            assert "schema" in content["application/json"]
