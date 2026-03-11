def user_is_admin(user):
    if not getattr(user, "is_authenticated", False):
        return False

    meta = getattr(user, "meta", {}) or {}
    roles = meta.get("roles", [])

    return any(
        (
            meta.get("is_admin") is True,
            meta.get("admin") is True,
            meta.get("role") == "admin",
            isinstance(roles, list) and "admin" in roles,
        )
    )
