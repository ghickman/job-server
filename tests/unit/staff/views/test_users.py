import pytest
from django.core.exceptions import BadRequest, PermissionDenied
from django.http import Http404

from jobserver.authorization import (
    InteractiveReporter,
    OutputPublisher,
    ProjectCollaborator,
    ProjectDeveloper,
)
from jobserver.commands import project_members
from jobserver.models import User
from jobserver.utils import set_from_qs
from staff.views.users import (
    UserAuditLog,
    UserClearRoles,
    UserCreate,
    UserDetail,
    UserDetailWithEmail,
    UserDetailWithOAuth,
    UserList,
    UserRoleList,
    UserSetOrgs,
)

from ....factories import (
    BackendFactory,
    BackendMembershipFactory,
    OrgFactory,
    OrgMembershipFactory,
    ProjectFactory,
    UserFactory,
    UserSocialAuthFactory,
    WorkspaceFactory,
)


def test_userauditlog_filter_by_type(rf, core_developer, project_membership):
    actor = UserFactory()
    project = ProjectFactory()
    user = UserFactory()

    project_membership(
        project=project,
        user=user,
        roles=[ProjectCollaborator],
        by=actor,
    )
    project_members.update_roles(
        member=project.memberships.first(),
        by=actor,
        roles=[ProjectCollaborator, ProjectDeveloper],
    )

    request = rf.get("/?types=project_member_added")
    request.user = core_developer

    response = UserAuditLog.as_view()(request, username=user.username)

    assert response.status_code == 200
    assert len(response.context_data["events"]) == 1
    assert response.context_data["events"][0].context["actor"].display_value == str(
        actor
    )


def test_userauditlog_success(rf, core_developer, project_membership):
    actor = UserFactory()
    project = ProjectFactory()
    user = UserFactory()

    project_membership(
        project=project,
        user=user,
        roles=[ProjectCollaborator],
        by=actor,
    )
    project_members.update_roles(
        member=project.memberships.first(),
        by=actor,
        roles=[ProjectCollaborator, ProjectDeveloper],
    )

    # add another member using the user we're testing with as the actor to show
    # we get audit logs for actors in this view as well
    project_membership(
        project=project,
        user=UserFactory(),
        roles=[],
        by=user,
    )

    request = rf.get("/")
    request.user = core_developer

    response = UserAuditLog.as_view()(request, username=user.username)

    assert response.status_code == 200
    assert len(response.context_data["events"]) == 4
    assert response.context_data["user"] == user


def test_userauditlog_unauthorized(rf):
    user = UserFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        UserAuditLog.as_view()(request, username=user.username)


def test_userauditlog_unknown_project(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    with pytest.raises(Http404):
        UserAuditLog.as_view()(request, username="")


@pytest.mark.parametrize("next_url", ["", "/some/other/url/"])
def test_userclearroles_success(rf, core_developer, next_url):
    user = UserFactory()

    suffix = f"?next={next_url}" if next_url else ""
    request = rf.post(f"/{suffix}")
    request.user = core_developer

    response = UserClearRoles.as_view()(request, username=user.username)

    assert response.status_code == 302

    expected = next_url if next_url else user.get_staff_roles_url()
    assert response.url == expected


def test_userclearroles_with_unknown_user(rf, core_developer):
    request = rf.post("/")
    request.user = core_developer

    with pytest.raises(Http404):
        UserClearRoles.as_view()(request, username="")


def test_userclearroles_unauthorized(rf):
    user = UserFactory()

    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        UserClearRoles.as_view()(request, username=user.username)


def test_usercreate_get_success(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    response = UserCreate.as_view()(request)

    assert response.status_code == 200


def test_usercreate_get_success_with_project_slug(rf, core_developer):
    project = ProjectFactory()

    request = rf.get(f"/?project-slug={project.slug}")
    request.user = core_developer

    response = UserCreate.as_view()(request)

    assert response.status_code == 200
    assert response.context_data["form"].initial["project"] == project


def test_usercreate_get_success_with_unknown_args(rf, core_developer):
    request = rf.get("/?project-slug=test")
    request.user = core_developer

    response = UserCreate.as_view()(request)

    assert response.status_code == 200
    assert "org" not in response.context_data["form"].initial
    assert "project" not in response.context_data["form"].initial


def test_usercreate_post_success(rf, core_developer):
    project = ProjectFactory()
    WorkspaceFactory(project=project, name=project.interactive_slug)

    data = {
        "project": project.pk,
        "name": "New Name-Name",
        "email": "test@example.com",
    }
    request = rf.post("/", data)
    request.user = core_developer

    response = UserCreate.as_view()(request)

    assert response.status_code == 302, response.context_data["form"].errors

    assert project.interactive_workspace
    assert project.interactive_workspace.repo

    user = User.objects.get(email="test@example.com")
    assert response.url == user.get_staff_url()
    assert user.created_by == core_developer
    assert user.name == "New Name-Name"
    assert set_from_qs(user.orgs.all()) == set_from_qs(project.orgs.all())
    assert user.projects.first() == project


def test_usercreate_unauthorized(rf):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        UserCreate.as_view()(request)


def test_userdetail_with_email_user_invokes_userdetailwithemail(
    rf, core_developer, project_membership
):
    org = OrgFactory()
    project = ProjectFactory()
    user = UserFactory()

    # link the user to an org and a project
    OrgMembershipFactory(org=org, user=user)
    project_membership(project=project, user=user, roles=[ProjectDeveloper])

    request = rf.get("/")
    request.user = core_developer

    response = UserDetail.as_view()(request, username=user.username)

    assert response.status_code == 200


def test_userdetail_with_oauth_user_invokes_userdetailwithoauth(
    rf, core_developer, project_membership
):
    org = OrgFactory()
    project = ProjectFactory()
    user = UserFactory()
    UserSocialAuthFactory(user=user)

    # link the user to a backend, and project
    BackendMembershipFactory(user=user)
    OrgMembershipFactory(org=org, user=user)
    project_membership(project=project, user=user, roles=[ProjectDeveloper])

    request = rf.get("/")
    request.user = core_developer

    response = UserDetail.as_view()(request, username=user.username)

    assert response.status_code == 200


def test_userdetail_with_unknown_user(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    with pytest.raises(Http404):
        UserDetail.as_view()(request, username="test")


def test_userdetail_without_core_dev_role(rf):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        UserDetail.as_view()(request, username="test")


def test_userdetailwithemail_get_success(rf, core_developer, project_membership):
    user = UserFactory()

    # add a couple of memberships so the orgs and projects comprehensions in
    # get_context_data fire
    OrgMembershipFactory(user=user)
    project_membership(user=user)

    request = rf.get("/")
    request.user = core_developer

    response = UserDetailWithEmail.as_view()(request, username=user.username)

    assert response.status_code == 200


def test_userdetailwithemail_post_success(rf, core_developer):
    user = UserFactory(fullname="testing", email="test@example.com")

    data = {
        "fullname": "Mr Testerson",
        "email": "testing@example.com",
    }
    request = rf.post("/", data=data)
    request.user = core_developer

    response = UserDetailWithEmail.as_view()(request, username=user.username)

    assert response.status_code == 302
    assert response.url == user.get_staff_url()

    user.refresh_from_db()
    assert user.fullname == "Mr Testerson"
    assert user.email == "testing@example.com"


def test_userdetailwithemail_with_oauth_user_invokes_userdetailwithoauth(
    rf, core_developer, project_membership
):
    org = OrgFactory()
    project = ProjectFactory()
    user = UserFactory()
    UserSocialAuthFactory(user=user)

    # link the user to some a backend, and project
    BackendMembershipFactory(user=user)
    OrgMembershipFactory(org=org, user=user)
    project_membership(project=project, user=user, roles=[ProjectDeveloper])

    request = rf.get("/")
    request.user = core_developer

    response = UserDetailWithEmail.as_view()(request, username=user.username)

    assert response.status_code == 200


def test_userdetailwithemail_with_unknown_user(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    with pytest.raises(Http404):
        UserDetailWithEmail.as_view()(request, username="test")


def test_userdetailwithemail_without_core_dev_role(rf, core_developer):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        UserDetailWithEmail.as_view()(request, username="test")


def test_userdetailwithoauth_get_success(rf, core_developer, project_membership):
    org = OrgFactory()
    project1 = ProjectFactory()
    project2 = ProjectFactory()
    user = UserFactory(roles=[OutputPublisher, ProjectDeveloper])
    UserSocialAuthFactory(user=user)

    # link the user to some Backends
    BackendMembershipFactory(user=user)
    BackendMembershipFactory(user=user)

    # link the user to the Org
    OrgMembershipFactory(org=org, user=user)

    # link the user to the Projects
    project_membership(project=project1, user=user)
    project_membership(project=project2, user=user)

    request = rf.get("/")
    request.user = core_developer

    response = UserDetailWithOAuth.as_view()(request, username=user.username)

    assert response.status_code == 200
    assert response.context_data["user"] == user


def test_userdetailwithoauth_post_success(rf, core_developer, project_membership):
    backend = BackendFactory()

    project1 = ProjectFactory()
    project2 = ProjectFactory()
    user = UserFactory(roles=[OutputPublisher, ProjectDeveloper])
    UserSocialAuthFactory(user=user)

    # link the user to some Backends
    BackendMembershipFactory(user=user)
    BackendMembershipFactory(user=user)

    # link the user to the Projects
    project_membership(project=project1, user=user)
    project_membership(project=project2, user=user)

    request = rf.post("/", {"backends": [backend.slug]})
    request.user = core_developer

    response = UserDetailWithOAuth.as_view()(request, username=user.username)

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == user.get_staff_url()

    user.refresh_from_db()
    assert set_from_qs(user.backends.all()) == {backend.pk}


def test_userdetailwithoauth_post_with_unknown_backend(
    rf, core_developer, project_membership
):
    project1 = ProjectFactory()
    project2 = ProjectFactory()
    user = UserFactory(roles=[OutputPublisher, ProjectDeveloper])
    UserSocialAuthFactory(user=user)

    # link the user to some Backends
    BackendMembershipFactory(user=user)
    BackendMembershipFactory(user=user)

    # link the user to the Projects
    project_membership(project=project1, user=user)
    project_membership(project=project2, user=user)

    request = rf.post("/", {"backends": ["not-a-real-backend"]})
    request.user = core_developer

    response = UserDetailWithOAuth.as_view()(request, username=user.username)

    assert response.status_code == 200, response.url

    # check we get an error from the form, and thus are passing in the
    # submitted data correctly
    expected = {
        "backends": [
            "Select a valid choice. not-a-real-backend is not one of the available choices."
        ]
    }
    assert response.context_data["form"].errors == expected

    # check we're rendering the appropriate error in the template
    assert (
        "not-a-real-backend is not one of the available choices."
        in response.rendered_content
    )


def test_userdetailwithoauth_with_email_only_user_invokes_userdetailwithemail(
    rf, core_developer, project_membership
):
    org = OrgFactory()
    project = ProjectFactory()
    user = UserFactory()

    # link the user to the Org&Project
    OrgMembershipFactory(org=org, user=user)
    project_membership(project=project, user=user, roles=[InteractiveReporter])

    request = rf.get("/")
    request.user = core_developer

    response = UserDetailWithOAuth.as_view()(request, username=user.username)

    assert response.status_code == 200


def test_userdetailwithoauth_with_unknown_user(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    with pytest.raises(Http404):
        UserDetailWithOAuth.as_view()(request, username="test")


def test_userdetailwithoauth_without_core_dev_role(rf):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        UserDetailWithOAuth.as_view()(request, username="test")


def test_userlist_filter_by_backend(rf, core_developer):
    backend = BackendFactory()

    BackendMembershipFactory(user=UserFactory(), backend=backend)
    BackendMembershipFactory(user=UserFactory())

    request = rf.get(f"/?backend={backend.pk}")
    request.user = core_developer

    response = UserList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


def test_userlist_filter_by_invalid_backend(rf, core_developer):
    request = rf.get("/?backend=test")
    request.user = core_developer

    with pytest.raises(BadRequest):
        UserList.as_view()(request)


def test_userlist_filter_by_invalid_missing(rf, core_developer):
    request = rf.get("/?missing=test")
    request.user = core_developer

    response = UserList.as_view()(request)

    assert list(response.context_data["object_list"]) == [core_developer]


def test_userlist_filter_by_missing(rf, core_developer):
    backend = BackendFactory()
    UserSocialAuthFactory(user=core_developer)
    social = UserSocialAuthFactory()

    BackendMembershipFactory(
        user=UserFactory(),
        created_by=core_developer,
        backend=backend,
    )

    request = rf.get("/?missing=backend")
    request.user = core_developer

    response = UserList.as_view()(request)

    assert list(response.context_data["object_list"]) == [core_developer, social.user]


def test_userlist_filter_by_org(rf, core_developer):
    org1 = OrgFactory()
    org2 = OrgFactory()

    OrgMembershipFactory(user=UserFactory(), org=org1)
    OrgMembershipFactory(user=UserFactory(), org=org2)

    request = rf.get(f"/?org={org1.slug}")
    request.user = core_developer

    response = UserList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


def test_userlist_filter_by_invalid_org(rf, core_developer):
    request = rf.get("/?org=test")
    request.user = core_developer

    response = UserList.as_view()(request)

    assert len(response.context_data["object_list"]) == 0


def test_userlist_filter_by_role(rf, core_developer):
    UserFactory(roles=[OutputPublisher])
    UserFactory(roles=[ProjectDeveloper])

    request = rf.get("/?role=OutputPublisher")
    request.user = core_developer

    response = UserList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


def test_userlist_filter_by_invalid_role(rf, core_developer):
    request = rf.get("/?role=unknown")
    request.user = core_developer

    with pytest.raises(Exception, match="^Unknown Roles:"):
        UserList.as_view()(request)


def test_userlist_filter_by_any_roles_yes_includes_global_roles(rf, core_developer):
    user = UserFactory(roles=[OutputPublisher])
    UserFactory()

    request = rf.get("/?any_roles=yes")
    request.user = core_developer

    response = UserList.as_view()(request)

    assert set_from_qs(response.context_data["object_list"]) == {
        core_developer.pk,
        user.pk,
    }


def test_userlist_filter_by_any_roles_yes_includes_project(
    rf, core_developer, project_membership
):
    UserFactory()

    user_with_project = UserFactory()
    project_membership(user=user_with_project, roles=[ProjectDeveloper])

    request = rf.get("/?any_roles=yes")
    request.user = core_developer

    response = UserList.as_view()(request)

    assert set_from_qs(response.context_data["object_list"]) == {
        core_developer.pk,
        user_with_project.pk,
    }


def test_userlist_filter_by_any_roles_yes_includes_org(
    rf, core_developer, project_membership
):
    UserFactory()

    user_with_project = UserFactory()
    project_membership(user=user_with_project, roles=[ProjectDeveloper])

    user_with_org = UserFactory()
    OrgMembershipFactory(user=user_with_org, roles=[ProjectDeveloper])

    request = rf.get("/?any_roles=yes")
    request.user = core_developer

    response = UserList.as_view()(request)

    assert set_from_qs(response.context_data["object_list"]) == {
        core_developer.pk,
        user_with_org.pk,
        user_with_project.pk,
    }


def test_userlist_filter_by_any_roles_no_excludes_global_roles(rf, core_developer):
    UserFactory(roles=[OutputPublisher])
    UserFactory(roles=[ProjectDeveloper])
    user = UserFactory()

    request = rf.get("/?any_roles=no")
    request.user = core_developer

    response = UserList.as_view()(request)

    assert set_from_qs(response.context_data["object_list"]) == {user.pk}


def test_userlist_filter_by_any_roles_no_excludes_project_roles(
    rf, core_developer, project_membership
):
    user = UserFactory()

    actor = UserFactory(roles=[ProjectDeveloper])

    # set up projects so the creator can have roles
    project1 = ProjectFactory(created_by=actor, updated_by=actor)
    project2 = ProjectFactory(created_by=actor, updated_by=actor)

    user_with_project = UserFactory()
    project_membership(
        project=project1,
        user=user_with_project,
        roles=[ProjectDeveloper],
        by=actor,
    )

    user_with_project_and_no_roles = UserFactory()
    project_membership(project=project1, user=user_with_project_and_no_roles, by=actor)

    user_with_mixture_of_project_roles = UserFactory()
    project_membership(
        project=project1, user=user_with_mixture_of_project_roles, by=actor
    )
    project_membership(
        project=project2,
        user=user_with_mixture_of_project_roles,
        roles=[ProjectDeveloper],
        by=actor,
    )

    request = rf.get("/?any_roles=no")
    request.user = core_developer

    response = UserList.as_view()(request)

    assert set_from_qs(response.context_data["object_list"]) == {
        user.pk,
        user_with_project_and_no_roles.pk,
    }


def test_userlist_filter_by_any_roles_no_excludes_org_roles(rf, core_developer):
    UserFactory(roles=[OutputPublisher])
    UserFactory(roles=[ProjectDeveloper])
    user = UserFactory()

    user_with_project = UserFactory()
    OrgMembershipFactory(user=user_with_project, roles=[ProjectDeveloper])

    user_with_org_and_no_roles = UserFactory()
    OrgMembershipFactory(user=user_with_org_and_no_roles)

    user_with_mixture_of_org_roles = UserFactory()
    OrgMembershipFactory(user=user_with_mixture_of_org_roles)
    OrgMembershipFactory(user=user_with_mixture_of_org_roles, roles=[ProjectDeveloper])

    request = rf.get("/?any_roles=no")
    request.user = core_developer

    response = UserList.as_view()(request)

    assert set_from_qs(response.context_data["object_list"]) == {
        user.pk,
        user_with_org_and_no_roles.pk,
    }


def test_userlist_filter_by_any_roles_invalid_does_nothing(rf, core_developer):
    UserFactory(roles=[OutputPublisher])
    UserFactory(roles=[])

    request = rf.get("/?any_roles=asdf")
    request.user = core_developer

    response = UserList.as_view()(request)

    assert len(response.context_data["object_list"]) == 3


def test_userlist_find_by_username(rf, core_developer):
    UserFactory(username="ben")
    UserFactory(fullname="ben g")
    UserFactory(username="seb")

    request = rf.get("/?q=ben")
    request.user = core_developer

    response = UserList.as_view()(request)

    assert response.status_code == 200

    assert len(response.context_data["object_list"]) == 2


def test_userlist_success(rf, core_developer):
    UserFactory.create_batch(5)

    request = rf.get("/")
    request.user = core_developer

    response = UserList.as_view()(request)

    assert response.status_code == 200

    # the core_developer fixture creates a User object as well as the 5 we
    # created in the batch call above
    assert len(response.context_data["object_list"]) == 6


def test_userrolelist_get_success(rf, core_developer):
    user = UserFactory()

    request = rf.get("/")
    request.user = core_developer

    response = UserRoleList.as_view()(request, username=user.username)

    assert response.status_code == 200


def test_userrolelist_post_success(rf, core_developer):
    user = UserFactory(roles=[ProjectDeveloper])

    data = {
        "roles": [
            "jobserver.authorization.roles.OutputPublisher",
            "jobserver.authorization.roles.ProjectDeveloper",
        ]
    }
    request = rf.post("/", data=data)
    request.user = core_developer

    response = UserRoleList.as_view()(request, username=user.username)

    assert response.status_code == 302, response.context_data["form"].errors

    user.refresh_from_db()
    assert set(user.roles) == {OutputPublisher, ProjectDeveloper}


def test_userrolelist_post_with_unknown_role(rf, core_developer):
    user = UserFactory()

    request = rf.post("/", {"roles": ["not-a-real-role"]})
    request.user = core_developer

    response = UserRoleList.as_view()(request, username=user.username)

    assert response.status_code == 200

    # check we get an error from the form, and thus are passing in the
    # submitted data correctly
    expected = {
        "roles": [
            "Select a valid choice. not-a-real-role is not one of the available choices."
        ]
    }
    assert response.context_data["form"].errors == expected

    # check we're rendering the appropriate error in the template
    assert (
        "not-a-real-role is not one of the available choices."
        in response.rendered_content
    )


def test_userrolelist_with_unknown_user(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    with pytest.raises(Http404):
        UserRoleList.as_view()(request, username="")


def test_userrolelist_without_core_dev_role(rf):
    user = UserFactory()

    request = rf.get("/")
    request.user = user

    with pytest.raises(PermissionDenied):
        UserRoleList.as_view()(request, username=user.username)


def test_usersetorgs_get_success(rf, core_developer):
    org1 = OrgFactory()
    org2 = OrgFactory()
    user = UserFactory()

    OrgMembershipFactory(org=org1, user=user)
    OrgMembershipFactory(org=org2, user=user)

    request = rf.get("/")
    request.user = core_developer

    response = UserSetOrgs.as_view()(request, username=user.username)

    assert response.status_code == 200
    assert response.context_data["user"] == user


def test_usersetorgs_post_success(rf, core_developer):
    existing_org = OrgFactory()
    new_org1 = OrgFactory()
    new_org2 = OrgFactory()

    user = UserFactory()

    OrgMembershipFactory(org=existing_org, user=user)

    request = rf.post("/", {"orgs": [new_org1.pk, new_org2.pk]})
    request.user = core_developer

    response = UserSetOrgs.as_view()(request, username=user.username)

    assert response.status_code == 302
    assert response.url == user.get_staff_url()

    user.refresh_from_db()
    assert set_from_qs(user.orgs.all()) == {new_org1.pk, new_org2.pk}


def test_usersetorgs_unknown_user(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer
    with pytest.raises(Http404):
        UserSetOrgs.as_view()(request, username="")
