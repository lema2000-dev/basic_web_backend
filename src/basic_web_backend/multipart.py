from dataclasses import dataclass
from email.parser import BytesParser
from email.policy import default

from .exceptions import BadRequest

@dataclass
class UploadedFile:
    filename: str
    content_type: str | None
    body: bytes
    headers: dict

def parse_multipart(body, boundary, charset="utf-8"):
    _validate_inputs(body=body, boundary=boundary)

    message = _parse_multipart_message(body=body, boundary=boundary)

    if not message.is_multipart():
        raise BadRequest("The request body is not valid multipart data.")

    if message.defects:
        raise BadRequest("The request body contains malformed multipart data.")

    form = {}
    files = {}

    for part in message.iter_parts():
        _process_part(part=part, form=form, files=files, default_charset=charset)

    return form, files

def _validate_inputs(body, boundary):
    if not isinstance(body, bytes):
        raise BadRequest("The multipart body must be bytes.")
    if not isinstance(boundary, str):
        raise BadRequest("The multipart boundary must be text.")
    if not boundary:
        raise BadRequest("The multipart boundary is missing or empty.")
    if "\n" in boundary or "\r" in boundary:
        raise BadRequest("The multipart boundary is invalid.")

def _parse_multipart_message(body, boundary):
    try:
        boundary_bytes = boundary.encode("ascii")
    except UnicodeEncodeError:
        raise BadRequest("The multipart boundary must contain only ASCII characters.")

    excaped_boundary = boundary_bytes.replace(b'"', b'\\"').replace(b'\\', b'\\\\')

    synthetic_headers = (
        b"Content-Type: multipart/form-data; "
        b'boundary="'
        + excaped_boundary 
        + b'"\r\n'
        + b"MIME-Version: 1.0\r\n"
        + b"\r\n"
    )

    return BytesParser(policy=default).parsebytes(synthetic_headers + body)

def _process_part(part, form, files, default_charset):
    if part.get_content_disposition() != "form-data":
        raise BadRequest("Each multipart part must use form-data content disposition.")

    field_name = part.get_param("name", header="content-disposition")

    if not field_name:
        raise BadRequest("Each multipart part must have a field name.")

    payload = part.get_payload(decode=True)

    if payload is None:
        payload = b""

    filename = part.get_filename()

    if filename is not None:
        uploaded_file = UploadedFile(
            filename=filename,
            content_type=_get_part_content_type(part=part),
            body=payload,
            headers=dict(part.items()),
        )

        files.setdefault(field_name, []).append(uploaded_file)

        return

    text = _decode_form_field(part=part, payload=payload, default_charset=default_charset)

    form.setdefault(field_name, []).append(text)

def _get_part_content_type(part):
    if part.get("Content-Type") is None:
        return None

    return part.get_content_type()

def _decode_form_field(part, payload, default_charset):
    charset = part.get_content_charset() or default_charset

    try:
        return payload.decode(charset)
    except LookupError as error:
        raise BadRequest(f"Unsupported multipart character encoding: {charset}") from error
    except UnicodeDecodeError as error:
        raise BadRequest(f"A multipart form field cannot be decoded using {charset}.") from error

