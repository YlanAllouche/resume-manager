#!/usr/bin/env python3
import json
import sys
import subprocess
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
                    str(theme_dir)
                ],
                capture_output=True,
                text=True,
                timeout=60
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
                    timeout=120
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
                if all(isinstance(k, str) and len(k) == 2 for k in obj.keys()) and \
                   all(isinstance(v, (str, int, float, bool)) or v is None for v in obj.values()):
                    languages.update(obj.keys())
                else:
                    for value in obj.values():
                        extract_languages(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_languages(item)
        
        extract_languages(resume)
        return languages if languages else {"en"}

    def _resolve_translations(self, obj: Any, language: str, available_languages: set) -> Any:
        if isinstance(obj, dict):
            if all(isinstance(k, str) and len(k) == 2 and k in available_languages 
                   for k in obj.keys()) and \
               all(isinstance(v, (str, int, float, bool)) or v is None for v in obj.values()):
                if language in obj:
                    return obj[language]
                elif "en" in obj:
                    return obj["en"]
                else:
                    return obj[next(iter(obj))]
            else:
                return {k: self._resolve_translations(v, language, available_languages) 
                        for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._resolve_translations(item, language, available_languages) 
                    for item in obj]
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
                job_path = work_dir / f"job{i}.json"
                self._save_json(job_path, job)
            
            del resume["work"]
            self._save_json(resume_path, resume)
            print(f"Split {work_count} jobs from {profile}")
        else:
            print(f"No work array found in {profile}/resume.json")

    def merge_jobs(self, profile: str) -> Dict[str, Any]:
        profile_dir = self.profiles_dir / profile
        resume_path = profile_dir / "resume.json"
        work_dir = profile_dir / "work"

        resume = self._load_json(resume_path)
        
        if work_dir.exists():
            jobs = []
            for job_file in sorted(work_dir.glob("*.json")):
                job = self._load_json(job_file)
                jobs.append(job)
            
            if jobs:
                jobs.sort(
                    key=lambda x: x.get("startDate", ""),
                    reverse=True
                )
                resume["work"] = jobs
        
        return resume

    def build(self, profile: str, language: Optional[str] = None, all_languages: bool = False) -> None:
        profile_dir = self.profiles_dir / profile
        
        if not profile_dir.exists():
            print(f"Profile '{profile}' not found")
            return
        
        resume = self.merge_jobs(profile)
        available_languages = self._get_available_languages(resume)
        
        if all_languages:
            languages = sorted(available_languages)
        elif language:
            languages = [language]
        else:
            languages = ["en"]
        
        for lang in languages:
            self._build_single(profile, resume, lang)

    def _build_single(self, profile: str, resume: Dict[str, Any], language: str) -> None:
        available_languages = self._get_available_languages(resume)
        resolved_resume = self._resolve_translations(resume, language, available_languages)
        
        basics = resolved_resume.get("basics", {})
        name = basics.get("name", "Resume")
        name_parts = name.split()
        
        if len(name_parts) >= 2:
            first_name = name_parts[0]
            last_name = name_parts[-1]
        elif len(name_parts) == 1:
            first_name = name_parts[0]
            last_name = ""
        else:
            first_name = "Resume"
            last_name = ""
        
        filename = f"{last_name.upper()}-{first_name.upper()}.pdf"
        output_dir = self.dist_dir / profile / language
        output_path = output_dir / filename
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self._generate_pdf(resolved_resume, output_path)
        print(f"Built {profile}/{language}/{filename}")

    def _generate_pdf(self, resume: Dict[str, Any], output_path: Path) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            resume_path = temp_dir_path / "resume.json"
            self._save_json(resume_path, resume)
            
            if not self.theme_dir.exists():
                print(f"Warning: Theme directory not found at {self.theme_dir}")
                print(f"Saving resume JSON only to {output_path}.json")
                self._save_json(output_path.parent / (output_path.stem + ".json"), resume)
                return
            
            output_path_abs = output_path.resolve()
            output_path_abs.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                result = subprocess.run(
                    [
                        "resume",
                        "export",
                        str(output_path_abs),
                        "--resume",
                        str(resume_path),
                        "--theme",
                        str(self.theme_dir)
                    ],
                    cwd=str(self.base_dir),
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    print(f"Warning: PDF generation failed: {result.stderr}")
                    self._save_json(output_path_abs.parent / (output_path_abs.stem + ".json"), resume)
            except FileNotFoundError:
                print("Warning: 'resume' CLI not found. Using resume-cli via npm.")
                try:
                    result = subprocess.run(
                        [
                            "npx",
                            "resume-cli",
                            "export",
                            str(output_path_abs),
                            "--resume",
                            str(resume_path),
                            "--theme",
                            str(self.theme_dir)
                        ],
                        cwd=str(self.base_dir),
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if result.returncode != 0:
                        print(f"Warning: PDF generation via npx failed: {result.stderr}")
                        self._save_json(output_path_abs.parent / (output_path_abs.stem + ".json"), resume)
                except Exception as e:
                    print(f"Warning: Could not generate PDF: {e}")
                    self._save_json(output_path_abs.parent / (output_path_abs.stem + ".json"), resume)
            except subprocess.TimeoutExpired:
                print("Warning: PDF generation timed out")
                self._save_json(output_path_abs.parent / (output_path_abs.stem + ".json"), resume)
            except Exception as e:
                print(f"Warning: Error during PDF generation: {e}")
                self._save_json(output_path_abs.parent / (output_path_abs.stem + ".json"), resume)


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python resume_manager.py split <profile>")
        print("  python resume_manager.py merge <profile>")
        print("  python resume_manager.py build <profile> <language>")
        print("  python resume_manager.py build <profile> --all")
        print("  python resume_manager.py build --all")
        sys.exit(1)

    manager = ResumeManager()
    command = sys.argv[1]

    if command == "split":
        if len(sys.argv) < 3:
            print("Usage: python resume_manager.py split <profile>")
            sys.exit(1)
        profile = sys.argv[2]
        manager.split_jobs(profile)

    elif command == "merge":
        if len(sys.argv) < 3:
            print("Usage: python resume_manager.py merge <profile>")
            sys.exit(1)
        profile = sys.argv[2]
        resume = manager.merge_jobs(profile)
        print(json.dumps(resume, indent=2, ensure_ascii=False))

    elif command == "build":
        if len(sys.argv) < 3:
            print("Usage:")
            print("  python resume_manager.py build <profile> <language>")
            print("  python resume_manager.py build <profile> --all")
            print("  python resume_manager.py build --all")
            sys.exit(1)

        if sys.argv[2] == "--all":
            profiles_dir = manager.profiles_dir
            if profiles_dir.exists():
                for profile_dir in profiles_dir.iterdir():
                    if profile_dir.is_dir():
                        manager.build(profile_dir.name, all_languages=True)
            else:
                print("No profiles directory found")
        else:
            profile = sys.argv[2]
            if len(sys.argv) >= 4 and sys.argv[3] == "--all":
                manager.build(profile, all_languages=True)
            elif len(sys.argv) >= 4:
                language = sys.argv[3]
                manager.build(profile, language=language)
            else:
                manager.build(profile, language="en")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
