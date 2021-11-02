from datetime import timedelta

from django.utils import timezone
from environs import Env


env = Env()


backends = [
    {
        "id": 1,
        "name": "EMIS",
        "slug": "emis",
        "is_active": True,
        "level_4_url": "",
    },
    {
        "id": 2,
        "name": "Expectations",
        "slug": "expectations",
        "is_active": False,
        "level_4_url": "",
    },
    {
        "id": 3,
        "name": "TPP",
        "slug": "tpp",
        "is_active": True,
        "level_4_url": "http://localhost:8001",
    },
    {
        "id": 6,
        "name": "Graphnet",
        "slug": "graphnet",
        "is_active": False,
        "level_4_url": "",
    },
    {
        "id": 5,
        "name": "Test",
        "slug": "test",
        "is_active": False,
        "level_4_url": "https://test.opensafely.org",
    },
    {
        "id": 4,
        "name": "databricks",
        "slug": "databricks",
        "is_active": False,
        "level_4_url": "",
    },
]

available_backends = {
    "databricks",
    "emis",
    "expectations",
    "tpp",
    "test",
    "graphnet",
}


def backends_to_choices(backends):
    return [(b.slug, b.name) for b in backends]


def ensure_backends():
    """
    Ensure the configured backends are present in the database

    We want to ensure Backends are configured in the database, but adding them
    via migrations caused problems (particularly with tests).  This lets us
    have a statically defined list of them, while keeping them in the database
    at runtime so we can keep using FKs to them.

    We keep the PK constant, but allow the configuration of the other fields.
    Auth tokens are generated by the running application and can be rotated in
    the Staff Area so changing one doesn't require a deploy.
    """
    from jobserver.models import Backend

    for backend in backends:
        backend, created = Backend.objects.update_or_create(
            pk=backend["id"],
            defaults={
                "name": backend["name"],
                "slug": backend["slug"],
                "is_active": backend["is_active"],
                "level_4_url": backend["level_4_url"],
            },
        )


def get_configured_backends():
    """Get a list of configured Backends from the env"""
    backends = env.list("BACKENDS", default=[])

    # remove whitespace and only return non-empty strings
    backends = {u.strip() for u in backends if u}

    unknown = backends - available_backends
    if unknown:
        sorted_unknown = sorted(unknown)
        raise Exception(f"Unknown backends: {', '.join(sorted_unknown)}")

    return backends


def show_warning(last_seen, minutes=5):
    if last_seen is None:
        return False

    now = timezone.now()
    threshold = timedelta(minutes=minutes)
    delta = now - last_seen

    if delta < threshold:
        return False

    return True
