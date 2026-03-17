"""
Auth boundary tests for compliance endpoints and tenant utilities.

These tests run without a live database or network. They cover:
- Role-based access helpers (_is_admin, _tenant_scope)
- Tenant resolution logic (manual_tenant_from_product, DB field preference)
- HTTP 403 enforcement via FastAPI TestClient with mocked dependencies
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient


# ============================================================
#  Helpers from compliance module
# ============================================================

class TestIsAdmin:
    def _make_user(self, role_str: str):
        user = MagicMock()
        role = MagicMock()
        role.value = role_str
        user.role = role
        return user

    def test_admin_returns_true(self):
        from app.api.endpoints.compliance import _is_admin
        from app.models.core import UserRole
        user = self._make_user(UserRole.ADMIN.value)
        assert _is_admin(user) is True

    def test_insurer_returns_false(self):
        from app.api.endpoints.compliance import _is_admin
        from app.models.core import UserRole
        user = self._make_user(UserRole.INSURER.value)
        assert _is_admin(user) is False

    def test_compliance_officer_returns_false(self):
        from app.api.endpoints.compliance import _is_admin
        from app.models.core import UserRole
        user = self._make_user(UserRole.COMPLIANCE_OFFICER.value)
        assert _is_admin(user) is False

    def test_consumer_returns_false(self):
        from app.api.endpoints.compliance import _is_admin
        from app.models.core import UserRole
        user = self._make_user(UserRole.CONSUMER.value)
        assert _is_admin(user) is False


class TestTenantScope:
    def _make_user(self, tenant_id=None, email="user@example.com"):
        user = MagicMock()
        user.tenant_id = tenant_id
        user.email = email
        return user

    def test_returns_tenant_id_when_set(self):
        from app.api.endpoints.compliance import _tenant_scope
        user = self._make_user(tenant_id="admin@heirs-life.com")
        assert _tenant_scope(user) == "admin@heirs-life.com"

    def test_falls_back_to_email_when_no_tenant(self):
        from app.api.endpoints.compliance import _tenant_scope
        user = self._make_user(tenant_id=None, email="someone@example.com")
        assert _tenant_scope(user) == "someone@example.com"

    def test_empty_string_tenant_falls_back_to_email(self):
        from app.api.endpoints.compliance import _tenant_scope
        user = self._make_user(tenant_id="", email="someone@example.com")
        # empty string is falsy, so should fall back
        assert _tenant_scope(user) == "someone@example.com"


# ============================================================
#  Tenant utility: manual_tenant_from_product
# ============================================================

class TestManualTenantFromProduct:
    def test_life_product(self):
        from app.services.tenant import manual_tenant_from_product
        assert manual_tenant_from_product("Life Insurance") == "admin@heirs-life.com"

    def test_life_lowercase(self):
        from app.services.tenant import manual_tenant_from_product
        assert manual_tenant_from_product("life") == "admin@heirs-life.com"

    def test_gadget_product(self):
        from app.services.tenant import manual_tenant_from_product
        assert manual_tenant_from_product("Gadget Insurance") == "admin@heirs-gadget.com"

    def test_device_product(self):
        from app.services.tenant import manual_tenant_from_product
        assert manual_tenant_from_product("Device Cover") == "admin@heirs-gadget.com"

    def test_auto_product_falls_to_general(self):
        from app.services.tenant import manual_tenant_from_product
        assert manual_tenant_from_product("Auto Insurance") == "admin@heirs-general.com"

    def test_none_falls_to_general(self):
        from app.services.tenant import manual_tenant_from_product
        assert manual_tenant_from_product(None) == "admin@heirs-general.com"

    def test_empty_string_falls_to_general(self):
        from app.services.tenant import manual_tenant_from_product
        assert manual_tenant_from_product("") == "admin@heirs-general.com"


class TestManualTenantDBPreference:
    """The _manual_tenant() helper in compliance.py should prefer the DB field."""

    def _make_manual(self, tenant_id=None, product_type="Life Insurance"):
        manual = MagicMock()
        manual.tenant_id = tenant_id
        manual.product_type = product_type
        return manual

    def test_uses_db_tenant_id_when_set(self):
        from app.api.endpoints.compliance import _manual_tenant
        manual = self._make_manual(tenant_id="admin@custom-tenant.com", product_type="Life Insurance")
        # DB field wins even though product_type would resolve to heirs-life
        assert _manual_tenant(manual) == "admin@custom-tenant.com"

    def test_falls_back_to_product_type_when_no_db_tenant(self):
        from app.api.endpoints.compliance import _manual_tenant
        manual = self._make_manual(tenant_id=None, product_type="Gadget Insurance")
        assert _manual_tenant(manual) == "admin@heirs-gadget.com"

    def test_falls_back_to_product_type_when_tenant_empty(self):
        from app.api.endpoints.compliance import _manual_tenant
        manual = self._make_manual(tenant_id="", product_type="Life Insurance")
        assert _manual_tenant(manual) == "admin@heirs-life.com"


# ============================================================
#  HTTP 403 enforcement (TestClient with mocked dependencies)
# ============================================================

def _make_auth_user(role_str: str, tenant_id: str = None, email: str = "user@test.com"):
    """Create a mock User object suitable for injecting via get_current_user."""
    from app.models.core import UserRole
    user = MagicMock()
    role_enum = MagicMock()
    role_enum.value = role_str
    user.role = role_enum
    user.tenant_id = tenant_id
    user.email = email
    # Make it behave like a UserRole in `not in [...]` checks
    user.role.__eq__ = lambda self, other: (
        other.value == role_str if hasattr(other, "value") else str(other) == role_str
    )
    return user


@pytest.fixture
def test_client():
    """TestClient with mocked DB so no real Postgres is needed."""
    from app.main import app
    from app.db.session import get_db
    from app.services.auth import get_current_user

    async def mock_db():
        db = AsyncMock()
        # Return empty result sets by default
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        result.scalars.return_value.first.return_value = None
        db.execute = AsyncMock(return_value=result)
        yield db

    # Override DB globally for these tests
    app.dependency_overrides[get_db] = mock_db
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


class TestAuditLogAccess:
    def _override_user(self, app, role_str, tenant_id=None):
        from app.services.auth import get_current_user
        from app.models.core import UserRole

        user = MagicMock()
        role = MagicMock()
        role.value = role_str
        # Replicate the `not in [UserRole.ADMIN, ...]` comparison used in the endpoint
        user.role = getattr(UserRole, role_str.upper(), role)
        user.tenant_id = tenant_id
        user.email = "user@test.com"

        async def mock_user():
            return user

        app.dependency_overrides[get_current_user] = mock_user

    def test_consumer_gets_403_on_audit_log(self, test_client):
        from app.main import app
        self._override_user(app, "consumer")
        resp = test_client.get("/api/v1/compliance/audit-log")
        assert resp.status_code == 403

    def test_partner_gets_403_on_audit_log(self, test_client):
        from app.main import app
        self._override_user(app, "partner")
        resp = test_client.get("/api/v1/compliance/audit-log")
        assert resp.status_code == 403

    def test_insurer_gets_200_on_audit_log(self, test_client):
        from app.main import app
        self._override_user(app, "insurer", tenant_id="admin@heirs-life.com")
        resp = test_client.get("/api/v1/compliance/audit-log")
        assert resp.status_code == 200

    def test_compliance_officer_gets_200_on_audit_log(self, test_client):
        from app.main import app
        self._override_user(app, "compliance_officer", tenant_id="admin@heirs-life.com")
        resp = test_client.get("/api/v1/compliance/audit-log")
        assert resp.status_code == 200

    def test_admin_gets_200_on_audit_log(self, test_client):
        from app.main import app
        self._override_user(app, "admin")
        resp = test_client.get("/api/v1/compliance/audit-log")
        assert resp.status_code == 200


class TestSLABreachAccess:
    def _override_user(self, app, role_str, tenant_id=None):
        from app.services.auth import get_current_user
        from app.models.core import UserRole

        user = MagicMock()
        user.role = getattr(UserRole, role_str.upper(), MagicMock())
        user.tenant_id = tenant_id
        user.email = "user@test.com"

        async def mock_user():
            return user

        app.dependency_overrides[get_current_user] = mock_user

    def test_consumer_gets_403_on_sla_breaches(self, test_client):
        from app.main import app
        self._override_user(app, "consumer")
        resp = test_client.get("/api/v1/compliance/sla/breaches")
        assert resp.status_code == 403

    def test_insurer_gets_200_on_sla_breaches(self, test_client):
        from app.main import app
        self._override_user(app, "insurer", tenant_id="admin@heirs-general.com")
        resp = test_client.get("/api/v1/compliance/sla/breaches")
        assert resp.status_code == 200
