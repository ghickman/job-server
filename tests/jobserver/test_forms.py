import pytest
from django.core.exceptions import ValidationError

from jobserver.backends import backends_to_choices
from jobserver.forms import JobRequestCreateForm, UserForm, WorkspaceCreateForm
from jobserver.models import Backend


@pytest.mark.django_db
def test_jobrequestcreateform_with_single_backend():
    emis = Backend.objects.get(slug="emis")
    choices = backends_to_choices([emis])
    form = JobRequestCreateForm({"backend": "emis"}, backends=choices)

    assert "backend" in form.fields
    assert form.fields["backend"].choices == choices

    assert form.is_valid, form.errors


@pytest.mark.django_db
def test_jobrequestcreateform_with_multiple_backends():
    choices = backends_to_choices(Backend.objects.all())
    form = JobRequestCreateForm({"backend": "tpp"}, backends=choices)

    assert "backend" in form.fields
    assert form.fields["backend"].choices == choices

    assert form.is_valid, form.errors


@pytest.mark.django_db
def test_userform_success():
    available_backends = Backend.objects.filter(slug__in=["emis", "tpp", "test"])

    data = {
        "backends": ["emis", "tpp"],
        "is_superuser": ["on"],
        "roles": [],
    }

    form = UserForm(
        available_backends=available_backends,
        available_roles=[],
        data=data,
    )

    assert form.is_valid(), form.errors

    output = set(form.cleaned_data["backends"].values_list("slug", flat=True))
    expected = set(
        Backend.objects.filter(slug__in=["emis", "tpp"]).values_list("slug", flat=True)
    )
    assert output == expected

    assert form.cleaned_data["is_superuser"]


@pytest.mark.django_db
def test_userform_with_no_backends():
    available_backends = Backend.objects.filter(slug__in=["tpp"])

    data = {
        "backends": [],
        "is_superuser": ["on"],
        "roles": [],
    }

    form = UserForm(
        available_backends=available_backends,
        available_roles=[],
        data=data,
    )

    assert form.is_valid()
    assert len(form.cleaned_data["backends"]) == 0


@pytest.mark.django_db
def test_userform_with_unknown_backend():
    available_backends = Backend.objects.filter(slug__in=["emis", "tpp", "test"])

    data = {
        "backends": ["emis", "tpp", "unknown"],
        "is_superuser": [""],
        "roles": [],
    }

    form = UserForm(
        available_backends=available_backends,
        available_roles=[],
        data=data,
    )

    assert not form.is_valid()
    assert form.errors == {
        "backends": [
            "Select a valid choice. unknown is not one of the available choices."
        ]
    }


@pytest.mark.django_db
def test_workspacecreateform_success():
    data = {
        "name": "test",
        "db": "slice",
        "repo": "http://example.com/derp/test-repo",
        "branch": "test-branch",
    }
    repos_with_branches = [
        {
            "name": "test-repo",
            "url": "http://example.com/derp/test-repo",
            "branches": ["test-branch"],
        }
    ]
    form = WorkspaceCreateForm(repos_with_branches, data)

    assert form.is_valid()


@pytest.mark.django_db
def test_workspacecreateform_success_with_upper_case_names():
    data = {
        "name": "TeSt",
        "db": "full",
        "repo": "http://example.com/derp/test-repo",
        "branch": "test-branch",
    }
    repos_with_branches = [
        {
            "name": "test-repo",
            "url": "http://example.com/derp/test-repo",
            "branches": ["test-branch"],
        }
    ]
    form = WorkspaceCreateForm(repos_with_branches, data)

    assert form.is_valid()
    assert form.cleaned_data["name"] == "test"


def test_workspacecreateform_unknown_branch():
    repos_with_branches = [
        {
            "name": "test-repo",
            "url": "http://example.com/derp/test-repo",
            "branches": ["test-branch"],
        }
    ]
    form = WorkspaceCreateForm(repos_with_branches)
    form.cleaned_data = {
        "name": "test",
        "db": "slice",
        "repo": "http://example.com/derp/test-repo",
        "branch": "unknown-branch",
    }

    with pytest.raises(ValidationError) as e:
        form.clean_branch()

    assert e.value.message.startswith("Unknown branch")


def test_workspacecreateform_unknown_repo():
    repos_with_branches = [
        {
            "name": "test-repo",
            "url": "http://example.com/derp/test-repo",
            "branches": ["test-branch"],
        }
    ]
    form = WorkspaceCreateForm(repos_with_branches)
    form.cleaned_data = {
        "name": "test",
        "db": "full",
        "repo": "unknown-repo",
        "branch": "test-branch",
    }

    with pytest.raises(ValidationError) as e:
        form.clean_branch()

    assert e.value.message.startswith("Unknown repo")
