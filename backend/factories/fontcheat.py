import fontawesome as fa


def search_icon_5(name: str) -> str | None:
    """Return a Font Awesome 5 class string if *name* matches a known icon."""
    if name.lower() in fa.icons:
        return f"fab fa-{name.lower()}"
    return None
