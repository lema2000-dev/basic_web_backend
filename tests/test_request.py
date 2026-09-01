from basic_web_backend.request import Request

def test_request_has_default_values():
    request = Request("GET", "/test")
    assert request.method == "GET"
    assert request.path == "/test"
    assert request.query_string == ""
    assert request.body == b""
    assert request.headers == []
    assert request.query == {}

def test_request_normalizes_method_to_uppercase():
    request = Request("post", "/test")
    assert request.method == "POST"

def test_request_preserves_path_and_body():
    body = b'{"key": "value"}'

    request = Request("POST", "/test", body=body)

    assert request.path == "/test"
    assert request.body is body

def test_request_accepts_headers_as_dict():
    headers = {"Content-Type": "application/json", "Authorization": "Bearer token"}
    request = Request("GET", "/test", headers=headers)

    assert request.headers == [
        ("content-type", "application/json"),
        ("authorization", "Bearer token")
    ]

def test_request_preservers_repeated_headers():
    headers = [("Content-Type", "application/json"), ("Content-Type", "text/plain")]
    request = Request("GET", "/test", headers=headers)

    assert request.headers == [
        ("content-type", "application/json"),
        ("content-type", "text/plain")
    ]

def test_get_header_is_case_insensitive():
    headers = {"Content-Type": "application/json"}
    request = Request("GET", "/test", headers=headers)

    assert request.get_header("content-type") == "application/json"
    assert request.get_header("CONTENT-TYPE") == "application/json"
    assert request.get_header("Content-Type") == "application/json"

def test_get_header_returns_first_repeated_value():
    headers = [("Content-Type", "application/json"), ("Content-Type", "text/plain")]
    request = Request("GET", "/test", headers=headers)

    assert request.get_header("content-type") == "application/json"

def test_get_header_returns_default_for_missing_header():
    request = Request("GET", "/test")

    assert request.get_header("missing-header", default="default-value") == "default-value"
    assert request.get_header("missing-header") is None

def test_get_headers_returns_all_matching_values():
    headers = [("Content-Type", "application/json"), ("Content-Type", "text/plain")]
    request = Request("GET", "/test", headers=headers)

    assert request.get_headers("content-type") == ["application/json", "text/plain"]
    assert request.get_headers("missing-header") == []

def test_request_preserves_repeated_query_parameters():
    query_string = "param=value1&param=value2&other=single"
    request = Request("GET", "/test", query_string=query_string)

    assert request.query == {
        "param": ["value1", "value2"],
        "other": ["single"]
    }

def test_request_preserves_blank_query_values():
    query_string = "param=&other=single"
    request = Request("GET", "/test", query_string=query_string)

    assert request.query == {
        "param": [""],
        "other": ["single"]
    }

def test_request_decodes_query_parameters():
    query_string = "messege=Hello+World%21"
    request = Request("GET", "/test", query_string=query_string)

    assert request.query == {
        "messege": ["Hello World!"]
    }


    