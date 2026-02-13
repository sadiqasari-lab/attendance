"""Health check endpoints for container orchestration and monitoring."""
from django.db import connection
from django.http import JsonResponse


def healthz(request):
    """Liveness probe — returns 200 if the application process is running."""
    return JsonResponse({"status": "ok"})


def readyz(request):
    """Readiness probe — returns 200 only when all dependencies are reachable."""
    checks = {}

    # Database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = str(exc)

    # Redis / Celery broker
    try:
        from django_redis import get_redis_connection

        redis_conn = get_redis_connection("default")
        redis_conn.ping()
        checks["redis"] = "ok"
    except Exception:
        # Fallback: try direct Redis check via Celery broker URL
        try:
            import redis
            from django.conf import settings

            r = redis.from_url(settings.CELERY_BROKER_URL)
            r.ping()
            checks["redis"] = "ok"
        except Exception as exc:
            checks["redis"] = str(exc)

    all_ok = all(v == "ok" for v in checks.values())
    status_code = 200 if all_ok else 503
    return JsonResponse({"status": "ok" if all_ok else "degraded", "checks": checks}, status=status_code)
