#!/usr/bin/env python3
"""
Comprehensive pytest test suite for the ResumeManager class.

Tests cover:
- Splitting array sections into individual files
- Merging section files back into arrays
- Building resumes for single and multiple profiles
- Building resumes for different languages
- Handling basics.json as a special case
- Handling optional resume.json
- Handling errors and edge cases
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from resume_manager import ResumeManager


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace with fragmented profile examples."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    profiles_dir = workspace / "profiles"
    profiles_dir.mkdir()

    backend_dir = profiles_dir / "backend_dev"
    backend_dir.mkdir()

    basics = {
        "name": {"en": "John Smith", "fr": "Jean Smith"},
        "label": {"en": "Backend Developer", "fr": "Développeur Backend"},
        "email": "john@example.com",
        "summary": {
            "en": "Experienced backend developer with Python expertise",
            "fr": "Développeur backend expérimenté avec expertise en Python",
        },
        "location": {"city": "San Francisco", "countryCode": "US"},
    }
    with open(backend_dir / "basics.json", "w") as f:
        json.dump(basics, f, indent=2, ensure_ascii=False)

    work_dir = backend_dir / "work"
    work_dir.mkdir()
    with open(work_dir / "0.json", "w") as f:
        json.dump(
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
            f,
            indent=2,
            ensure_ascii=False,
        )

    with open(work_dir / "1.json", "w") as f:
        json.dump(
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
            f,
            indent=2,
            ensure_ascii=False,
        )

    education_dir = backend_dir / "education"
    education_dir.mkdir()
    with open(education_dir / "0.json", "w") as f:
        json.dump(
            {
                "institution": "University of California",
                "studyType": "Bachelor",
                "area": "Computer Science",
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    skills_dir = backend_dir / "skills"
    skills_dir.mkdir()
    with open(skills_dir / "0.json", "w") as f:
        json.dump(
            {
                "name": {"en": "Backend Development", "fr": "Développement Backend"},
                "level": {"en": "Expert", "fr": "Expert"},
                "keywords": ["Python", "PostgreSQL"],
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    frontend_dir = profiles_dir / "frontend_dev"
    frontend_dir.mkdir()

    frontend_basics = {
        "name": {"en": "Jane Doe", "fr": "Jeanne Doe"},
        "label": {"en": "Frontend Developer", "fr": "Développeuse Frontend"},
        "email": "jane@example.com",
        "summary": {
            "en": "Creative frontend developer with React expertise",
            "fr": "Développeuse frontend créative avec expertise React",
        },
        "location": {"city": "New York", "countryCode": "US"},
    }
    with open(frontend_dir / "basics.json", "w") as f:
        json.dump(frontend_basics, f, indent=2, ensure_ascii=False)

    frontend_work_dir = frontend_dir / "work"
    frontend_work_dir.mkdir()
    with open(frontend_work_dir / "0.json", "w") as f:
        json.dump(
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
            f,
            indent=2,
            ensure_ascii=False,
        )

    with open(frontend_work_dir / "1.json", "w") as f:
        json.dump(
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
            f,
            indent=2,
            ensure_ascii=False,
        )

    frontend_education_dir = frontend_dir / "education"
    frontend_education_dir.mkdir()
    with open(frontend_education_dir / "0.json", "w") as f:
        json.dump(
            {
                "institution": "Tech Bootcamp",
                "studyType": "Certificate",
                "area": "Full Stack Development",
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    frontend_skills_dir = frontend_dir / "skills"
    frontend_skills_dir.mkdir()
    with open(frontend_skills_dir / "0.json", "w") as f:
        json.dump(
            {
                "name": {"en": "Frontend Development", "fr": "Développement Frontend"},
                "level": {"en": "Expert", "fr": "Expert"},
                "keywords": ["React", "TypeScript"],
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    (workspace / "node_modules").mkdir()

    return workspace


@pytest.fixture
def manager(temp_workspace):
    """Create a ResumeManager instance."""
    return ResumeManager(str(temp_workspace))


@pytest.fixture(autouse=True)
def mock_pdf_generation():
    """Mock the PDF generation and theme setup to avoid external dependencies."""

    def mock_generate_pdf(self, resume, output_path):
        output_path_abs = output_path.resolve()
        json_path = output_path_abs.parent / (output_path_abs.name + ".json")
        self._save_json(json_path, resume)

    def mock_ensure_theme(self):
        theme_dir = self.base_dir / "node_modules" / "jsonresume-theme-awesomish"
        theme_dir.mkdir(parents=True, exist_ok=True)
        return theme_dir

    with patch.object(ResumeManager, "_generate_pdf", mock_generate_pdf), patch.object(
        ResumeManager, "_ensure_theme", mock_ensure_theme
    ):
        yield


class TestMergeSection:
    """Tests for merging section files."""

    def test_merge_work_section(self, manager):
        """Test merging work files back into an array."""
        merged_items = manager._merge_section("backend_dev", "work")

        assert merged_items is not None
        assert len(merged_items) == 2
        assert merged_items[0]["name"] in ["Tech Corp", "StartupXYZ"]

    def test_merge_nonexistent_section(self, manager):
        """Test merging when section folder doesn't exist."""
        result = manager._merge_section("backend_dev", "nonexistent")
        assert result is None

    def test_merge_all_sections_without_resume_json(self, manager):
        """Test merging all fragmented sections without resume.json file."""
        merged_resume = manager._merge_all_sections("backend_dev")

        assert "basics" in merged_resume
        assert merged_resume["basics"]["name"]["en"] == "John Smith"
        assert "work" in merged_resume
        assert len(merged_resume["work"]) == 2
        assert "education" in merged_resume
        assert len(merged_resume["education"]) == 1
        assert "skills" in merged_resume
        assert len(merged_resume["skills"]) == 1

    def test_merge_basics_from_file(self, manager):
        """Test that basics.json is properly loaded when merging."""
        merged_resume = manager._merge_all_sections("backend_dev")

        assert merged_resume["basics"]["name"]["en"] == "John Smith"
        assert merged_resume["basics"]["label"]["fr"] == "Développeur Backend"


class TestBuildFunctionality:
    """Tests for building resumes."""

    def test_build_single_profile_no_resume_json(self, manager, temp_workspace):
        """Test building a single profile without resume.json file."""
        manager.build("backend_dev")

        dist_dir = temp_workspace / "dist" / "backend_dev"
        assert dist_dir.exists()
        assert (dist_dir / "en").exists()
        assert (dist_dir / "fr").exists()

    def test_build_all_profiles(self, manager, temp_workspace):
        """Test building all profiles."""
        manager.build(None)

        dist_dir = temp_workspace / "dist"
        assert (dist_dir / "backend_dev" / "en").exists()
        assert (dist_dir / "backend_dev" / "fr").exists()
        assert (dist_dir / "frontend_dev" / "en").exists()
        assert (dist_dir / "frontend_dev" / "fr").exists()

    def test_build_creates_json_outputs(self, manager, temp_workspace):
        """Test that build creates JSON files."""
        manager.build("backend_dev")

        assert (
            temp_workspace / "dist" / "backend_dev" / "en" / "SMITH-JOHN.json"
        ).exists()
        assert (
            temp_workspace / "dist" / "backend_dev" / "fr" / "SMITH-JEAN.json"
        ).exists()

    def test_build_json_contains_all_sections(self, manager, temp_workspace):
        """Test that built JSON files contain all merged sections."""
        manager.build("backend_dev")

        json_path = temp_workspace / "dist" / "backend_dev" / "en" / "SMITH-JOHN.json"
        with open(json_path) as f:
            resume = json.load(f)

        assert "basics" in resume
        assert "work" in resume
        assert len(resume["work"]) == 2
        assert "education" in resume
        assert "skills" in resume

    def test_build_resolves_translations(self, manager, temp_workspace):
        """Test that build correctly resolves translations."""
        manager.build("backend_dev")

        en_path = temp_workspace / "dist" / "backend_dev" / "en" / "SMITH-JOHN.json"
        with open(en_path) as f:
            en_resume = json.load(f)

        fr_path = temp_workspace / "dist" / "backend_dev" / "fr" / "SMITH-JEAN.json"
        with open(fr_path) as f:
            fr_resume = json.load(f)

        assert en_resume["basics"]["name"] == "John Smith"
        assert fr_resume["basics"]["name"] == "Jean Smith"

    def test_build_nonexistent_profile(self, manager):
        """Test that building a nonexistent profile handles gracefully."""
        manager.build("nonexistent_profile")


class TestLanguageDetection:
    """Tests for language detection and resolution."""

    def test_get_available_languages(self, manager):
        """Test detection of available languages."""
        resume = manager._merge_all_sections("backend_dev")

        languages = manager._get_available_languages(resume)
        assert "en" in languages
        assert "fr" in languages

    def test_resolve_translations_english(self, manager):
        """Test translation resolution for English."""
        test_obj = {"en": "Hello", "fr": "Bonjour"}
        available_langs = {"en", "fr"}

        result = manager._resolve_translations(test_obj, "en", available_langs)
        assert result == "Hello"

    def test_resolve_translations_french(self, manager):
        """Test translation resolution for French."""
        test_obj = {"en": "Hello", "fr": "Bonjour"}
        available_langs = {"en", "fr"}

        result = manager._resolve_translations(test_obj, "fr", available_langs)
        assert result == "Bonjour"

    def test_resolve_translations_fallback(self, manager):
        """Test that unsupported language falls back to English."""
        test_obj = {"en": "Hello", "fr": "Bonjour"}
        available_langs = {"en", "fr"}

        result = manager._resolve_translations(test_obj, "de", available_langs)
        assert result == "Hello"

    def test_resolve_translations_nested_objects(self, manager):
        """Test translation resolution for nested objects."""
        test_obj = {
            "name": {"en": "John", "fr": "Jean"},
            "position": {"en": "Engineer", "fr": "Ingénieur"},
        }
        available_langs = {"en", "fr"}

        result = manager._resolve_translations(test_obj, "fr", available_langs)
        assert result["name"] == "Jean"
        assert result["position"] == "Ingénieur"

    def test_resolve_translations_with_arrays(self, manager):
        """Test translation resolution for arrays."""
        test_obj = [
            {"name": {"en": "John", "fr": "Jean"}},
            {"name": {"en": "Jane", "fr": "Jeanne"}},
        ]
        available_langs = {"en", "fr"}

        result = manager._resolve_translations(test_obj, "fr", available_langs)
        assert result[0]["name"] == "Jean"
        assert result[1]["name"] == "Jeanne"
