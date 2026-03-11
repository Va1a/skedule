from functools import wraps

from flask import abort

from skedule import db
from skedule.models import Feature


FEATURE_DEFINITIONS = {
    "logs": {
        "label": "Logs",
        "icon": "file-text",
        "description": "Show log entry and log viewer navigation across the app.",
        "default_enabled": False,
    },
    "leaderboard": {
        "label": "Leaderboard",
        "icon": "bar-chart-2",
        "description": "Enable the leaderboard page and its navigation link.",
        "default_enabled": False,
    },
    "discussion": {
        "label": "Discussion",
        "icon": "smile",
        "description": "Enable the discussion page and its navigation link.",
        "default_enabled": False,
    },
}


def sync_defined_features():
    existing_features = {
        feature.name: feature
        for feature in Feature.query.filter(
            Feature.name.in_(FEATURE_DEFINITIONS.keys())
        ).all()
    }

    created = False
    for name, definition in FEATURE_DEFINITIONS.items():
        if name in existing_features:
            continue
        feature = Feature(
            name=name,
            enabled=definition.get("default_enabled", False),
        )
        db.session.add(feature)
        existing_features[name] = feature
        created = True

    if created:
        db.session.commit()

    return existing_features


def get_feature_entries():
    feature_rows = sync_defined_features()
    return [
        {
            "name": name,
            "label": definition["label"],
            "icon": definition["icon"],
            "description": definition["description"],
            "enabled": feature_rows[name].enabled,
        }
        for name, definition in FEATURE_DEFINITIONS.items()
    ]


def get_feature_entry(name):
    feature_rows = sync_defined_features()
    definition = FEATURE_DEFINITIONS.get(name)
    if definition is None:
        return None

    return {
        "name": name,
        "label": definition["label"],
        "icon": definition["icon"],
        "description": definition["description"],
        "enabled": feature_rows[name].enabled,
    }


def is_feature_enabled(name):
    definition = FEATURE_DEFINITIONS.get(name)
    if definition is None:
        return False

    feature = Feature.query.filter_by(name=name).first()
    if feature is None:
        return definition.get("default_enabled", False)
    return feature.enabled


def set_enabled_features(feature_names):
    sync_defined_features()
    requested_features = set(feature_names)
    features = Feature.query.filter(Feature.name.in_(FEATURE_DEFINITIONS.keys())).all()
    for feature in features:
        feature.enabled = feature.name in requested_features
    db.session.commit()


def set_feature_enabled(name, enabled):
    if name not in FEATURE_DEFINITIONS:
        return None

    feature = Feature.query.filter_by(name=name).first()
    if feature is None:
        feature = Feature(
            name=name,
            enabled=FEATURE_DEFINITIONS[name].get("default_enabled", False),
        )
        db.session.add(feature)

    feature.enabled = enabled
    db.session.commit()
    return feature


def feature_required(name):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if not is_feature_enabled(name):
                abort(404)
            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator
