from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, ListView

from .forms import JobCreateForm, WorkspaceCreateForm
from .models import Job, Workspace


@method_decorator(login_required, name="dispatch")
class JobCreate(CreateView):
    form_class = JobCreateForm
    model = Job
    template_name = "job_create.html"

    def get_success_url(self):
        return self.object.get_absolute_url()


class JobDetail(DetailView):
    model = Job
    queryset = Job.objects.select_related("workspace")
    template_name = "job_detail.html"


class JobList(ListView):
    model = Job
    ordering = "-pk"
    paginate_by = 25
    template_name = "job_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = ["completed", "in-progress", "pending"]
        context["workspaces"] = Workspace.objects.all()
        return context

    def get_queryset(self):
        qs = super().get_queryset().select_related("workspace")

        q = self.request.GET.get("q")
        if q:
            try:
                q = int(q)
            except ValueError:
                qs = qs.filter(action_id__icontains=q)
            else:
                # if the query looks enough like a number for int() to handle
                # it then we can look for a job number
                qs = qs.filter(Q(action_id__icontains=q) | Q(pk=q))

        status = self.request.GET.get("status")
        if status:
            status_lut = {
                "completed": qs.completed,
                "in-progress": qs.in_progress,
                "pending": qs.pending,
            }
            qs = status_lut[status]()

        workspace = self.request.GET.get("workspace")
        if workspace:
            qs = qs.filter(workspace_id=workspace)

        return qs


@method_decorator(login_required, name="dispatch")
class WorkspaceCreate(CreateView):
    form_class = WorkspaceCreateForm
    model = Workspace
    template_name = "workspace_create.html"

    def get_success_url(self):
        return self.object.get_absolute_url()


class WorkspaceDetail(DetailView):
    model = Workspace
    template_name = "workspace_detail.html"


class WorkspaceList(ListView):
    ordering = "name"
    paginate_by = 25
    queryset = Workspace.objects.prefetch_related("jobs")
    template_name = "workspace_list.html"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        # if there are no workspaces redirect the user to the new Workspace
        # page immediately
        if request.user.is_authenticated and not self.object_list:
            return redirect("workspace-create")

        return response
