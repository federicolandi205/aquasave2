"""Crea las tablas iniciales de AQUASAVE."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea tablas, índices, tipos enumerados y relación entre entidades."""
    estado_prototipo = sa.Enum("activo", "inactivo", name="estado_prototipo")
    estado_alerta = sa.Enum("VERDE", "AMARILLO", "ROJO", name="estado_alerta")
    # op.create_table crea automáticamente los tipos ENUM asociados a sus columnas.
    # No llamamos .create() antes porque PostgreSQL intentaría crear cada tipo dos veces.
    op.create_table(
        "prototypes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("codigo_unico", sa.String(length=64), nullable=False),
        sa.Column("latitud", sa.Float(), nullable=False),
        sa.Column("longitud", sa.Float(), nullable=False),
        sa.Column("barrio", sa.String(length=120), nullable=False),
        sa.Column("ciudad", sa.String(length=120), nullable=False),
        sa.Column("fecha_instalacion", sa.Date(), nullable=False),
        sa.Column("estado", estado_prototipo, nullable=False),
        sa.CheckConstraint("latitud >= -90 AND latitud <= 90", name="ck_prototypes_latitud"),
        sa.CheckConstraint("longitud >= -180 AND longitud <= 180", name="ck_prototypes_longitud"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codigo_unico"),
    )
    op.create_index("ix_prototypes_id", "prototypes", ["id"])
    op.create_index("ix_prototypes_codigo_unico", "prototypes", ["codigo_unico"])
    op.create_table(
        "measurements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("prototype_id", sa.Integer(), nullable=False),
        sa.Column("distancia_cm", sa.Float(), nullable=False),
        sa.Column("nivel_agua_cm", sa.Float(), nullable=False),
        sa.Column("porcentaje", sa.Float(), nullable=False),
        sa.Column("estado_alerta", estado_alerta, nullable=False),
        sa.Column("temperatura", sa.Float(), nullable=True),
        sa.Column("fecha_hora", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("distancia_cm >= 0", name="ck_measurements_distancia"),
        sa.CheckConstraint("nivel_agua_cm >= 0", name="ck_measurements_nivel"),
        sa.CheckConstraint("porcentaje >= 0 AND porcentaje <= 100", name="ck_measurements_porcentaje"),
        sa.ForeignKeyConstraint(["prototype_id"], ["prototypes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_measurements_id", "measurements", ["id"])
    op.create_index("ix_measurements_prototype_id", "measurements", ["prototype_id"])


def downgrade() -> None:
    """Elimina en orden inverso las tablas y los tipos enumerados."""
    op.drop_index("ix_measurements_prototype_id", table_name="measurements")
    op.drop_index("ix_measurements_id", table_name="measurements")
    op.drop_table("measurements")
    op.drop_index("ix_prototypes_codigo_unico", table_name="prototypes")
    op.drop_index("ix_prototypes_id", table_name="prototypes")
    op.drop_table("prototypes")
    sa.Enum(name="estado_alerta").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="estado_prototipo").drop(op.get_bind(), checkfirst=True)
