"""Reference data for RBAC: global roles, all permissions, role links.

Reconciles the permission table with the Tool Gateway's tool permission codes
(previously 12 tool codes had no row and no role had any banking permission),
and makes this migration the single home of RBAC reference data (it was in
scripts/seed_api_gateway.py). Additive and idempotent: every insert is
ON CONFLICT DO NOTHING, so it is safe on databases that already contain the
seeded rows.

Revision ID: 0002_tool_permissions
Revises: 0001_initial_schema
Create Date: 2026-10-19
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_tool_permissions"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (role_code, role_name, description); tenant_id NULL = global role.
ROLES = [
    ("CUSTOMER", "Customer", "Standard banking customer"),
    ("SUPPORT_AGENT", "Support Agent", "Human customer support agent"),
    ("ADMIN", "Administrator", "Tenant administrator"),
]

# Permissions that existed before this migration (seeded by 0001-era seeds).
EXISTING_PERMISSIONS = [
    ("chat.read", "Read conversations", "Read customer conversations"),
    ("chat.write", "Send messages", "Send customer service messages"),
    ("account.read", "Read account information", "View authorized account information"),
    ("transaction.read", "Read transactions", "View authorized account transactions"),
    ("card.read", "Read card information", "View authorized card information"),
    ("card.block", "Block card", "Block an authorized customer card"),
    ("loan.read", "Read loan information", "View authorized loan information"),
    ("payment.read", "Read payments", "View payment information"),
    ("payment.create", "Create payment", "Create an authorized payment"),
    ("complaint.create", "Create complaint", "Create a customer complaint"),
    ("complaint.read", "Read complaint", "Read complaint information"),
    ("ticket.create", "Create support ticket", "Create customer support ticket"),
    ("ticket.read", "Read support ticket", "Read support ticket"),
    ("knowledge.read", "Read knowledge base", "Retrieve approved knowledge"),
    ("knowledge.write", "Manage knowledge base", "Create and update knowledge"),
    ("knowledge.publish", "Publish knowledge", "Approve and publish knowledge"),
    ("analytics.read", "Read analytics", "View tenant analytics"),
    ("admin.users", "Manage users", "Manage tenant users"),
    ("admin.roles", "Manage roles", "Manage roles and permissions"),
    ("audit.read", "Read audit logs", "View security and activity audit logs"),
    ("knowledge.manage", "Manage knowledge documents", "Upload and list knowledge documents"),
    ("users.manage", "Manage users (admin API)", "List and manage tenant users"),
]

# Tool Gateway permission codes that had no row.
NEW_TOOL_PERMISSIONS = [
    ("customer.profile.read", "Read customer profile", "View the customer's own profile"),
    ("account.balance.read", "Read account balance", "View an authorized account balance"),
    ("account.transactions.read", "Read account transactions", "View authorized account transactions"),
    ("card.transactions.read", "Read card transactions", "View authorized card transactions"),
    ("beneficiary.read", "Read beneficiaries", "View the customer's beneficiaries"),
    ("beneficiary.create", "Create beneficiary", "Add a beneficiary"),
    ("beneficiary.deactivate", "Deactivate beneficiary", "Remove a beneficiary"),
    ("payment.status.read", "Read payment status", "View the status of a payment"),
    ("payment.cancel", "Cancel payment", "Cancel a pending payment"),
    ("loan.status.read", "Read loan status", "View the status of a loan"),
    ("loan.payments.read", "Read loan payments", "View loan installments and payments"),
    ("complaint.status.read", "Read complaint status", "View the status of a complaint"),
]

CUSTOMER_TOOL_PERMISSIONS = [
    "customer.profile.read",
    "account.read", "account.balance.read", "account.transactions.read",
    "card.read", "card.transactions.read", "card.block",
    "beneficiary.read", "beneficiary.create", "beneficiary.deactivate",
    "payment.read", "payment.status.read", "payment.create", "payment.cancel",
    "loan.read", "loan.status.read", "loan.payments.read",
    "complaint.read", "complaint.status.read", "complaint.create",
]

ROLE_PERMISSIONS = {
    # Self-service on the customer's own data. HIGH/CRITICAL tools are still
    # held by the Tool Gateway until the customer confirms.
    "CUSTOMER": CUSTOMER_TOOL_PERMISSIONS + ["chat.read", "chat.write", "knowledge.read"],
    # Read-only on customer data, can raise complaints; no money movement or card blocking.
    "SUPPORT_AGENT": [
        "customer.profile.read",
        "account.read", "account.balance.read", "account.transactions.read",
        "card.read", "card.transactions.read",
        "beneficiary.read", "payment.read", "payment.status.read",
        "loan.read", "loan.status.read", "loan.payments.read",
        "complaint.read", "complaint.status.read", "complaint.create",
        "chat.read", "knowledge.read", "ticket.create", "ticket.read",
    ],
    "ADMIN": ["knowledge.manage", "audit.read", "users.manage", "knowledge.read"],
}

# Links that did not exist before this migration (ADMIN's other three did).
ADDED_LINKS = {
    "CUSTOMER": ROLE_PERMISSIONS["CUSTOMER"],
    "SUPPORT_AGENT": ROLE_PERMISSIONS["SUPPORT_AGENT"],
    "ADMIN": ["knowledge.read"],
}


def upgrade() -> None:
    conn = op.get_bind()
    for role_code, role_name, description in ROLES:
        conn.execute(
            sa.text(
                "INSERT INTO role (tenant_id, role_code, role_name, description) "
                "VALUES (NULL, :code, :name, :description) "
                "ON CONFLICT (role_code) WHERE tenant_id IS NULL DO NOTHING"
            ),
            {"code": role_code, "name": role_name, "description": description},
        )
    for code, name, description in EXISTING_PERMISSIONS + NEW_TOOL_PERMISSIONS:
        conn.execute(
            sa.text(
                "INSERT INTO permission (permission_code, permission_name, description) "
                "VALUES (:code, :name, :description) ON CONFLICT (permission_code) DO NOTHING"
            ),
            {"code": code, "name": name, "description": description},
        )
    for role_code, permission_codes in ROLE_PERMISSIONS.items():
        for permission_code in permission_codes:
            conn.execute(
                sa.text(
                    "INSERT INTO role_permission (role_id, permission_id) "
                    "SELECT r.id, p.id FROM role r, permission p "
                    "WHERE r.tenant_id IS NULL AND r.role_code = :role AND p.permission_code = :permission "
                    "ON CONFLICT DO NOTHING"
                ),
                {"role": role_code, "permission": permission_code},
            )


def downgrade() -> None:
    """Remove what this migration added. Roles and pre-existing permissions stay
    (deleting a role would cascade to users' role assignments)."""
    conn = op.get_bind()
    for role_code, permission_codes in ADDED_LINKS.items():
        conn.execute(
            sa.text(
                "DELETE FROM role_permission rp USING role r, permission p "
                "WHERE rp.role_id = r.id AND rp.permission_id = p.id "
                "AND r.tenant_id IS NULL AND r.role_code = :role AND p.permission_code = ANY(:permissions)"
            ),
            {"role": role_code, "permissions": permission_codes},
        )
    conn.execute(
        sa.text("DELETE FROM permission WHERE permission_code = ANY(:codes)"),
        {"codes": [code for code, _, _ in NEW_TOOL_PERMISSIONS]},
    )
