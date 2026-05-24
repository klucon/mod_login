from __future__ import annotations

import json
from html import escape

from sqlalchemy import text


def _settings(settings: str) -> dict[str, object]:
    raw = (settings or "").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _bool(value: object, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() not in ("false", "0", "no", "")
    return default if value is None else bool(value)


def _locale(context: dict) -> str:
    return str(context.get("locale") or "cs_CZ")


def _request(context: dict) -> object:
    return context.get("request")


def _is_logged_in(context: dict) -> bool:
    request = _request(context)
    if request is None:
        return False
    cookies = getattr(request, "cookies", {})
    return bool(cookies.get("access_token"))


def _csrf(context: dict) -> str:
    request = _request(context)
    if request is None:
        return ""
    session = getattr(request, "session", {})
    return str(session.get("_csrf") or "")


async def _com_user_urls(db: object, locale: str) -> tuple[str, str, str]:
    """Return (login_url, logout_url, profile_url) for the current locale."""
    _SLUGS: dict[str, dict[str, str]] = {
        "cs_CZ": {
            "slug": "uzivatele",
            "login": "prihlasit",
            "logout": "odhlasit",
            "profile": "profil",
        },
        "en_GB": {
            "slug": "users",
            "login": "login",
            "logout": "logout",
            "profile": "profile",
        },
    }
    parts = _SLUGS.get(locale) or _SLUGS["cs_CZ"]

    if db is not None:
        try:
            row = (
                await db.execute(
                    text(
                        "SELECT value FROM system_settings WHERE id = 1 LIMIT 1"
                    )
                )
            ).mappings().first()
        except Exception:
            pass

    slug = parts["slug"]
    return (
        f"/{slug}/{parts['login']}",
        f"/{slug}/{parts['logout']}",
        f"/{slug}/{parts['profile']}",
    )


async def _username(db: object, request: object) -> str:
    """Resolve logged-in username from cookie → DB."""
    if db is None or request is None:
        return ""
    cookies = getattr(request, "cookies", {})
    token = str(cookies.get("access_token") or "")
    if not token:
        return ""
    try:
        import jwt
        from src.config import get_settings
        settings = get_settings()
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return str(payload.get("sub") or "")
    except Exception:
        return ""


def _t(locale: str) -> dict[str, str]:
    _CS = {
        "login": "Přihlásit se",
        "logout": "Odhlásit se",
        "profile": "Profil",
        "username_label": "Uživatelské jméno",
        "password_label": "Heslo",
        "submit": "Přihlásit se",
    }
    _EN = {
        "login": "Log in",
        "logout": "Log out",
        "profile": "Profile",
        "username_label": "Username",
        "password_label": "Password",
        "submit": "Log in",
    }
    return _CS if locale.startswith("cs") else _EN


def _wrap(html: str, css_class: str) -> str:
    cls = escape(css_class.strip(), quote=True)
    wrapper_class = f"mod-login {cls}".strip()
    return f'<div class="{wrapper_class}">{html}</div>'


def _render_logged_in(
    *,
    username: str,
    logout_url: str,
    profile_url: str,
    show_username: bool,
    show_profile_link: bool,
    labels: dict[str, str],
) -> str:
    parts: list[str] = []
    if show_username and username:
        parts.append(
            f'<span class="mod-login__username">{escape(username)}</span>'
        )
    if show_profile_link:
        parts.append(
            f'<a class="mod-login__profile-link" href="{escape(profile_url, quote=True)}">'
            f'{labels["profile"]}</a>'
        )
    parts.append(
        f'<a class="mod-login__logout-link" href="{escape(logout_url, quote=True)}">'
        f'{labels["logout"]}</a>'
    )
    return "".join(parts)


def _render_inline_form(
    *,
    login_url: str,
    csrf: str,
    labels: dict[str, str],
    request: object,
) -> str:
    action = escape(login_url, quote=True)
    csrf_input = f'<input type="hidden" name="_csrf" value="{escape(csrf, quote=True)}">'
    # preserve redirect back to current page
    current_path = ""
    url_obj = getattr(request, "url", None)
    if url_obj:
        current_path = str(getattr(url_obj, "path", "") or "")
    next_input = (
        f'<input type="hidden" name="next" value="{escape(current_path, quote=True)}">'
        if current_path else ""
    )
    return (
        f'<form class="mod-login__form" method="post" action="{action}">'
        f"{csrf_input}{next_input}"
        f'<div class="mod-login__field">'
        f'<label class="mod-login__label">{labels["username_label"]}'
        f'<input class="mod-login__input" type="text" name="username" autocomplete="username" required>'
        f"</label></div>"
        f'<div class="mod-login__field">'
        f'<label class="mod-login__label">{labels["password_label"]}'
        f'<input class="mod-login__input" type="password" name="password" autocomplete="current-password" required>'
        f"</label></div>"
        f'<button class="mod-login__submit" type="submit">{labels["submit"]}</button>'
        f"</form>"
    )


def _render_link(*, login_url: str, labels: dict[str, str]) -> str:
    return (
        f'<a class="mod-login__link" href="{escape(login_url, quote=True)}">'
        f'{labels["login"]}</a>'
    )


async def render(context: dict | None = None) -> str:
    context = context or {}
    db = context.get("db")
    locale = _locale(context)
    settings = _settings(str(context.get("settings") or ""))
    style = str(settings.get("style") or "inline").strip()
    show_username = _bool(settings.get("show_username"), default=True)
    show_profile_link = _bool(settings.get("show_profile_link"), default=True)
    css_class = str(settings.get("css_class") or "").strip()
    labels = _t(locale)
    request = _request(context)

    login_url, logout_url, profile_url = await _com_user_urls(db, locale)

    if _is_logged_in(context):
        username = await _username(db, request)
        html = _render_logged_in(
            username=username,
            logout_url=logout_url,
            profile_url=profile_url,
            show_username=show_username,
            show_profile_link=show_profile_link,
            labels=labels,
        )
    elif style == "inline":
        html = _render_inline_form(
            login_url=login_url,
            csrf=_csrf(context),
            labels=labels,
            request=request,
        )
    else:
        html = _render_link(login_url=login_url, labels=labels)

    return _wrap(html, css_class)
