"""initial schema

Revision ID: 845dce14a600
Revises:
Create Date: 2026-09-13 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "845dce14a600"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


material_category = postgresql.ENUM(
    "WALL", "ROOF", "FLOOR", "INSULATION", name="material_category"
)
simulation_status = postgresql.ENUM(
    "CREATED", "RUNNING", "COMPLETED", "FAILED", name="simulation_status"
)
simulation_backend = postgresql.ENUM("MOCK", "ANSYS", name="simulation_backend")
optimization_status = postgresql.ENUM(
    "CREATED", "RUNNING", "COMPLETED", "FAILED", name="optimization_status"
)
report_format = postgresql.ENUM("JSON", "MARKDOWN", name="report_format")


def upgrade() -> None:
    bind = op.get_bind()
    material_category.create(bind, checkfirst=True)
    simulation_status.create(bind, checkfirst=True)
    simulation_backend.create(bind, checkfirst=True)
    optimization_status.create(bind, checkfirst=True)
    report_format.create(bind, checkfirst=True)

    # ---------------------------------------------------------------
    # materials
    # ---------------------------------------------------------------
    op.create_table(
        "materials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "category",
            postgresql.ENUM(
                "WALL", "ROOF", "FLOOR", "INSULATION",
                name="material_category", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("description", sa.Text()),
        sa.Column("thermal_conductivity", sa.Numeric(10, 4), nullable=False),
        sa.Column("density", sa.Numeric(10, 2), nullable=False),
        sa.Column("specific_heat", sa.Numeric(10, 2), nullable=False),
        sa.Column("emissivity", sa.Numeric(4, 3), nullable=False),
        sa.Column("solar_absorptivity", sa.Numeric(4, 3), nullable=False),
        sa.Column("cost_factor", sa.Numeric(10, 3), nullable=False, server_default="1.0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", name="uq_materials_name"),
        sa.CheckConstraint("thermal_conductivity > 0", name="ck_materials_thermal_conductivity_positive"),
        sa.CheckConstraint("density > 0", name="ck_materials_density_positive"),
        sa.CheckConstraint("specific_heat > 0", name="ck_materials_specific_heat_positive"),
        sa.CheckConstraint("emissivity >= 0 AND emissivity <= 1", name="ck_materials_emissivity_range"),
        sa.CheckConstraint(
            "solar_absorptivity >= 0 AND solar_absorptivity <= 1",
            name="ck_materials_solar_absorptivity_range",
        ),
        sa.CheckConstraint("cost_factor > 0", name="ck_materials_cost_factor_positive"),
    )

    # ---------------------------------------------------------------
    # projects
    # ---------------------------------------------------------------
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("location", sa.String(255)),
        sa.Column("description", sa.Text()),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("climate_type", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
            name="ck_projects_latitude_range",
        ),
        sa.CheckConstraint(
            "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
            name="ck_projects_longitude_range",
        ),
    )
    op.create_index("ix_projects_location", "projects", ["location"])

    # ---------------------------------------------------------------
    # climate_profiles
    # ---------------------------------------------------------------
    op.create_table(
        "climate_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("location", sa.String(255)),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("climate_type", sa.String(100)),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", name="uq_climate_profiles_name"),
    )

    # ---------------------------------------------------------------
    # climate_data
    # ---------------------------------------------------------------
    op.create_table(
        "climate_data",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "climate_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("climate_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("temperature", sa.Numeric(6, 2), nullable=False),
        sa.Column("humidity", sa.Numeric(5, 2), nullable=False),
        sa.Column("pressure", sa.Numeric(7, 2)),
        sa.Column("solar_radiation", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("wind_speed", sa.Numeric(6, 2)),
        sa.Column("wind_direction", sa.Numeric(5, 1)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("humidity >= 0 AND humidity <= 100", name="ck_climate_data_humidity_range"),
        sa.CheckConstraint("solar_radiation >= 0", name="ck_climate_data_solar_radiation_nonneg"),
        sa.CheckConstraint(
            "wind_direction IS NULL OR (wind_direction >= 0 AND wind_direction < 360)",
            name="ck_climate_data_wind_direction_range",
        ),
    )
    op.create_index(
        "ix_climate_data_profile_timestamp", "climate_data", ["climate_profile_id", "timestamp"]
    )

    # ---------------------------------------------------------------
    # designs
    # ---------------------------------------------------------------
    op.create_table(
        "designs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("design_name", sa.String(255)),
        sa.Column("description", sa.Text()),
        sa.Column("is_baseline", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_recommended", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("length", sa.Numeric(8, 3), nullable=False),
        sa.Column("width", sa.Numeric(8, 3), nullable=False),
        sa.Column("height", sa.Numeric(8, 3), nullable=False),
        sa.Column("wall_thickness", sa.Numeric(6, 4), nullable=False),
        sa.Column("roof_thickness", sa.Numeric(6, 4), nullable=False),
        sa.Column("floor_thickness", sa.Numeric(6, 4), nullable=False),
        sa.Column("insulation_thickness", sa.Numeric(6, 4), nullable=False, server_default="0"),
        sa.Column("opening_percentage", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("orientation", sa.Numeric(5, 1)),
        sa.Column("occupants", sa.Integer()),
        sa.Column("floor_area", sa.Numeric(10, 3)),
        sa.Column("target_min_temperature", sa.Numeric(5, 2)),
        sa.Column("target_max_temperature", sa.Numeric(5, 2)),
        sa.Column("budget", sa.Numeric(14, 2)),
        sa.Column("wall_material_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("materials.id")),
        sa.Column("roof_material_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("materials.id")),
        sa.Column("floor_material_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("materials.id")),
        sa.Column("insulation_material_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("materials.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("length > 0 AND width > 0 AND height > 0", name="ck_designs_dimensions_positive"),
        sa.CheckConstraint("wall_thickness > 0", name="ck_designs_wall_thickness_positive"),
        sa.CheckConstraint("roof_thickness > 0", name="ck_designs_roof_thickness_positive"),
        sa.CheckConstraint("floor_thickness > 0", name="ck_designs_floor_thickness_positive"),
        sa.CheckConstraint("insulation_thickness >= 0", name="ck_designs_insulation_thickness_nonneg"),
        sa.CheckConstraint(
            "opening_percentage >= 0 AND opening_percentage <= 100",
            name="ck_designs_opening_percentage_range",
        ),
        sa.CheckConstraint(
            "target_min_temperature IS NULL OR target_max_temperature IS NULL "
            "OR target_min_temperature <= target_max_temperature",
            name="ck_designs_target_temperature_order",
        ),
    )
    op.create_index("ix_designs_project_id", "designs", ["project_id"])

    # ---------------------------------------------------------------
    # simulations
    # ---------------------------------------------------------------
    op.create_table(
        "simulations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "design_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("designs.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "climate_profile_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("climate_profiles.id"), nullable=True,
        ),
        sa.Column("duration_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("timestep_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column(
            "status",
            postgresql.ENUM(
                "CREATED", "RUNNING", "COMPLETED", "FAILED",
                name="simulation_status", create_type=False,
            ),
            nullable=False, server_default="CREATED",
        ),
        sa.Column(
            "backend",
            postgresql.ENUM("MOCK", "ANSYS", name="simulation_backend", create_type=False),
            nullable=False, server_default="MOCK",
        ),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("error_message", sa.Text()),
        sa.Column("average_temperature", sa.Numeric(6, 2)),
        sa.Column("minimum_temperature", sa.Numeric(6, 2)),
        sa.Column("maximum_temperature", sa.Numeric(6, 2)),
        sa.Column("comfort_percentage", sa.Numeric(5, 2)),
        sa.Column("total_heat_loss", sa.Numeric(14, 3)),
        sa.Column("total_solar_gain", sa.Numeric(14, 3)),
        sa.Column("external_energy_requirement", sa.Numeric(14, 3)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_simulations_project_id", "simulations", ["project_id"])
    op.create_index("ix_simulations_design_id", "simulations", ["design_id"])

    # ---------------------------------------------------------------
    # simulation_results
    # ---------------------------------------------------------------
    op.create_table(
        "simulation_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "simulation_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("indoor_temperature", sa.Numeric(6, 2), nullable=False),
        sa.Column("outdoor_temperature", sa.Numeric(6, 2), nullable=False),
        sa.Column("heat_loss", sa.Numeric(12, 3)),
        sa.Column("solar_gain", sa.Numeric(12, 3)),
        sa.Column("comfort_status", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_simulation_results_simulation_timestamp",
        "simulation_results",
        ["simulation_id", "timestamp"],
    )

    # ---------------------------------------------------------------
    # optimization_runs
    # ---------------------------------------------------------------
    op.create_table(
        "optimization_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("baseline_design_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("designs.id")),
        sa.Column("best_design_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("designs.id")),
        sa.Column("algorithm", sa.String(100)),
        sa.Column(
            "status",
            postgresql.ENUM(
                "CREATED", "RUNNING", "COMPLETED", "FAILED",
                name="optimization_status", create_type=False,
            ),
            nullable=False, server_default="CREATED",
        ),
        sa.Column("candidate_count", sa.Integer()),
        sa.Column("iterations", sa.Integer()),
        sa.Column("best_score", sa.Numeric(10, 4)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_optimization_runs_project_id", "optimization_runs", ["project_id"])

    # ---------------------------------------------------------------
    # optimization_candidates
    # ---------------------------------------------------------------
    op.create_table(
        "optimization_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "optimization_run_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("optimization_runs.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "design_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("designs.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("generation", sa.Integer()),
        sa.Column("score", sa.Numeric(10, 4)),
        sa.Column("comfort_score", sa.Numeric(10, 4)),
        sa.Column("heat_loss_score", sa.Numeric(10, 4)),
        sa.Column("energy_score", sa.Numeric(10, 4)),
        sa.Column("cost_score", sa.Numeric(10, 4)),
        sa.Column("rank", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_optimization_candidates_run_id", "optimization_candidates", ["optimization_run_id"]
    )

    # ---------------------------------------------------------------
    # recommendations
    # ---------------------------------------------------------------
    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("design_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("designs.id")),
        sa.Column(
            "optimization_run_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("optimization_runs.id"),
        ),
        sa.Column("score", sa.Numeric(10, 4)),
        sa.Column("explanation", sa.Text()),
        sa.Column("trade_offs", postgresql.JSONB()),
        sa.Column("assumptions", postgresql.JSONB()),
        sa.Column("limitations", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ---------------------------------------------------------------
    # reports
    # ---------------------------------------------------------------
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column(
            "format",
            postgresql.ENUM("JSON", "MARKDOWN", name="report_format", create_type=False),
            nullable=False, server_default="JSON",
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("recommendations")
    op.drop_table("optimization_candidates")
    op.drop_index("ix_optimization_runs_project_id", table_name="optimization_runs")
    op.drop_table("optimization_runs")
    op.drop_index("ix_simulation_results_simulation_timestamp", table_name="simulation_results")
    op.drop_table("simulation_results")
    op.drop_index("ix_simulations_design_id", table_name="simulations")
    op.drop_index("ix_simulations_project_id", table_name="simulations")
    op.drop_table("simulations")
    op.drop_index("ix_designs_project_id", table_name="designs")
    op.drop_table("designs")
    op.drop_index("ix_climate_data_profile_timestamp", table_name="climate_data")
    op.drop_table("climate_data")
    op.drop_table("climate_profiles")
    op.drop_index("ix_projects_location", table_name="projects")
    op.drop_table("projects")
    op.drop_table("materials")

    bind = op.get_bind()
    report_format.drop(bind, checkfirst=True)
    optimization_status.drop(bind, checkfirst=True)
    simulation_backend.drop(bind, checkfirst=True)
    simulation_status.drop(bind, checkfirst=True)
    material_category.drop(bind, checkfirst=True)
