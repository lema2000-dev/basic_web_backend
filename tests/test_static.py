import pytest

from basic_web_backend.exceptions import NotFound
from basic_web_backend.static import StaticFileHandler


def test_static_file_handler_serves_file(
    tmp_path,
):
    static_folder = tmp_path / "static"
    static_folder.mkdir()

    css_file = static_folder / "style.css"
    css_file.write_text(
        "body { color: red; }",
        encoding="utf-8",
    )

    handler = StaticFileHandler(
        static_folder
    )

    response = handler.serve("style.css")

    assert response == (
        b"body { color: red; }",
        200,
        {
            "Content-Type": "text/css",
        },
    )


def test_static_file_handler_serves_nested_file(
    tmp_path,
):
    static_folder = tmp_path / "static"
    image_folder = static_folder / "images"
    image_folder.mkdir(parents=True)

    image_file = image_folder / "logo.png"
    image_file.write_bytes(b"PNG data")

    handler = StaticFileHandler(
        static_folder
    )

    response = handler.serve(
        "images/logo.png"
    )

    assert response == (
        b"PNG data",
        200,
        {
            "Content-Type": "image/png",
        },
    )


def test_static_file_handler_raises_not_found_for_missing_file(
    tmp_path,
):
    static_folder = tmp_path / "static"
    static_folder.mkdir()

    handler = StaticFileHandler(
        static_folder
    )

    with pytest.raises(NotFound):
        handler.serve("missing.css")


def test_static_file_handler_rejects_directory(
    tmp_path,
):
    static_folder = tmp_path / "static"
    nested_folder = static_folder / "images"
    nested_folder.mkdir(parents=True)

    handler = StaticFileHandler(
        static_folder
    )

    with pytest.raises(NotFound):
        handler.serve("images")


def test_static_file_handler_rejects_path_traversal(
    tmp_path,
):
    static_folder = tmp_path / "static"
    static_folder.mkdir()

    secret_file = tmp_path / "secret.txt"
    secret_file.write_text(
        "secret",
        encoding="utf-8",
    )

    handler = StaticFileHandler(
        static_folder
    )

    with pytest.raises(NotFound):
        handler.serve("../secret.txt")


def test_static_file_handler_rejects_absolute_path(
    tmp_path,
):
    static_folder = tmp_path / "static"
    static_folder.mkdir()

    secret_file = tmp_path / "secret.txt"
    secret_file.write_text(
        "secret",
        encoding="utf-8",
    )

    handler = StaticFileHandler(
        static_folder
    )

    with pytest.raises(NotFound):
        handler.serve(str(secret_file))


def test_static_file_handler_rejects_symlink_outside_static_folder(
    tmp_path,
):
    static_folder = tmp_path / "static"
    static_folder.mkdir()

    secret_file = tmp_path / "secret.txt"
    secret_file.write_text(
        "secret",
        encoding="utf-8",
    )

    symlink = static_folder / "secret-link.txt"
    symlink.symlink_to(secret_file)

    handler = StaticFileHandler(
        static_folder
    )

    with pytest.raises(NotFound):
        handler.serve("secret-link.txt")

def test_static_file_handler_accepts_custom_headers(
    tmp_path,
):
    static_folder = tmp_path / "static"
    static_folder.mkdir()

    file_path = static_folder / "style.css"
    file_path.write_text(
        "body {}",
        encoding="utf-8",
    )

    handler = StaticFileHandler(
        static_folder
    )

    response = handler.serve(
        filename="style.css",
        headers={
            "Cache-Control": "public, max-age=3600",
        },
    )

    assert response == (
        b"body {}",
        200,
        {
            "Cache-Control": "public, max-age=3600",
            "Content-Type": "text/css",
        },
    )

def test_static_file_handler_can_serve_attachment(
    tmp_path,
):
    static_folder = tmp_path / "static"
    static_folder.mkdir()

    file_path = static_folder / "report.pdf"
    file_path.write_bytes(b"PDF data")

    handler = StaticFileHandler(
        static_folder
    )

    response = handler.serve(
        filename="report.pdf",
        as_attachment=True,
        download_name="annual-report.pdf",
    )

    assert response == (
        b"PDF data",
        200,
        {
            "Content-Type": "application/pdf",
            "Content-Disposition": (
                'attachment; '
                'filename="annual-report.pdf"'
            ),
        },
    )