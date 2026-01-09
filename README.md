
# JSON Resume Management System

Build tailored resumes for different clients and languages from a single source of truth.
Fragment your resume into organized, manageable JSON files (basics, education, work, skills, etc.), then automatically generate every profile/language variant as PDF.

![flow](./flow.gif)

## Quick Start


You can try it by going into the example folder and running:

```bash
# Build all profiles with all languages (default)
../resume_manager.py
# Or
python resume_manager.py # if available in PATH

# Build a specific profile
resume_manager.py --profile backend_dev

```

### Nvim based workflow

Make sure you have enabled local config in neovim in your init.lua with:

```lua
vim.o.exrc = true
```

Then, opening the example folder and trusting/allowing the local config, you will have autocommands on save for:
- rerendering all pdf's when modifying a json fragment in the profiles folder
- rerendering a particular pdf when modifying a json file in the dist folder for one off modification

## Features

### Translation 
Any field in your resume can be either a primitive value or a language-keyed dictionary.
The script detects which and resolves translations recursively through all nested structures.

```json
{
  "name": { "en": "John Smith", "es": "Jean Smith" },
  "email": "john@example.com",
  "work": [
    {
      "position": { "en": "Senior Engineer", "fr": "Ingenieur Senior" }
    }
  ]
}
```

**Translation Resolution**: Uses requested language → falls back to English → falls back to any available language.


### PDF & JSON Building
Automatically generates both PDF and JSON files with language-specific translations.

- Output: `dist/<profile>/<language>/LASTNAME-FIRSTNAME.{pdf,json}`
- Example: `dist/backend_dev/en/SMITH-JOHN.pdf`

### Automatic Theme Setup
Clones and installs the `jsonresume-theme-awesomish` theme automatically if not found.
Uses pnpm if available otherwise defaults to npm and if neither are present simply builds it up with git manually.

## Directory structure to make it work

```
├── profiles/                              # This is where you work
│   ├── backend_dev/
│   │   ├── basics.json                    # Personal info (name, email, etc.)
│   │   ├── work/                          # Job experiences
│   │   │   ├── 0.json
│   │   │   └── 1.json
│   │   ├── education/                     # Education history
│   │   │   ├── 0.json
│   │   │   └── 1.json
│   │   ├── skills/                        # Skills
│   │   │   ├── 0.json
│   │   │   ├── 1.json
│   │   │   └── 2.json
│   │   ├── projects/
│   │   ├── publications/
│   │   ├── certificates/
│   │   ├── awards/
│   │   ├── volunteer/
│   │   ├── interests/
│   │   ├── references/
│   │   └── languages/
│   └── frontend_dev/
│       ├── basics.json
│       ├── work/
│       └── ... (other sections)
├── dist/                                  # This is the output
│   ├── backend_dev/
│   │   ├── en/
│   │   │   ├── SMITH-JOHN.pdf
│   │   │   └── SMITH-JOHN.json            # Merged resume for this language
│   │   └── fr/
│   │       └── ...
│   └── ...
└── resume_manager.py
```

## Installation

### Requirements
- Python 3.8+
- `git`, `npm` or `pnpm` (for theme dependencies)
- `resume-cli` (automatic fallback to `npx resume-cli` if not installed globally)

### Setup
```bash
# Install resume-cli globally (optional, script can use npx)
pnpm install -g resume-cli #opional

# Run the script - it handles everything else
python resume_manager.py
```

## Usage Examples

### Build Everything
```bash
python resume_manager.py
# Builds all profiles with all detected languages
```

### Build Specific Profile
```bash
python resume_manager.py --profile backend_dev
# Builds both en and fr versions if available
```

### Build from Custom Location
```bash
python resume_manager.py /path/to/resume-project
# Looks for profiles/ and creates dist/ in that directory
```

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

## How It Works

1. **Language Detection**: Scans resume structure for dictionaries with 2-letter language codes (en, fr, etc.) and primitive values
2. **Section Merging**: Combines all fragmented sections:
   - Loads `basics.json` if it exists
   - Merges all folders (work, education, skills, etc.) in numeric file order
3. **Translation Resolution**: For each field, checks if it's a translation dict and applies language fallback logic
4. **PDF Generation**: Merges all sections, resolves translations for the target language, and generates PDF via resume-cli with the awesomish theme
5. **Naming**: Output files named `LASTNAME-FIRSTNAME.pdf` based on resolved `basics.name` for the target language


## Key Design Decisions

- **Generic Fragmentation**: All top-level array sections use the same fragmentation pattern
- **Numeric File Order**: Merge order determined by filename (0.json before 1.json, etc.) - users can renumber to reorder
- **Basics as Special Case**: Single `basics.json` file instead of a folder (it's an object, not an array)
- **Smart Language Fallbacks**: Missing language → English → any available language
- **Automatic Theme Setup**: No manual configuration needed
- **Dual Output**: Every PDF has a matching JSON file with the same name
- **In-Place Translations**: No separate translation files needed
- **Default to All**: Builds all languages automatically (no need for `--all` flag)

## Fragment Management

All JSON Resume array fields can be fragmented into individual files for easier editing and organization:

- **basics**: Stored as `basics.json` (single file, not a folder) - **required**
- **Array sections**: Each fragmented into a folder with numbered files (optional)
  - `work/`: Job experiences
  - `education/`: Education history
  - `skills/`: Skill entries
  - `languages/`: Languages
  - `certificates/`: Certifications
  - `awards/`: Awards and recognitions
  - `volunteer/`: Volunteer experiences
  - `publications/`: Publications and articles
  - `projects/`: Projects
  - `interests/`: Interests and hobbies
  - `references/`: References

### File Organization

- **basics.json**: Required file containing personal information
- **Section folders**: Create only the folders you need (e.g., if you have no awards, don't create `awards/`)
- **Numeric naming**: Files within section folders are named `0.json`, `1.json`, `2.json`, etc.
  - Files are merged in **numeric order** (0 comes before 1, 1 before 2, etc.)
  - You can use prefixes for readability: `01_main-job.json` sorts before `02_side-project.json`
- **No resume.json needed**: The build process automatically merges all sections from `basics.json` and section folders

### Usage

The build process automatically merges all fragmented sections during the build phase. Just organize your files in the profile directory and run:

```bash
# Build all profiles with all languages
python resume_manager.py

# Build a specific profile
python resume_manager.py --profile backend_dev
```
