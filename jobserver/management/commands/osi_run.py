import subprocess
import sys
import tempfile

from django.core.management.base import BaseCommand

from interactive.models import AnalysisRequest
from interactive.submit import git


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "analysis_request_slug",
            help="Analysis request slug to link the released file to",
        )

    def handle(self, *args, **options):
        slug = options["analysis_request_slug"]
        analysis_request = AnalysisRequest.objects.filter(slug=slug).first()
        if analysis_request is None:
            self.stderr.write(self.style.ERROR(f"Unknown Analysis: {slug}"))
            sys.exit(1)

        repo = analysis_request.project.interactive_workspace.repo

        if repo.url.startswith("https://github.com"):
            msg = f"This tool only works with local repos, the given repo lives at: {repo.url}"
            self.stderr.write(self.style.ERROR(msg))
            sys.exit(1)

        with tempfile.TemporaryDirectory(suffix=f"repo-{analysis_request.pk}") as path:
            git("clone", repo.url, path)

            cmd = [
                "opensafely",
                "run",
                "run_all",
                "--project-dir",
                path,
                "--timestamps",
            ]

            self.stdout.write(f"Executing: {' '.join(cmd)}")

            subprocess.run(cmd, check=True)
