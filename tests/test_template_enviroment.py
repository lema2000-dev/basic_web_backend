import pytest

from basic_web_backend.exceptions import TemplateNotFound
from basic_web_backend.template.environment import TemplateEnvironment

def test_enviroment_renders_template_file(tmp_path):
    template_folder = tmp_path / "templates"
    template_folder.mkdir()
    template_file = template_folder / "profile.html"
    template_file.write_text("<h1>Hello, {{ username }}!</h1>", encoding="utf-8")

    environment = TemplateEnvironment(template_folder=template_folder)
    result = environment.render("profile.html", username="Martin")

    assert result == "<h1>Hello, Martin!</h1>"

def test_enviroment_renders_nested_template(tmp_path):
    template_folder = tmp_path / "templates"
    user_folder = template_folder / "users"
    user_folder.mkdir(parents=True)
    template_file = user_folder / "profile.html"
    template_file.write_text("<h1>Hello, {{ user.name }}!</h1>", encoding="utf-8")

    environment = TemplateEnvironment(template_folder=template_folder)
    result = environment.render("users/profile.html", user={"name": "Martin"})
    assert result == "<h1>Hello, Martin!</h1>"

def test_enviroment_rejects_missing_template(tmp_path):
    template_folder = tmp_path / "templates"
    template_folder.mkdir()

    environment = TemplateEnvironment(template_folder=template_folder)

    with pytest.raises(TemplateNotFound) as error_info:
        environment.render("missing.html")

    assert error_info.value.template_name == "missing.html"

def test_enviroment_rejects_path_traversal(tmp_path):
    template_folder = tmp_path / "templates"
    template_folder.mkdir()

    secret_file = tmp_path / "secret.html"
    secret_file.write_text("<h1>Secret</h1>", encoding="utf-8")

    enviroment = TemplateEnvironment(template_folder=template_folder)

    with pytest.raises(TemplateNotFound):
        enviroment.render("../secret.html")

def test_enviroment_rejects_directory(tmp_path):
    template_folder = tmp_path / "templates"
    template_folder.mkdir()

    nested_folder = template_folder / "users"
    nested_folder.mkdir()

    enviroment = TemplateEnvironment(template_folder=template_folder)
    with pytest.raises(TemplateNotFound):
        enviroment.render("users")

def test_enviroment_supports_custom_encoding(tmp_path):
    template_folder = tmp_path / "templates"
    template_folder.mkdir()
    template_file = template_folder / "message.html"
    template_file.write_text("<p>Hello, {{ name }}!</p>", encoding="utf-16")

    enviroment = TemplateEnvironment(template_folder=template_folder, encoding="utf-16")
    result = enviroment.render("message.html", name="Martin")

    assert result == "<p>Hello, Martin!</p>"

def test_enviroment_uses_cahed_template(tmp_path):
    template_folder = tmp_path / "templates"
    template_folder.mkdir()
    template_file = template_folder / "message.html"
    template_file.write_text("First: {{ value }}", encoding="utf-8")

    enviroment = TemplateEnvironment(template_folder=template_folder, cache_enabled=True, auto_reload=False)
    first_result = enviroment.render("message.html", value="One")
    template_file.write_text("Changed: {{ value }}", encoding="utf-8")
    second_result = enviroment.render("message.html", value="Two")
    assert first_result == "First: One"
    assert second_result == "First: Two"  # Cached template is used, so the change is not reflected

def test_enviroment_can_disable_cache(tmp_path):
    template_folder = tmp_path / "templates"
    template_folder.mkdir()
    template_file = template_folder / "message.html"
    template_file.write_text("First", encoding="utf-8")
    enviroment = TemplateEnvironment(template_folder=template_folder, cache_enabled=False)

    assert enviroment.render("message.html") == "First"

    template_file.write_text("Changed", encoding="utf-8")

    assert enviroment.render("message.html") == "Changed"  # Cache is disabled, so the change is reflected

def test_enviroment_auto_reloads_changed_file(tmp_path):
    template_folder = tmp_path / "templates"
    template_folder.mkdir()
    template_file = template_folder / "message.html"
    template_file.write_text("First", encoding="utf-8")
    enviroment = TemplateEnvironment(template_folder=template_folder, cache_enabled=True, auto_reload=True)

    assert enviroment.render("message.html") == "First"

    template_file.write_text("Changed content", encoding="utf-8")

    assert enviroment.render("message.html") == "Changed content"  # Auto-reload is enabled, so the change is reflected

def test_enviroment_clears_one_cached_template(tmp_path):
    template_folder = tmp_path / "templates"
    template_folder.mkdir()
    template_file = template_folder / "message.html"
    template_file.write_text("First", encoding="utf-8")
    enviroment = TemplateEnvironment(template_folder=template_folder)
    enviroment.render("message.html")
    template_file.write_text("Changed", encoding="utf-8")
    enviroment.clear_cache("message.html")

    assert enviroment.render("message.html") == "Changed"  # Cache is cleared, so the change is reflected

def test_enviroment_clears_complete_cache(tmp_path):
    template_folder = tmp_path / "templates"
    template_folder.mkdir()
    first_file = template_folder / "first.html"
    second_file = template_folder / "second.html"

    first_file.write_text("First old", encoding="utf-8")
    second_file.write_text("Second old", encoding="utf-8")

    enviroment = TemplateEnvironment(template_folder=template_folder)

    enviroment.render("first.html")
    enviroment.render("second.html")

    first_file.write_text("First new", encoding="utf-8")
    second_file.write_text("Second new", encoding="utf-8")

    enviroment.clear_cache()

    assert enviroment.render("first.html") == "First new"
    assert enviroment.render("second.html") == "Second new"