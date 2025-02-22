import pytest

from jobserver.authorization import ProjectCollaborator, ProjectDeveloper
from jobserver.management.commands.merge_projects import MergeException, merge_projects
from jobserver.models import Project
from jobserver.utils import set_from_qs
from tests.factories import OrgFactory, ProjectFactory, UserFactory


def test_merge_projects_success(project_membership):
    both = [ProjectDeveloper, ProjectCollaborator]

    operator = UserFactory()

    org1 = OrgFactory()
    org2 = OrgFactory()

    user1 = UserFactory()
    user2 = UserFactory()
    user3 = UserFactory()
    user4 = UserFactory()
    user5 = UserFactory()

    primary = ProjectFactory(orgs=[org1])
    project_membership(user=user1, project=primary, roles=[ProjectDeveloper])
    project_membership(user=user4, project=primary, roles=[ProjectDeveloper])

    project1 = ProjectFactory(orgs=[org1])
    project_membership(project=project1, user=user1, roles=both)
    project_membership(project=project1, user=user2, roles=both)

    project2 = ProjectFactory(orgs=[org2])
    project_membership(project=project2, user=user2, roles=both)
    project_membership(project=project2, user=user3, roles=both)

    project3 = ProjectFactory(orgs=[org1])
    project_membership(project=project3, user=user4, roles=both)
    project_membership(project=project3, user=user5, roles=both)

    merge_projects(
        operator.username, primary.slug, [project1.slug, project2.slug, project3.slug]
    )

    # check the projects have been deleted
    assert not Project.objects.filter(
        slug__in=[project1.slug, project2.slug, project2.slug]
    )

    assert set_from_qs(primary.members.all()) == {
        user1.pk,
        user2.pk,
        user3.pk,
        user4.pk,
        user5.pk,
    }
    assert set(primary.memberships.get(user__pk=user1.pk).roles) == {ProjectDeveloper}
    assert set(primary.memberships.get(user__pk=user2.pk).roles) == set(both)
    assert set(primary.memberships.get(user__pk=user3.pk).roles) == set(both)
    assert set(primary.memberships.get(user__pk=user4.pk).roles) == {ProjectDeveloper}
    assert set(primary.memberships.get(user__pk=user5.pk).roles) == set(both)
    assert set_from_qs(primary.orgs.all()) == set([org1.pk, org2.pk])

    assert primary.redirects.count() == 3


def test_merge_projects_unknown_other_projects():
    primary = ProjectFactory()
    user = UserFactory()

    project = ProjectFactory()

    msg = "Unknown projects: unknown-project"
    with pytest.raises(MergeException, match=msg):
        merge_projects(user.username, primary.slug, [project.slug, "unknown-project"])


def test_merge_projects_unknown_primary_projects():
    user = UserFactory()

    project1 = ProjectFactory()
    project2 = ProjectFactory()

    msg = "Primary project does not exist"
    with pytest.raises(MergeException, match=msg):
        merge_projects(user.username, "unknown-slug", [project1.slug, project2.slug])


def test_merge_projects_unknown_user():
    primary = ProjectFactory()
    project = ProjectFactory()
    with pytest.raises(MergeException, match="User does not exist"):
        merge_projects("unknown", primary.slug, [project.slug])
