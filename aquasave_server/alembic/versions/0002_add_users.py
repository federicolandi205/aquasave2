"""Agregar cuentas de usuario con baja lógica."""
from alembic import op
import sqlalchemy as sa

revision = "0002_add_users"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=256), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("eliminado_en", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_id", "users", ["id"])

def downgrade():
    op.drop_index("ix_users_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
