from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "src/modules/mod_login/module.py"
SPEC = importlib.util.spec_from_file_location("mod_login_module", MODULE_PATH)
assert SPEC and SPEC.loader
_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(_mod)

render = _mod.render
_settings = _mod._settings
_bool = _mod._bool
_is_logged_in = _mod._is_logged_in
_render_logged_in = _mod._render_logged_in
_render_inline_form = _mod._render_inline_form
_render_link = _mod._render_link
_wrap = _mod._wrap


# ── _settings ────────────────────────────────────────────────────────────────

def test_settings_empty() -> None:
    assert _settings("") == {}


def test_settings_valid_json() -> None:
    assert _settings('{"style": "link"}') == {"style": "link"}


def test_settings_invalid_json() -> None:
    assert _settings("not-json") == {}


# ── _bool ────────────────────────────────────────────────────────────────────

def test_bool_true_values() -> None:
    assert _bool(True) is True
    assert _bool("true") is True
    assert _bool(1) is True


def test_bool_false_values() -> None:
    assert _bool(False) is False
    assert _bool("false") is False
    assert _bool("0") is False


def test_bool_none_uses_default() -> None:
    assert _bool(None, default=True) is True
    assert _bool(None, default=False) is False


# ── _is_logged_in ─────────────────────────────────────────────────────────────

class _Request:
    def __init__(self, *, token: str = "", path: str = "/", session: dict | None = None):
        self.cookies = {"access_token": token} if token else {}
        self.url = type("URL", (), {"path": path})()
        self.session = session or {}


def test_is_logged_in_with_token() -> None:
    ctx = {"request": _Request(token="sometoken")}
    assert _is_logged_in(ctx) is True


def test_is_logged_in_without_token() -> None:
    ctx = {"request": _Request()}
    assert _is_logged_in(ctx) is False


def test_is_logged_in_no_request() -> None:
    assert _is_logged_in({}) is False


# ── _render_logged_in ─────────────────────────────────────────────────────────

def test_render_logged_in_shows_username() -> None:
    labels = {"profile": "Profil", "logout": "Odhlásit se"}
    html = _render_logged_in(
        username="alice", logout_url="/odhlasit", profile_url="/profil",
        show_username=True, show_profile_link=True, labels=labels,
    )
    assert "alice" in html
    assert "/profil" in html
    assert "/odhlasit" in html


def test_render_logged_in_hides_username() -> None:
    labels = {"profile": "Profile", "logout": "Log out"}
    html = _render_logged_in(
        username="bob", logout_url="/logout", profile_url="/profile",
        show_username=False, show_profile_link=True, labels=labels,
    )
    assert "bob" not in html


def test_render_logged_in_hides_profile() -> None:
    labels = {"profile": "Profile", "logout": "Log out"}
    html = _render_logged_in(
        username="carol", logout_url="/logout", profile_url="/profile",
        show_username=True, show_profile_link=False, labels=labels,
    )
    assert "/profile" not in html
    assert "/logout" in html


def test_render_logged_in_escapes_username() -> None:
    labels = {"profile": "P", "logout": "L"}
    html = _render_logged_in(
        username='<script>xss</script>', logout_url="/l", profile_url="/p",
        show_username=True, show_profile_link=False, labels=labels,
    )
    assert "<script>" not in html


# ── _render_inline_form ───────────────────────────────────────────────────────

def test_render_inline_form_contains_inputs() -> None:
    labels = {"username_label": "User", "password_label": "Pass", "submit": "Go"}
    html = _render_inline_form(
        login_url="/login", csrf="tok123", labels=labels, request=_Request(path="/home"),
    )
    assert 'type="text"' in html
    assert 'type="password"' in html
    assert "tok123" in html
    assert 'action="/login"' in html


def test_render_inline_form_next_param() -> None:
    labels = {"username_label": "U", "password_label": "P", "submit": "S"}
    html = _render_inline_form(
        login_url="/login", csrf="", labels=labels, request=_Request(path="/akce"),
    )
    assert 'name="next"' in html
    assert "/akce" in html


# ── _render_link ──────────────────────────────────────────────────────────────

def test_render_link() -> None:
    html = _render_link(login_url="/login", labels={"login": "Přihlásit se"})
    assert "Přihlásit se" in html
    assert 'href="/login"' in html


# ── _wrap ─────────────────────────────────────────────────────────────────────

def test_wrap_adds_class() -> None:
    html = _wrap("<span>x</span>", "my-class")
    assert "mod-login my-class" in html


def test_wrap_no_extra_class() -> None:
    html = _wrap("<span>x</span>", "")
    assert 'class="mod-login"' in html


# ── render — integration ──────────────────────────────────────────────────────

async def test_render_not_logged_in_inline() -> None:
    ctx = {
        "request": _Request(),
        "locale": "cs_CZ",
        "settings": '{"style": "inline"}',
        "db": None,
    }
    html = await render(ctx)
    assert "mod-login" in html
    assert 'type="text"' in html


async def test_render_not_logged_in_link() -> None:
    ctx = {
        "request": _Request(),
        "locale": "cs_CZ",
        "settings": '{"style": "link"}',
        "db": None,
    }
    html = await render(ctx)
    assert "mod-login" in html
    assert "prihlasit" in html
    assert 'type="text"' not in html


async def test_render_not_logged_in_en() -> None:
    ctx = {
        "request": _Request(),
        "locale": "en_GB",
        "settings": '{"style": "link"}',
        "db": None,
    }
    html = await render(ctx)
    assert "Log in" in html


async def test_render_empty_context() -> None:
    html = await render(None)
    assert "mod-login" in html


async def test_render_css_class_applied() -> None:
    ctx = {
        "request": _Request(),
        "locale": "cs_CZ",
        "settings": '{"style": "link", "css_class": "navbar-login"}',
        "db": None,
    }
    html = await render(ctx)
    assert "navbar-login" in html
