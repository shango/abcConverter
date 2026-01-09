# macOS Setup and Usage Guide

Simple setup using Homebrew + Python venv (no conda required).

---

## Setup (One-Time)

```bash
# 1. Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install dependencies via Homebrew
brew install python@3.11 alembic

# 3. Clone/download the repository and run setup
cd /path/to/alembic_to_jsx
chmod +x setup.sh run.sh
./setup.sh
```

Done! The setup script creates a virtual environment (venv) that contains all the dependencies and automatically links everything.

---

## Usage

### GUI Mode
```bash
./run.sh
```

### Command Line Mode

**1. Activate the virtual environment:**
```bash
source venv/bin/activate
```
*Your command prompt will change to show `(venv)` - this means you're in the virtual environment.*

**2. Run the converter:**
```bash
# Basic usage
python a2j.py input.abc output.jsx

# With options (typical folder structure example)
# Project/
#   alembic_files/          <- Your source .abc files
#     tracking_shot.abc
#   ae_import/              <- Empty folder for output
#
python a2j.py alembic_files/tracking_shot.abc ae_import/tracking_shot.jsx --comp-name "MyScene"
# Creates: ae_import/tracking_shot.jsx + all .obj files in ae_import/

# Batch processing
for file in *.abc; do
  python a2j.py "$file" "${file%.abc}.jsx"
done

# Help
python a2j.py --help
```

**3. When done, deactivate the virtual environment:**
```bash
deactivate
```
*Your command prompt returns to normal.*

---

## Troubleshooting

**"ModuleNotFoundError: No module named 'alembic'"**
```bash
brew install alembic
./setup.sh  # Re-run setup
```

**"Command not found: brew"**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Check Alembic installation:**
```bash
python3 -c "import alembic.Abc; print('✓ Working')"
```

---

## Coming Back Later

After you've closed your terminal, here's how to use the app again:

```bash
# 1. Navigate to the project directory
cd /path/to/alembic_to_jsx

# 2. Activate the virtual environment
source venv/bin/activate
# Your prompt will show: (venv)

# 3. Run the app
./run.sh                                    # GUI mode
python a2j.py input.abc output.jsx          # CLI mode

# 4. When done, deactivate
deactivate
# Your prompt returns to normal
```

**Note:** The GUI script (`./run.sh`) automatically activates the venv for you. For CLI mode, you must activate it manually first.

---

## Dependencies

| Package | Installation |
|---------|-------------|
| Python 3.8+ | `brew install python@3.11` |
| Alembic | `brew install alembic` |
| numpy, imath | `pip install numpy imath` (auto-installed by setup.sh) |

---

## System Requirements

- macOS 10.15 (Catalina) or later
- 4 GB RAM minimum
- After Effects 2020+ (for JSX import)

---

For detailed documentation, see [README.md](README.md)
