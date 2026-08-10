from utils.error_handlers import ApiError, handle_api_error, invalid_request_body_response, internal_server_error_response, value_error_response


def test_invalid_request_body_response_uses_standard_error_shape():
    response, status_code = invalid_request_body_response()

    assert status_code == 400
    assert response.get_json() == {
        "status": "error",
        "error_code": "invalid_request",
        "message": "Invalid request body",
    }


def test_value_error_response_uses_standard_error_shape():
    response, status_code = value_error_response(ValueError("duplicate role"))

    assert status_code == 422
    assert response.get_json() == {
        "status": "error",
        "message": "duplicate role",
    }


def test_internal_server_error_response_uses_standard_error_shape():
    response, status_code = internal_server_error_response()

    assert status_code == 500
    assert response.get_json() == {
        "status": "error",
        "error_code": "internal_server_error",
        "message": "Internal server error",
    }


def test_value_error_response_infers_conflict_code_for_duplicate_user_errors():
    response, status_code = value_error_response(ValueError("User Already Exists!"))

    assert status_code == 422
    payload = response.get_json()
    assert payload["status"] == "error"
    assert payload["error_code"] == "user_already_exists"
    assert payload["message"] == "User Already Exists!"
    assert payload["details"] == {
        "code": "user_already_exists",
        "domain": "user",
        "operation": "create",
        "message": "The requested user already exists.",
    }


def test_value_error_response_infers_validation_code_for_invalid_password_errors():
    response, status_code = value_error_response(ValueError("Invalid Password!"))

    assert status_code == 422
    payload = response.get_json()
    assert payload["status"] == "error"
    assert payload["error_code"] == "invalid_password"
    assert payload["message"] == "Invalid Password!"
    assert payload["details"] == {
        "code": "invalid_password",
        "domain": "user",
        "operation": "create",
        "message": "The provided password does not meet the validation requirements.",
    }


def test_value_error_response_includes_domain_specific_details_for_resource_errors():
    folder_response, folder_status = value_error_response(ValueError("Folder not found!"))
    password_response, password_status = value_error_response(ValueError("Password not found!"))
    role_response, role_status = value_error_response(ValueError("Role Not Found!"))

    assert folder_status == 422
    assert folder_response.get_json()["details"] == {
        "code": "folder_not_found",
        "domain": "folder",
        "operation": "lookup",
        "message": "The requested folder could not be found.",
    }

    assert password_status == 422
    assert password_response.get_json()["details"] == {
        "code": "password_not_found",
        "domain": "password",
        "operation": "lookup",
        "message": "The requested password could not be found.",
    }

    assert role_status == 422
    assert role_response.get_json()["details"] == {
        "code": "role_not_found",
        "domain": "role",
        "operation": "lookup",
        "message": "The requested role could not be found.",
    }


def test_handle_api_error_uses_standard_error_shape_and_payload_details():
    response, status_code = handle_api_error(ApiError("Conflict detected", status_code=409, payload={"code": "duplicate"}))

    assert status_code == 409
    assert response.get_json() == {
        "status": "error",
        "message": "Conflict detected",
        "details": {"code": "duplicate"},
    }
