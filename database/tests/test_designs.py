"""
Tests 6-7: Design creation + material relationships.
"""
from app.models.material import MaterialCategory
from app.repositories.design_repository import DesignRepository
from app.repositories.material_repository import MaterialRepository
from app.repositories.project_repository import ProjectRepository


def _make_project(db_session):
    return ProjectRepository(db_session).create(name="Design Test Project")


def _make_material(db_session, name, category):
    return MaterialRepository(db_session).create(
        name=name, category=category,
        thermal_conductivity=0.5, density=1000, specific_heat=900,
        emissivity=0.9, solar_absorptivity=0.6, cost_factor=1.0,
    )


def test_design_creation(db_session):
    project = _make_project(db_session)
    repo = DesignRepository(db_session)
    design = repo.create(
        project_id=project.id,
        design_name="Baseline",
        is_baseline=True,
        length=6, width=5, height=3,
        wall_thickness=0.3, roof_thickness=0.2, floor_thickness=0.15,
        insulation_thickness=0.05, opening_percentage=15,
    )
    assert design.id is not None
    assert design.project_id == project.id


def test_design_material_relationships(db_session):
    project = _make_project(db_session)
    wall = _make_material(db_session, "Rel Wall Material", MaterialCategory.WALL)
    roof = _make_material(db_session, "Rel Roof Material", MaterialCategory.ROOF)

    repo = DesignRepository(db_session)
    design = repo.create(
        project_id=project.id,
        length=6, width=5, height=3,
        wall_thickness=0.3, roof_thickness=0.2, floor_thickness=0.15,
        wall_material_id=wall.id,
        roof_material_id=roof.id,
    )

    db_session.refresh(design)
    assert design.wall_material.name == "Rel Wall Material"
    assert design.roof_material.name == "Rel Roof Material"


def test_design_list_by_project(db_session):
    project = _make_project(db_session)
    repo = DesignRepository(db_session)
    repo.create(project_id=project.id, length=5, width=4, height=3,
                wall_thickness=0.3, roof_thickness=0.2, floor_thickness=0.15)
    repo.create(project_id=project.id, length=6, width=4, height=3,
                wall_thickness=0.3, roof_thickness=0.2, floor_thickness=0.15)
    assert len(repo.list_by_project(project.id)) == 2
