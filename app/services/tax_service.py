from sqlalchemy import select

from app.models.tenant_tax_rule import TenantTaxRule


def get_tax_amount(db, tenant_id, amount):
    rule = db.execute(
        select(TenantTaxRule)
        .where(TenantTaxRule.tenant_id == tenant_id)
        .order_by(TenantTaxRule.effective_from.desc())
    ).scalar_one_or_none()

    if not rule:
        return 0

    return (amount * rule.rate) / 100
