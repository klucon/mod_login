# mod_login — Frontend login modul pro KLUCON CMS

Widget pro přihlášení a správu uživatelské session ve frontend tématu. Vykresluje se do libovolné pozice tématu přes `{{ render_position('...') }}`.

## Chování

- **Nepřihlášený uživatel** — zobrazí inline přihlašovací formulář (výchozí) nebo odkaz na stránku přihlášení.
- **Přihlášený uživatel** — zobrazí uživatelské jméno, odkaz na profil a odkaz na odhlášení.

## Nastavení

| Klíč | Výchozí | Popis |
|------|---------|-------|
| `style` | `inline` | `inline` = formulář přímo, `link` = jen odkaz |
| `show_username` | `true` | Zobrazit uživatelské jméno přihlášeného |
| `show_profile_link` | `true` | Zobrazit odkaz na profil |
| `css_class` | — | Volitelná CSS třída wrapperu |

## Vývoj a testy

```bash
cd module/mod_login
pip install -e ".[dev]"
pytest -q
```
