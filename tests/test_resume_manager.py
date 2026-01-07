#!/usr/bin/env python3
"""
Comprehensive pytest test suite for the ResumeManager class.

Tests cover:
- Splitting work sections into individual job files
- Merging job files back into a work array
- Building resumes for single and multiple profiles
- Building resumes for different languages
- Handling errors and edge cases
"""

import json
import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from resume_manager import ResumeManager


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace with profiles and node_modules."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Create profiles directory
    profiles_dir = workspace / "profiles"
    profiles_dir.mkdir()

    # Create backend_dev profile
    backend_dir = profiles_dir / "backend_dev"
    backend_dir.mkdir()
    backend_resume = {
        "basics": {
            "name": {"en": "John Smith", "fr": "Jean Smith"},
            "label": {"en": "Backend Developer", "fr": "Développeur Backend"},
            "email": "john@example.com",
            "summary": {
                "en": "Experienced backend developer with Python expertise",
                "fr": "Développeur backend expérimenté avec expertise en Python"
            },
            "location": {"city": "San Francisco", "countryCode": "US"}
        },
        "work": [
            {
                "name": "Tech Corp",
                "position": {"en": "Senior Backend Engineer", "fr": "Ingénieur Backend Senior"},
                "startDate": "2022-01-15",
                "endDate": "2024-12-31",
                "summary": {
                    "en": "Led backend improvements",
                    "fr": "J'ai dirigé des améliorations"
                }
            },
            {
                "name": "StartupXYZ",
                "position": {"en": "Backend Developer", "fr": "Développeur Backend"},
                "startDate": "2020-06-01",
                "endDate": "2022-01-14",
                "summary": {
                    "en": "Built RESTful APIs",
                    "fr": "Construit des APIs RESTful"
                }
            }
        ],
        "education": [
            {
                "institution": "University of California",
                "studyType": "Bachelor",
                "area": "Computer Science"
            }
        ],
        "skills": [
            {
                "name": {"en": "Backend Development", "fr": "Développement Backend"},
                "level": {"en": "Expert", "fr": "Expert"},
                "keywords": ["Python", "PostgreSQL"]
            }
        ]
    }
    with open(backend_dir / "resume.json", "w") as f:
        json.dump(backend_resume, f, indent=2, ensure_ascii=False)

    # Create frontend_dev profile
    frontend_dir = profiles_dir / "frontend_dev"
    frontend_dir.mkdir()
    frontend_resume = {
        "basics": {
            "name": {"en": "Jane Doe", "fr": "Jeanne Doe"},
            "label": {"en": "Frontend Developer", "fr": "Développeuse Frontend"},
            "email": "jane@example.com",
            "summary": {
                "en": "Creative frontend developer with React expertise",
                "fr": "Développeuse frontend créative avec expertise React"
            },
            "location": {"city": "New York", "countryCode": "US"}
        },
        "work": [
            {
                "name": "Creative Studio",
                "position": {"en": "Lead Frontend Engineer", "fr": "Ingénieure Frontend Leader"},
                "startDate": "2023-03-01",
                "endDate": "",
                "summary": {
                    "en": "Leading frontend team",
                    "fr": "Diriger l'équipe frontend"
                }
            },
            {
                "name": "Web Solutions Inc",
                "position": {"en": "Frontend Developer", "fr": "Développeuse Frontend"},
                "startDate": "2021-01-15",
                "endDate": "2023-02-28",
                "summary": {
                    "en": "Developed web applications",
                    "fr": "Développé des applications web"
                }
            }
        ],
        "education": [
            {
                "institution": "Tech Bootcamp",
                "studyType": "Certificate",
                "area": "Full Stack Development"
            }
        ],
        "skills": [
            {
                "name": {"en": "Frontend Development", "fr": "Développement Frontend"},
                "level": {"en": "Expert", "fr": "Expert"},
                "keywords": ["React", "TypeScript"]
            }
        ]
    }
    with open(frontend_dir / "resume.json", "w") as f:
        json.dump(frontend_resume, f, indent=2, ensure_ascii=False)

    # Create node_modules directory
    (workspace / "node_modules").mkdir()

    return workspace


@pytest.fixture
def manager(temp_workspace):
    """Create a ResumeManager instance."""
    return ResumeManager(str(temp_workspace))


class TestSplitJobs:
    """Tests for splitting work sections."""

    def test_split_single_profile(self, manager, temp_workspace):
        """Test splitting work section of a single profile."""
        manager.split_jobs("backend_dev")

        work_dir = temp_workspace / "profiles" / "backend_dev" / "work"
        assert work_dir.exists()

        job_files = sorted(work_dir.glob("*.json"))
        assert len(job_files) == 2

        assert (work_dir / "job0.json").exists()
        assert (work_dir / "job1.json").exists()

        resume_path = temp_workspace / "profiles" / "backend_dev" / "resume.json"
        with open(resume_path) as f:
            resume = json.load(f)
        assert "work" not in resume

    def test_split_preserves_job_data(self, manager, temp_workspace):
        """Test that split preserves job data correctly."""
        manager.split_jobs("backend_dev")

        work_dir = temp_workspace / "profiles" / "backend_dev" / "work"
        with open(work_dir / "job0.json") as f:
            job0 = json.load(f)

        assert "name" in job0
        assert "position" in job0
        assert job0["name"] == "Tech Corp"

    def test_split_multiple_profiles(self, manager, temp_workspace):
        """Test splitting multiple profiles."""
        manager.split_jobs("backend_dev")
        manager.split_jobs("frontend_dev")

        backend_work_dir = temp_workspace / "profiles" / "backend_dev" / "work"
        assert len(list(backend_work_dir.glob("*.json"))) == 2

        frontend_work_dir = temp_workspace / "profiles" / "frontend_dev" / "work"
        assert len(list(frontend_work_dir.glob("*.json"))) == 2

    def test_split_nonexistent_profile_fails(self, manager):
        """Test that splitting a nonexistent profile fails."""
        with pytest.raises(FileNotFoundError):
            manager.split_jobs("nonexistent_profile")


class TestMergeJobs:
    """Tests for merging job files."""

    def test_merge_single_profile(self, manager, temp_workspace):
        """Test merging work files back into a work array."""
        manager.split_jobs("backend_dev")
        merged_resume = manager.merge_jobs("backend_dev")

        assert "work" in merged_resume
        assert len(merged_resume["work"]) == 2
        assert merged_resume["work"][0]["name"] in ["Tech Corp", "StartupXYZ"]

    def test_merge_preserves_job_order_by_date(self, manager, temp_workspace):
        """Test that merge orders jobs by start date (newest first)."""
        manager.split_jobs("backend_dev")
        merged_resume = manager.merge_jobs("backend_dev")

        work = merged_resume["work"]
        assert work[0]["name"] == "Tech Corp"
        assert work[1]["name"] == "StartupXYZ"

    def test_merge_without_split(self, manager):
        """Test merging when work section hasn't been split."""
        merged_resume = manager.merge_jobs("backend_dev")

        assert "work" in merged_resume
        assert len(merged_resume["work"]) == 2

    def test_merge_empty_work_directory(self, manager, temp_workspace):
        """Test merging when work directory is empty."""
        manager.split_jobs("backend_dev")

        work_dir = temp_workspace / "profiles" / "backend_dev" / "work"
        for job_file in work_dir.glob("*.json"):
            job_file.unlink()

        merged_resume = manager.merge_jobs("backend_dev")
        assert "work" not in merged_resume or len(merged_resume.get("work", [])) == 0


class TestBuildFunctionality:
    """Tests for building resumes."""

    def test_build_single_profile(self, manager, temp_workspace):
        """Test building a single profile."""
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

        assert (temp_workspace / "dist" / "backend_dev" / "en" / "SMITH-JOHN.json").exists()
        assert (temp_workspace / "dist" / "backend_dev" / "fr" / "SMITH-JEAN.json").exists()

    def test_build_json_contains_work_array(self, manager, temp_workspace):
        """Test that built JSON files contain the merged work array."""
        manager.build("backend_dev")

        json_path = temp_workspace / "dist" / "backend_dev" / "en" / "SMITH-JOHN.json"
        with open(json_path) as f:
            resume = json.load(f)

        assert "work" in resume
        assert len(resume["work"]) == 2

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
        resume = manager._load_json(
            Path(manager.base_dir) / "profiles" / "backend_dev" / "resume.json"
        )

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
            "position": {"en": "Engineer", "fr": "Ingénieur"}
        }
        available_langs = {"en", "fr"}

        result = manager._resolve_translations(test_obj, "fr", available_langs)
        assert result["name"] == "Jean"
        assert result["position"] == "Ingénieur"

    def test_resolve_translations_with_arrays(self, manager):
        """Test translation resolution for arrays."""
        test_obj = [
            {"name": {"en": "John", "fr": "Jean"}},
            {"name": {"en": "Jane", "fr": "Jeanne"}}
        ]
        available_langs = {"en", "fr"}

        result = manager._resolve_translations(test_obj, "fr", available_langs)
        assert result[0]["name"] == "Jean"
        assert result[1]["name"] == "Jeanne"
