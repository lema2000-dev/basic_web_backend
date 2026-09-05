from pathlib import Path

from basic_web_backend.application import (
    WebApplication,
)
from basic_web_backend.config import (
    ApplicationConfig,
)
from basic_web_backend.exceptions import (
    BadRequest,
)
from basic_web_backend.response import (
    html_response,
    json_response,
)
from basic_web_server.server import Server


EXAMPLE_FOLDER = Path(__file__).parent
STATIC_FOLDER = EXAMPLE_FOLDER / "static"


config = ApplicationConfig(
    static_folder=STATIC_FOLDER,
    static_url_path="/static",
    max_content_length=5_000_000,
)

app = WebApplication(config=config)


@app.route("/")
def index(request):
    return html_response(
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">

            <meta
                name="viewport"
                content="width=device-width, initial-scale=1"
            >

            <title>Multipart upload</title>

            <link
                rel="stylesheet"
                href="/static/style.css"
            >

            <script
                src="/static/app.js"
                defer
            ></script>
        </head>

        <body>
            <main class="container">
                <h1>Multipart file upload</h1>

                <p>
                    Select a file and send it to
                    the backend.
                </p>

                <form id="upload-form">
                    <label for="description">
                        Description
                    </label>

                    <input
                        id="description"
                        name="description"
                        type="text"
                        value="Example document"
                    >

                    <label for="document">
                        Document
                    </label>

                    <input
                        id="document"
                        name="document"
                        type="file"
                        required
                    >

                    <button type="submit">
                        Upload
                    </button>
                </form>

                <pre id="upload-result">
No file uploaded yet.
                </pre>
            </main>
        </body>
        </html>
        """
    )


@app.route(
    "/api/upload",
    methods=["POST"],
)
def upload_file(request):
    form, files = request.get_multipart()

    descriptions = form.get(
        "description",
        [],
    )
    uploaded_files = files.get(
        "document",
        [],
    )

    if not uploaded_files:
        raise BadRequest(
            "A document file is required."
        )

    uploaded_file = uploaded_files[0]

    description = (
        descriptions[0]
        if descriptions
        else ""
    )

    return json_response(
        {
            "description": description,
            "filename": uploaded_file.filename,
            "content_type": (
                uploaded_file.content_type
            ),
            "size": len(uploaded_file.body),
        }
    )


server = Server(app)
server.start_console()