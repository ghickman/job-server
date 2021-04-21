from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, TemplateView, View

from ..authorization import has_permission
from ..authorization.decorators import require_superuser
from ..forms import ProjectCreateForm, ResearcherFormSet
from ..models import Org, Project, ProjectMembership


@method_decorator(require_superuser, name="dispatch")
class ProjectCreate(CreateView):
    form_class = ProjectCreateForm
    model = Project
    template_name = "project_create.html"

    def dispatch(self, request, *args, **kwargs):
        self.org = get_object_or_404(Org, slug=self.kwargs["org_slug"])

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.object = None
        researcher_formset = ResearcherFormSet(prefix="researcher")
        return self.render_to_response(
            self.get_context_data(researcher_formset=researcher_formset)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["org"] = self.org
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        self.object = None

        form = self.get_form()
        researcher_formset = ResearcherFormSet(request.POST, prefix="researcher")

        form_valid = form.is_valid()
        formset_valid = researcher_formset.is_valid()
        if not (form_valid and formset_valid):
            return self.render_to_response(
                self.get_context_data(researcher_formset=researcher_formset)
            )

        project = form.save(commit=False)
        project.org = self.org
        project.save()

        researchers = researcher_formset.save()
        project.researcher_registrations.add(*researchers)

        return redirect(project)


@method_decorator(require_superuser, name="dispatch")
class ProjectDetail(DetailView):
    template_name = "project_detail.html"

    def get_object(self):
        return get_object_or_404(
            Project,
            slug=self.kwargs["project_slug"],
            org__slug=self.kwargs["org_slug"],
        )

    def get_context_data(self, **kwargs):
        can_manage_members = has_permission(
            self.request.user,
            "manage_project_members",
            project=self.object,
        )

        context = super().get_context_data(**kwargs)
        context["can_manage_members"] = can_manage_members
        context["workspaces"] = self.object.workspaces.order_by("name")
        return context


@method_decorator(require_superuser, name="dispatch")
class ProjectDisconnectWorkspace(View):
    def post(self, request, *args, **kwargs):
        """A transitional view to help with migrating Workspaces under Projects"""
        project = get_object_or_404(
            Project,
            org__slug=self.kwargs["org_slug"],
            slug=self.kwargs["project_slug"],
        )

        workspace_id = request.POST.get("id")
        if not workspace_id:
            return redirect(project)

        project.workspaces.filter(pk=workspace_id).update(project=None)

        return redirect(project)


@method_decorator(require_superuser, name="dispatch")
class ProjectRemoveMember(View):
    model = ProjectMembership

    def post(self, request, *args, **kwargs):
        try:
            membership = ProjectMembership.objects.select_related("project").get(
                project__org__slug=self.kwargs["org_slug"],
                project__slug=self.kwargs["project_slug"],
                user__username=self.request.POST.get("username"),
            )
        except ProjectMembership.DoesNotExist:
            raise Http404

        can_manage_members = has_permission(
            self.request.user,
            "manage_project_members",
            project=membership.project,
        )
        if can_manage_members:
            membership.delete()
        else:
            messages.error(
                request, "You do not have permission to remove Project members."
            )

        return redirect(membership.project.get_settings_url())


@method_decorator(require_superuser, name="dispatch")
class ProjectSettings(TemplateView):
    template_name = "project_settings.html"

    def get_context_data(self, **kwargs):
        project = get_object_or_404(
            Project,
            org__slug=self.kwargs["org_slug"],
            slug=self.kwargs["project_slug"],
        )

        can_manage_members = has_permission(
            self.request.user,
            "manage_project_members",
            project=project,
        )
        members = project.members.select_related("user")

        context = super().get_context_data(**kwargs)
        context["can_manage_members"] = can_manage_members
        context["members"] = members
        context["project"] = project
        return context
