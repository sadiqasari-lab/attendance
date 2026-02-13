"""Backup and restore views for the attendance system."""
import gzip
import io
import json
import os
import time
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.http import HttpResponse
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsSuperAdmin

BACKUP_DIR = Path(settings.BASE_DIR) / "backups"


def _ensure_backup_dir():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


class BackupListView(APIView):
    """List available backups."""

    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        _ensure_backup_dir()
        backups = []
        for f in sorted(BACKUP_DIR.glob("*.json.gz"), reverse=True):
            stat = f.stat()
            backups.append(
                {
                    "filename": f.name,
                    "size_bytes": stat.st_size,
                    "size_display": _human_size(stat.st_size),
                    "created_at": time.strftime(
                        "%Y-%m-%dT%H:%M:%S", time.localtime(stat.st_mtime)
                    ),
                }
            )
        return Response({"success": True, "data": backups})


class BackupCreateView(APIView):
    """Create a new database backup (gzipped JSON fixture)."""

    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        _ensure_backup_dir()
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{timestamp}.json.gz"
        filepath = BACKUP_DIR / filename

        buf = io.StringIO()
        try:
            call_command(
                "dumpdata",
                "--natural-foreign",
                "--natural-primary",
                "--exclude=contenttypes",
                "--exclude=auth.permission",
                "--exclude=admin.logentry",
                "--exclude=sessions.session",
                "--indent=2",
                stdout=buf,
            )
        except Exception as e:
            return Response(
                {"success": False, "error": {"detail": f"Backup failed: {e}"}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        data = buf.getvalue()
        with gzip.open(filepath, "wt", encoding="utf-8") as f:
            f.write(data)

        stat = filepath.stat()
        return Response(
            {
                "success": True,
                "data": {
                    "filename": filename,
                    "size_bytes": stat.st_size,
                    "size_display": _human_size(stat.st_size),
                    "created_at": time.strftime(
                        "%Y-%m-%dT%H:%M:%S", time.localtime(stat.st_mtime)
                    ),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class BackupDownloadView(APIView):
    """Download a specific backup file."""

    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request, filename):
        filepath = BACKUP_DIR / filename
        # Prevent path traversal
        if not filepath.resolve().is_relative_to(BACKUP_DIR.resolve()):
            return Response(
                {"success": False, "error": {"detail": "Invalid filename."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not filepath.exists():
            return Response(
                {"success": False, "error": {"detail": "Backup not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        with open(filepath, "rb") as f:
            content = f.read()
        response = HttpResponse(content, content_type="application/gzip")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class BackupDeleteView(APIView):
    """Delete a specific backup file."""

    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def delete(self, request, filename):
        filepath = BACKUP_DIR / filename
        if not filepath.resolve().is_relative_to(BACKUP_DIR.resolve()):
            return Response(
                {"success": False, "error": {"detail": "Invalid filename."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not filepath.exists():
            return Response(
                {"success": False, "error": {"detail": "Backup not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        filepath.unlink()
        return Response({"success": True, "data": {"detail": "Backup deleted."}})


class BackupRestoreView(APIView):
    """Restore the database from an uploaded backup file."""

    permission_classes = [IsAuthenticated, IsSuperAdmin]
    parser_classes = [MultiPartParser]

    def post(self, request):
        uploaded = request.FILES.get("file")
        filename = request.data.get("filename")

        if uploaded:
            # Restore from uploaded file
            try:
                raw = uploaded.read()
                try:
                    content = gzip.decompress(raw).decode("utf-8")
                except gzip.BadGzipFile:
                    content = raw.decode("utf-8")
                # Validate JSON
                json.loads(content)
            except (json.JSONDecodeError, UnicodeDecodeError):
                return Response(
                    {"success": False, "error": {"detail": "Invalid backup file format."}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif filename:
            # Restore from existing backup on server
            filepath = BACKUP_DIR / filename
            if not filepath.resolve().is_relative_to(BACKUP_DIR.resolve()):
                return Response(
                    {"success": False, "error": {"detail": "Invalid filename."}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not filepath.exists():
                return Response(
                    {"success": False, "error": {"detail": "Backup not found."}},
                    status=status.HTTP_404_NOT_FOUND,
                )
            with gzip.open(filepath, "rt", encoding="utf-8") as f:
                content = f.read()
        else:
            return Response(
                {"success": False, "error": {"detail": "No file or filename provided."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Write to temp file and load
        _ensure_backup_dir()
        tmp_path = BACKUP_DIR / "_restore_tmp.json"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(content)
            call_command("loaddata", str(tmp_path), verbosity=0)
        except Exception as e:
            return Response(
                {"success": False, "error": {"detail": f"Restore failed: {e}"}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

        return Response(
            {"success": True, "data": {"detail": "Database restored successfully."}},
        )


def _human_size(size_bytes):
    """Convert bytes to human-readable size."""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
