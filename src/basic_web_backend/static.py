from pathlib import Path

from .exceptions import NotFound
from .response import file_response

class StaticFileHandler:
    def __init__(self, static_folder):
        self.static_folder = Path(static_folder).resolve()

    def serve(self, filename, status_code=200, headers=None, as_attachment=False, download_name=None):
        try:
            file_path = (self.static_folder / filename).resolve()

        except (OSError, RuntimeError):
            raise NotFound(path=filename)

        if not file_path.is_relative_to(self.static_folder):
            raise NotFound(path=filename)

        if not file_path.is_file():
            raise NotFound(path=filename)

        try:
            return file_response(file_path=file_path, status_code=status_code, headers=headers, as_attachment=as_attachment, download_name=download_name)
        except (FileNotFoundError, PermissionError, IsADirectoryError):
            raise NotFound(path=filename)

        

