#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional


class ResumeManager:
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir).resolve()
        self.profiles_dir = self.base_dir / "profiles"
        self.dist_dir = self.base_dir / "dist"
        self.theme_dir = self._ensure_theme()

    def _ensure_theme(self) -> Path:
        theme_dir = self.base_dir / "node_modules" / "jsonresume-theme-awesomish"

        if theme_dir.exists():
            return theme_dir

        print("Theme not found. Cloning jsonresume-theme-awesomish...")

        try:
            theme_dir.parent.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(
                [
                    "git",
                    "clone",
                    "https://github.com/ylanallouche/jsonresume-theme-awesomish.git",
                    str(theme_dir),
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                print(f"Cloned theme to {theme_dir}")
                self._install_dependencies(theme_dir)
                return theme_dir
            else:
                print(f"Warning: Clone failed: {result.stderr}")
        except Exception as e:
            print(f"Warning: Could not clone theme: {e}")

        return theme_dir

    def _install_dependencies(self, theme_dir: Path) -> None:
        for cmd in ["pnpm", "npm"]:
            try:
                result = subprocess.run(
                    [cmd, "install"],
                    cwd=str(theme_dir),
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode == 0:
                    print(f"Installed dependencies with {cmd}")
                    return
            except FileNotFoundError:
                continue
            except Exception as e:
                print(f"Warning: {cmd} install failed: {e}")

    def _load_json(self, path: Path) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_json(self, path: Path, data: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _get_available_languages(self, resume: Dict[str, Any]) -> set:
        languages = set()

        def extract_languages(obj: Any) -> None:
            if isinstance(obj, dict):
                if all(isinstance(k, str) and len(k) == 2 for k in obj.keys()) and all(
                    isinstance(v, (str, int, float, bool)) or v is None
                    for v in obj.values()
                ):
                    languages.update(obj.keys())
                else:
                    for value in obj.values():
                        extract_languages(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_languages(item)

        extract_languages(resume)
        return languages if languages else {"en"}

    def _resolve_translations(
        self, obj: Any, language: str, available_languages: set
    ) -> Any:
        if isinstance(obj, dict):
            if all(
                isinstance(k, str) and len(k) == 2 and k in available_languages
                for k in obj.keys()
            ) and all(
                isinstance(v, (str, int, float, bool)) or v is None
                for v in obj.values()
            ):
                if language in obj:
                    return obj[language]
                elif "en" in obj:
                    return obj["en"]
                else:
                    return obj[next(iter(obj))]
            else:
                return {
                    k: self._resolve_translations(v, language, available_languages)
                    for k, v in obj.items()
                }
        elif isinstance(obj, list):
            return [
                self._resolve_translations(item, language, available_languages)
                for item in obj
            ]
        else:
            return obj

    def split_jobs(self, profile: str) -> None:
        profile_dir = self.profiles_dir / profile
        resume_path = profile_dir / "resume.json"
        work_dir = profile_dir / "work"

        resume = self._load_json(resume_path)
        work_dir.mkdir(parents=True, exist_ok=True)

        if "work" in resume and isinstance(resume["work"], list):
            work_count = len(resume["work"])
            for i, job in enumerate(resume["work"]):
                self._save_json(work_dir / f"job{i}.json", job)

            del resume["work"]
            self._save_json(resume_path, resume)
            print(f"Split {work_count} jobs from {profile}")
        else:
            print(f"No work array found in {profile}/resume.json")

    def merge_jobs(self, profile: str) -> Dict[str, Any]:
        profile_dir = self.profiles_dir / profile
        resume = self._load_json(profile_dir / "resume.json")
        work_dir = profile_dir / "work"

        if work_dir.exists():
            jobs = [
                self._load_json(job_file)
                for job_file in sorted(work_dir.glob("*.json"))
            ]
            if jobs:
                jobs.sort(key=lambda x: x.get("startDate", ""), reverse=True)
                resume["work"] = jobs

        return resume

    def build(self, profile: Optional[str] = None) -> None:
        if profile:
            profile_dir = self.profiles_dir / profile
            if not profile_dir.exists():
                print(f"Profile '{profile}' not found")
                return
            self._build_profile(profile)
        else:
            if self.profiles_dir.exists():
                for profile_dir in self.profiles_dir.iterdir():
                    if profile_dir.is_dir():
                        self._build_profile(profile_dir.name)
            else:
                print("No profiles directory found")

    def _build_profile(self, profile: str) -> None:
        resume = self.merge_jobs(profile)
        available_languages = self._get_available_languages(resume)

        for lang in sorted(available_languages):
            self._build_single(profile, resume, lang)

    def _build_single(
        self, profile: str, resume: Dict[str, Any], language: str
    ) -> None:
        available_languages = self._get_available_languages(resume)
        resolved_resume = self._resolve_translations(
            resume, language, available_languages
        )

        name = resolved_resume.get("basics", {}).get("name", "Resume")
        name_parts = name.split()

        if len(name_parts) >= 2:
            last_name = name_parts[-1]
            first_name = name_parts[0]
        elif len(name_parts) == 1:
            last_name = ""
            first_name = name_parts[0]
        else:
            last_name = ""
            first_name = "Resume"

        filename = f"{last_name.upper()}-{first_name.upper()}"
        output_dir = self.dist_dir / profile / language
        output_path = output_dir / filename

        output_dir.mkdir(parents=True, exist_ok=True)
        self._generate_pdf(resolved_resume, output_path)
        print(f"Built {profile}/{language}/{filename}.pdf")

    def _generate_pdf(self, resume: Dict[str, Any], output_path: Path) -> None:
        output_path_abs = output_path.resolve()
        json_path = output_path_abs.parent / (output_path_abs.name + ".json")

        self._save_json(json_path, resume)

        if not self.theme_dir.exists():
            print(f"Warning: Theme not found at {self.theme_dir}")
            return

        theme_relative = "./" + str(self.theme_dir.relative_to(self.base_dir))

        with tempfile.TemporaryDirectory() as temp_dir:
            resume_path = Path(temp_dir) / "resume.json"
            self._save_json(resume_path, resume)

            for cmd in ["resume", "npx"]:
                try:
                    cmd_args = (
                        ["resume", "export"]
                        if cmd == "resume"
                        else ["npx", "resume-cli", "export"]
                    )
                    result = subprocess.run(
                        cmd_args
                        + [
                            str(output_path_abs) + ".pdf",
                            "--resume",
                            str(resume_path),
                            "--theme",
                            theme_relative,
                        ],
                        cwd=str(self.base_dir),
                        capture_output=True,
                        text=True,
                        timeout=60 if cmd == "npx" else 30,
                    )

                    if result.returncode == 0:
                        return
                except FileNotFoundError:
                    continue
                except subprocess.TimeoutExpired:
                    print("Warning: PDF generation timed out")
                    return
                except Exception as e:
                    print(f"Warning: PDF generation error: {e}")
                    return


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("split", "merge"):
        command = sys.argv[1]
        if len(sys.argv) < 3:
            print(f"Usage: python resume_manager.py {command} <profile>")
            sys.exit(1)

        profile = sys.argv[2]
        manager = ResumeManager(".")

        if command == "split":
            manager.split_jobs(profile)
        else:
            resume = manager.merge_jobs(profile)
            print(json.dumps(resume, indent=2, ensure_ascii=False))
        return

    location = "."
    profile = None

    for i, arg in enumerate(sys.argv[1:], 1):
        if arg.startswith("--"):
            if arg == "--profile" and i < len(sys.argv) - 1:
                profile = sys.argv[i + 1]
        elif i == 1:
            location = arg

    try:
        manager = ResumeManager(location)
        manager.build(profile)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
