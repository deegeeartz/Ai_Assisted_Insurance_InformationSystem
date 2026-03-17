"""
Tenant resolution utilities.

The three Heirs tenants are identified by their insurer admin emails.
`manual_tenant_from_product()` is a fallback for records that pre-date the
`tenant_id` column on UnderwritingManual; new manuals have the field set
directly at upload time so the string-matching heuristic is not needed.
"""

_LIFE_TENANT = "admin@heirs-life.com"
_GADGET_TENANT = "admin@heirs-gadget.com"
_GENERAL_TENANT = "admin@heirs-general.com"


def manual_tenant_from_product(product_type: str | None) -> str:
    """Infer tenant from product_type string (legacy fallback only)."""
    product = (product_type or "").lower()
    if "life" in product:
        return _LIFE_TENANT
    if "gadget" in product or "device" in product:
        return _GADGET_TENANT
    return _GENERAL_TENANT


def policy_tenant_from_product(product_type: str | None) -> str:
    """Return the tenant_id to stamp on a new Policy based on product_type."""
    return manual_tenant_from_product(product_type)
