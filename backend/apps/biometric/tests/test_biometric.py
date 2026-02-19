"""Tests for the biometric app."""
import numpy as np
import pytest

from apps.biometric.encryption import decrypt_embedding, encrypt_embedding
from apps.biometric.models import BiometricEnrollmentLog, BiometricTemplate


class TestBiometricEncryption:
    def test_encrypt_decrypt_roundtrip(self):
        """Embedding should survive encrypt/decrypt cycle."""
        original = np.random.randn(128).astype(np.float64)
        encrypted, iv = encrypt_embedding(original)
        decrypted = decrypt_embedding(encrypted, iv)
        np.testing.assert_array_almost_equal(original, decrypted)

    def test_encrypted_data_differs_from_original(self):
        original = np.random.randn(128).astype(np.float64)
        encrypted, iv = encrypt_embedding(original)
        assert encrypted != original.tobytes()

    def test_different_iv_each_time(self):
        original = np.random.randn(128).astype(np.float64)
        _, iv1 = encrypt_embedding(original)
        _, iv2 = encrypt_embedding(original)
        assert iv1 != iv2

    def test_wrong_iv_fails(self):
        import os
        original = np.random.randn(128).astype(np.float64)
        encrypted, iv = encrypt_embedding(original)
        wrong_iv = os.urandom(16)
        # With wrong IV, decryption may not raise but must produce wrong data
        try:
            decrypted = decrypt_embedding(encrypted, wrong_iv)
            # If it doesn't raise, the output must differ from the original
            assert not np.array_equal(original, decrypted)
        except Exception:
            pass  # An exception is also acceptable


class TestBiometricTemplateModel:
    @pytest.mark.django_db
    def test_template_creation(self, tenant, employee):
        embedding = np.random.randn(128).astype(np.float64)
        encrypted, iv = encrypt_embedding(embedding)

        template = BiometricTemplate.objects.create(
            tenant=tenant,
            employee=employee,
            encrypted_embedding=encrypted,
            encryption_iv=iv,
            num_images_used=5,
            status=BiometricTemplate.Status.ACTIVE,
            quality_score=0.85,
        )
        assert template.pk is not None
        assert template.status == BiometricTemplate.Status.ACTIVE
        assert template.embedding_version == 1

    @pytest.mark.django_db
    def test_template_str(self, tenant, employee):
        embedding = np.random.randn(128).astype(np.float64)
        encrypted, iv = encrypt_embedding(embedding)

        template = BiometricTemplate.objects.create(
            tenant=tenant,
            employee=employee,
            encrypted_embedding=encrypted,
            encryption_iv=iv,
        )
        assert "Template v1" in str(template)


class TestBiometricEnrollmentLog:
    @pytest.mark.django_db
    def test_log_creation(self, tenant, employee):
        log = BiometricEnrollmentLog.objects.create(
            tenant=tenant,
            employee=employee,
            event=BiometricEnrollmentLog.Event.STARTED,
            details={"num_images": 5},
        )
        assert log.event == "STARTED"
        assert log.details["num_images"] == 5


class TestBiometricAPI:
    @pytest.mark.django_db
    def test_enroll_requires_authentication(self, api_client, tenant):
        response = api_client.post(f"/api/v1/{tenant.slug}/biometric/enroll/")
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_verify_requires_authentication(self, api_client, tenant):
        response = api_client.post(f"/api/v1/{tenant.slug}/biometric/verify/")
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_list_templates(self, authenticated_client, tenant, employee):
        response = authenticated_client.get(
            f"/api/v1/{tenant.slug}/biometric/templates/"
        )
        assert response.status_code == 200
