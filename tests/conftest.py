import pytest
import structlog
from django.conf import settings
from structlog.testing import LogCapture

from jobserver.authorization.roles import CoreDeveloper

from .factories import OrgFactory, OrgMembershipFactory, UserFactory


@pytest.fixture
def api_rf():
    from rest_framework.test import APIRequestFactory

    return APIRequestFactory()


@pytest.fixture
def core_developer():
    return UserFactory(roles=[CoreDeveloper])


@pytest.fixture(name="log_output")
def fixture_log_output():
    return LogCapture()


@pytest.fixture(autouse=True)
def fixture_configure_structlog(log_output):
    structlog.configure(processors=[log_output])


@pytest.fixture(autouse=True)
def set_release_storage(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "RELEASE_STORAGE", tmp_path / "releases")


@pytest.fixture
def user():
    """
    Generate a User instance with useful things attached

    We almost always want a User to be part of an OpenSAFELY Org and have that
    Org tied to a GitHub Organisation.
    """
    org = OrgFactory(name="OpenSAFELY", slug="opensafely")
    user = UserFactory()

    # Make the User part of the Org
    OrgMembershipFactory(org=org, user=user)

    return user
