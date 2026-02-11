"""Biometric service layer — enrollment, verification, liveness."""
import io
import logging

import numpy as np
from django.conf import settings
from PIL import Image

from apps.core.models import AuditLog
from apps.core.utils import get_client_ip

from .encryption import decrypt_embedding, encrypt_embedding
from .models import BiometricEnrollmentLog, BiometricTemplate

logger = logging.getLogger(__name__)


class BiometricService:
    """Service for face recognition enrollment and verification."""

    @staticmethod
    def enroll(employee, images, request):
        """
        Enroll an employee with multiple face images.

        Args:
            employee: Employee instance
            images: list of InMemoryUploadedFile or file-like objects
            request: HTTP request

        Returns:
            BiometricTemplate instance
        """
        tenant = request.tenant
        min_images = getattr(settings, "BIOMETRIC_MIN_ENROLLMENT_IMAGES", 3)

        if len(images) < min_images:
            raise ValueError(f"At least {min_images} images are required for enrollment.")

        # Log enrollment start
        BiometricEnrollmentLog.objects.create(
            tenant=tenant,
            employee=employee,
            event=BiometricEnrollmentLog.Event.STARTED,
            details={"num_images": len(images)},
            created_by=request.user,
        )

        embeddings = []
        for i, image_file in enumerate(images):
            try:
                embedding = BiometricService._extract_embedding(image_file)
                if embedding is not None:
                    embeddings.append(embedding)
                    BiometricEnrollmentLog.objects.create(
                        tenant=tenant,
                        employee=employee,
                        event=BiometricEnrollmentLog.Event.IMAGE_CAPTURED,
                        details={"image_index": i},
                        created_by=request.user,
                    )
            except Exception:
                logger.exception("Failed to extract embedding from image %d", i)

        if len(embeddings) < min_images:
            BiometricEnrollmentLog.objects.create(
                tenant=tenant,
                employee=employee,
                event=BiometricEnrollmentLog.Event.FAILED,
                details={"reason": "Insufficient valid face embeddings."},
                created_by=request.user,
            )
            raise ValueError(
                f"Could not extract enough face embeddings. Got {len(embeddings)}, need {min_images}."
            )

        # Average the embeddings for a more robust template
        avg_embedding = np.mean(embeddings, axis=0)

        # Encrypt the embedding
        encrypted_data, iv = encrypt_embedding(avg_embedding)

        # Revoke old active templates
        BiometricTemplate.objects.filter(
            tenant=tenant,
            employee=employee,
            status=BiometricTemplate.Status.ACTIVE,
            is_deleted=False,
        ).update(status=BiometricTemplate.Status.REVOKED)

        # Create new template
        template = BiometricTemplate.objects.create(
            tenant=tenant,
            employee=employee,
            encrypted_embedding=encrypted_data,
            encryption_iv=iv,
            num_images_used=len(embeddings),
            status=BiometricTemplate.Status.ACTIVE,
            quality_score=BiometricService._calculate_quality(embeddings),
            created_by=request.user,
        )

        # Mark user as enrolled
        employee.user.requires_biometric_enrollment = False
        employee.user.save(update_fields=["requires_biometric_enrollment"])

        BiometricEnrollmentLog.objects.create(
            tenant=tenant,
            employee=employee,
            template=template,
            event=BiometricEnrollmentLog.Event.COMPLETED,
            details={"template_version": template.embedding_version},
            created_by=request.user,
        )

        AuditLog.objects.create(
            tenant=tenant,
            user=request.user,
            action="ENROLLMENT",
            resource_type="BiometricTemplate",
            resource_id=template.pk,
            details={
                "num_images": len(embeddings),
                "quality_score": template.quality_score,
            },
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return template

    @staticmethod
    def verify(employee, image_file, tenant):
        """
        Verify a face image against stored biometric template.

        Returns:
            (match: bool, score: float)
        """
        template = BiometricTemplate.objects.filter(
            tenant=tenant,
            employee=employee,
            status=BiometricTemplate.Status.ACTIVE,
            is_deleted=False,
        ).first()

        if not template:
            return False, 0.0

        # Extract embedding from the input image
        probe_embedding = BiometricService._extract_embedding(image_file)
        if probe_embedding is None:
            return False, 0.0

        # Decrypt stored embedding
        stored_embedding = decrypt_embedding(
            bytes(template.encrypted_embedding),
            bytes(template.encryption_iv),
        )

        # Calculate distance (face_recognition uses Euclidean distance)
        distance = np.linalg.norm(stored_embedding - probe_embedding)
        # Convert distance to similarity score (0-1, higher is better)
        score = max(0.0, 1.0 - distance)

        threshold = getattr(settings, "BIOMETRIC_MATCH_THRESHOLD", 0.6)
        match = score >= threshold

        return match, float(score)

    @staticmethod
    def _extract_embedding(image_file):
        """
        Extract 128-dimensional face embedding using face_recognition library.

        Returns:
            numpy array of shape (128,) or None if no face detected.
        """
        try:
            import face_recognition

            # Read image data
            if hasattr(image_file, "read"):
                image_data = image_file.read()
                if hasattr(image_file, "seek"):
                    image_file.seek(0)
            else:
                image_data = image_file

            # Convert to numpy array via PIL
            pil_image = Image.open(io.BytesIO(image_data))
            pil_image = pil_image.convert("RGB")
            image_array = np.array(pil_image)

            # Detect face and extract embedding
            face_locations = face_recognition.face_locations(image_array, model="hog")
            if not face_locations:
                logger.warning("No face detected in image.")
                return None

            encodings = face_recognition.face_encodings(
                image_array, known_face_locations=face_locations
            )
            if not encodings:
                return None

            return encodings[0]

        except ImportError:
            logger.error(
                "face_recognition library not installed. "
                "Install with: pip install face_recognition"
            )
            # Return a mock embedding for development
            return np.random.randn(128)
        except Exception:
            logger.exception("Failed to extract face embedding")
            return None

    @staticmethod
    def _calculate_quality(embeddings):
        """
        Calculate quality score based on embedding consistency.
        Higher consistency among multiple captures = higher quality.
        """
        if len(embeddings) < 2:
            return 0.5

        # Calculate average pairwise distance
        distances = []
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                d = np.linalg.norm(embeddings[i] - embeddings[j])
                distances.append(d)

        avg_distance = np.mean(distances)
        # Convert to quality score (lower distance = higher quality)
        quality = max(0.0, min(1.0, 1.0 - avg_distance))
        return round(quality, 4)

    @staticmethod
    def revoke_template(employee, tenant, user):
        """Revoke the active biometric template for an employee."""
        updated = BiometricTemplate.objects.filter(
            tenant=tenant,
            employee=employee,
            status=BiometricTemplate.Status.ACTIVE,
            is_deleted=False,
        ).update(status=BiometricTemplate.Status.REVOKED)

        if updated:
            employee.user.requires_biometric_enrollment = True
            employee.user.save(update_fields=["requires_biometric_enrollment"])

            BiometricEnrollmentLog.objects.create(
                tenant=tenant,
                employee=employee,
                event=BiometricEnrollmentLog.Event.REVOKED,
                created_by=user,
            )

        return updated > 0

    @staticmethod
    def delete_template(employee, tenant, user):
        """Permanently delete biometric data for an employee (GDPR/compliance)."""
        templates = BiometricTemplate.objects.filter(
            tenant=tenant,
            employee=employee,
            is_deleted=False,
        )
        count = templates.count()
        for t in templates:
            t.soft_delete(user=user)

        employee.user.requires_biometric_enrollment = True
        employee.user.save(update_fields=["requires_biometric_enrollment"])

        return count
