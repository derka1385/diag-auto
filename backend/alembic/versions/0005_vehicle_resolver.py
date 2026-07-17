"""vehicle resolver technical identity

Revision ID: 0005_vehicle_resolver
Revises: 0004
"""
from alembic import op
import sqlalchemy as sa

revision="0005";down_revision="0004";branch_labels=None;depends_on=None

def upgrade():
    for table in ("vehicle_configuration_candidates","vehicle_configurations"):
        op.add_column(table,sa.Column("tecdoc_k_type",sa.String(100),nullable=True));op.add_column(table,sa.Column("cnit",sa.String(100),nullable=True));op.add_column(table,sa.Column("type_mine",sa.String(100),nullable=True));op.add_column(table,sa.Column("engine_ecu_manufacturer",sa.String(120),nullable=True));op.add_column(table,sa.Column("engine_ecu_model",sa.String(120),nullable=True));op.create_index(f"ix_{table}_tecdoc_k_type",table,["tecdoc_k_type"]);op.create_index(f"ix_{table}_cnit",table,["cnit"])
    op.add_column("vehicle_configurations",sa.Column("engine_code_from_provider",sa.String(100),nullable=True));op.add_column("vehicle_configurations",sa.Column("engine_code_confirmed_by_user",sa.String(100),nullable=True));op.add_column("vehicle_configurations",sa.Column("providers_used",sa.JSON(),nullable=False,server_default="[]"));op.add_column("vehicle_configurations",sa.Column("field_provenance",sa.JSON(),nullable=False,server_default="{}"))

def downgrade():
    for column in ("field_provenance","providers_used","engine_code_confirmed_by_user","engine_code_from_provider"):op.drop_column("vehicle_configurations",column)
    for table in ("vehicle_configurations","vehicle_configuration_candidates"):
        op.drop_index(f"ix_{table}_cnit",table_name=table);op.drop_index(f"ix_{table}_tecdoc_k_type",table_name=table)
        for column in ("engine_ecu_model","engine_ecu_manufacturer","type_mine","cnit","tecdoc_k_type"):op.drop_column(table,column)
