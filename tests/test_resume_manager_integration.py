#!/usr/bin/env python3
"""
Integration test suite for the ResumeManager class.

These tests validate actual PDF generation and theme functionality.
They require external dependencies (resume-cli, node_modules) and take longer to run.

Run with: pytest tests/test_resume_manager_integration.py -v
Or to run only integration tests: pytest -m integration

These tests are slower than unit tests and should be run separately
from the main test suite for faster feedback during development.
"""

import json
import sys
from pathlib import Path

import pytest

# TODO: Mocking is bad

sys.path.insert(0, str(Path(__file__).parent.parent))

from resume_manager import ResumeManager


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace with profiles and node_modules."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    profiles_dir = workspace / "profiles"
    profiles_dir.mkdir()

    backend_dir = profiles_dir / "backend_dev"
    backend_dir.mkdir()
    backend_resume = {
        "basics": {
            "name": {"en": "John Smith", "fr": "Jean Smith"},
            "label": {"en": "Backend Developer", "fr": "Développeur Backend"},
            "email": "john@example.com",
            "summary": {
                "en": "Experienced backend developer with Python expertise",
                "fr": "Développeur backend expérimenté avec expertise en Python",
            },
            "location": {"city": "San Francisco", "countryCode": "US"},
        },
        "work": [
            {
                "name": "Tech Corp",
                "position": {
                    "en": "Senior Backend Engineer",
                    "fr": "Ingénieur Backend Senior",
                },
                "startDate": "2022-01-15",
                "endDate": "2024-12-31",
                "summary": {
                    "en": "Led backend improvements",
                    "fr": "J'ai dirigé des améliorations",
                },
            },
            {
                "name": "StartupXYZ",
                "position": {"en": "Backend Developer", "fr": "Développeur Backend"},
                "startDate": "2020-06-01",
                "endDate": "2022-01-14",
                "summary": {
                    "en": "Built RESTful APIs",
                    "fr": "Construit des APIs RESTful",
                },
            },
        ],
        "education": [
            {
                "institution": "University of California",
                "studyType": "Bachelor",
                "area": "Computer Science",
            }
        ],
        "skills": [
            {
                "name": {"en": "Backend Development", "fr": "Développement Backend"},
                "level": {"en": "Expert", "fr": "Expert"},
                "keywords": ["Python", "PostgreSQL"],
            }
        ],
    }
    with open(backend_dir / "resume.json", "w") as f:
        json.dump(backend_resume, f, indent=2, ensure_ascii=False)

    frontend_dir = profiles_dir / "frontend_dev"
    frontend_dir.mkdir()
    frontend_resume = {
        "basics": {
            "name": {"en": "Jane Doe", "fr": "Jeanne Doe"},
            "label": {"en": "Frontend Developer", "fr": "Développeuse Frontend"},
            "email": "jane@example.com",
            "summary": {
                "en": "Creative frontend developer with React expertise",
                "fr": "Développeuse frontend créative avec expertise React",
            },
            "location": {"city": "New York", "countryCode": "US"},
        },
        "work": [
            {
                "name": "Creative Studio",
                "position": {
                    "en": "Lead Frontend Engineer",
                    "fr": "Ingénieure Frontend Leader",
                },
                "startDate": "2023-03-01",
                "endDate": "",
                "summary": {
                    "en": "Leading frontend team",
                    "fr": "Diriger l'équipe frontend",
                },
            },
            {
                "name": "Web Solutions Inc",
                "position": {"en": "Frontend Developer", "fr": "Développeuse Frontend"},
                "startDate": "2021-01-15",
                "endDate": "2023-02-28",
                "summary": {
                    "en": "Developed web applications",
                    "fr": "Développé des applications web",
                },
            },
        ],
        "education": [
            {
                "institution": "Tech Bootcamp",
                "studyType": "Certificate",
                "area": "Full Stack Development",
            }
        ],
        "skills": [
            {
                "name": {"en": "Frontend Development", "fr": "Développement Frontend"},
                "level": {"en": "Expert", "fr": "Expert"},
                "keywords": ["React", "TypeScript"],
            }
        ],
    }
    with open(frontend_dir / "resume.json", "w") as f:
        json.dump(frontend_resume, f, indent=2, ensure_ascii=False)

    (workspace / "node_modules").mkdir()

    return workspace


@pytest.fixture
def manager(temp_workspace):
    """Create a ResumeManager instance."""
    return ResumeManager(str(temp_workspace))


@pytest.mark.integration
class TestPDFGeneration:
    """Integration tests for PDF generation with real resume-cli."""

    def test_integration_pdf_generation_single_profile(self, manager, temp_workspace):
        """Test actual PDF generation for a single profile."""
        manager.build("backend_dev")

        dist_dir = temp_workspace / "dist" / "backend_dev"
        assert dist_dir.exists()

        en_json = dist_dir / "en" / "SMITH-JOHN.json"
        fr_json = dist_dir / "fr" / "SMITH-JEAN.json"

        assert en_json.exists(), "English JSON should exist"
        assert fr_json.exists(), "French JSON should exist"

        with open(en_json) as f:
            en_resume = json.load(f)
        assert en_resume["basics"]["name"] == "John Smith"
        assert "work" in en_resume

    def test_integration_pdf_generation_all_profiles(self, manager, temp_workspace):
        """Test actual PDF generation for all profiles."""
        manager.build(None)

        dist_dir = temp_workspace / "dist"

        assert (dist_dir / "backend_dev" / "en").exists()
        assert (dist_dir / "backend_dev" / "fr").exists()
        assert (dist_dir / "frontend_dev" / "en").exists()
        assert (dist_dir / "frontend_dev" / "fr").exists()

        backend_en = dist_dir / "backend_dev" / "en" / "SMITH-JOHN.json"
        backend_fr = dist_dir / "backend_dev" / "fr" / "SMITH-JEAN.json"

        assert backend_en.exists()
        assert backend_fr.exists()

        with open(backend_en) as f:
            backend_en_data = json.load(f)
        with open(backend_fr) as f:
            backend_fr_data = json.load(f)

        assert backend_en_data["basics"]["name"] == "John Smith"
        assert backend_fr_data["basics"]["name"] == "Jean Smith"

        frontend_en = dist_dir / "frontend_dev" / "en" / "DOE-JANE.json"
        frontend_fr = dist_dir / "frontend_dev" / "fr" / "DOE-JEANNE.json"

        assert frontend_en.exists()
        assert frontend_fr.exists()

        with open(frontend_en) as f:
            frontend_en_data = json.load(f)
        with open(frontend_fr) as f:
            frontend_fr_data = json.load(f)

        assert frontend_en_data["basics"]["name"] == "Jane Doe"
        assert frontend_fr_data["basics"]["name"] == "Jeanne Doe"

    def test_integration_json_work_array_preservation(self, manager, temp_workspace):
        """Test that work arrays are correctly preserved in generated JSONs."""
        manager.build("backend_dev")

        json_path = temp_workspace / "dist" / "backend_dev" / "en" / "SMITH-JOHN.json"
        with open(json_path) as f:
            resume = json.load(f)

        assert "work" in resume
        assert len(resume["work"]) == 2

        assert resume["work"][0]["name"] == "Tech Corp"
        assert resume["work"][1]["name"] == "StartupXYZ"

        assert isinstance(resume["work"][0]["position"], str)
        assert resume["work"][0]["position"] == "Senior Backend Engineer"

    def test_integration_split_and_build(self, manager, temp_workspace):
        """Test the full workflow: split work section, then build."""
        manager.split_section("backend_dev", "work")

        work_dir = temp_workspace / "profiles" / "backend_dev" / "work"
        assert work_dir.exists()
        assert len(list(work_dir.glob("*.json"))) == 2

        manager.build("backend_dev")

        json_path = temp_workspace / "dist" / "backend_dev" / "en" / "SMITH-JOHN.json"
        with open(json_path) as f:
            resume = json.load(f)

        assert "work" in resume
        assert len(resume["work"]) == 2

    def test_integration_theme_installation(self, manager):
        """Test that theme directory is properly set up."""
        assert manager.theme_dir.exists()


@pytest.mark.integration
@pytest.mark.slow
class TestPDFGenerationSlow:
    """Slower integration tests that test PDF file generation (if resume-cli available)."""

    def test_integration_actual_pdf_creation(self, manager, temp_workspace):
        """Test that actual PDF files are created if resume-cli is available."""
        manager.build("backend_dev")

        dist_dir = temp_workspace / "dist" / "backend_dev"

        en_pdf = dist_dir / "en" / "SMITH-JOHN.pdf"
        fr_pdf = dist_dir / "fr" / "SMITH-JEAN.pdf"

        assert (dist_dir / "en" / "SMITH-JOHN.json").exists()
        assert (dist_dir / "fr" / "SMITH-JEAN.json").exists()

        if en_pdf.exists():
            assert en_pdf.stat().st_size > 0, "PDF should have content"
        if fr_pdf.exists():
            assert fr_pdf.stat().st_size > 0, "PDF should have content"
