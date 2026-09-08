from pathlib import Path

from basic_web_backend.application import WebApplication
from basic_web_backend.config import ApplicationConfig

from basic_web_server import Server as LemaServer

BASE_DIRECTORY = Path(__file__).parent

config = ApplicationConfig(
    template_folder=BASE_DIRECTORY / "templates",
    template_cache=True,
    template_auto_reload=True,
    static_folder=BASE_DIRECTORY / "static",
    static_url_path="/static",
    debug=True
)

app = WebApplication(config=config)

USERS = [
    {
        "username": "martin",
        "name": "Martin",
        "active": True,
        "roles": ["Developer", "Tester"]
    },
    {
        "username": "alice",
        "name": "Alice",
        "active": True,
        "roles": ["Designer"]
    },
    {
        "username": "guest",
        "name": "Guest",
        "active": False,
        "roles": []
    }

]

@app.route(path="/", methods=["GET"])
def index(request):
    return app.render_template(
        template_name="index.html",
        title="Template example",
        users=USERS
    )

@app.route(path="/users/<string:username>", methods=["GET"])
def profile(request, username):
    selected_user = None

    for user in USERS:
        if user["username"] == username:
            selected_user = user
            break

    if selected_user is None:
        selected_user = {
            "username": username,
            "name": username,
            "active": False,
            "roles": []
        }

    return app.render_template("profile.html", title="User Profile", user=selected_user)


server = LemaServer(app)
server.start_console()