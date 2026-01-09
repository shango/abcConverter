#!/bin/bash
# Setup script for macOS/Linux
# This creates a virtual environment and installs all dependencies

set -e

echo "===================================="
echo "Alembic to JSX Converter - Setup"
echo "===================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
echo "✓ Found Python $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install basic dependencies
echo "Installing Python dependencies..."
pip install numpy imath pyinstaller

# Install/Link Alembic
echo ""
echo "===================================="
echo "Setting up Alembic Python bindings"
echo "===================================="
echo ""

# Check if Homebrew Alembic is installed
if command -v brew &> /dev/null && brew list alembic &> /dev/null; then
    echo "✓ Homebrew Alembic found"

    # Determine correct PYTHONPATH based on Homebrew prefix
    BREW_PREFIX=$(brew --prefix)
    PYTHON_VERSION=$(python3 --version | grep -oE '[0-9]+\.[0-9]+')
    ALEMBIC_PYTHONPATH="$BREW_PREFIX/lib/python${PYTHON_VERSION}/site-packages"

    # Add to venv activation script
    ACTIVATE_SCRIPT="venv/bin/activate"
    if [ -f "$ACTIVATE_SCRIPT" ]; then
        # Check if PYTHONPATH is already set in activate script
        if ! grep -q "PYTHONPATH.*alembic" "$ACTIVATE_SCRIPT"; then
            echo "" >> "$ACTIVATE_SCRIPT"
            echo "# Link to Homebrew Alembic" >> "$ACTIVATE_SCRIPT"
            echo "export PYTHONPATH=\"$ALEMBIC_PYTHONPATH:\$PYTHONPATH\"" >> "$ACTIVATE_SCRIPT"
            echo "✓ Added Alembic to venv PYTHONPATH"
        else
            echo "✓ Alembic already linked to venv"
        fi
    fi

    # Also set for current session
    export PYTHONPATH="$ALEMBIC_PYTHONPATH:$PYTHONPATH"

    # Verify installation
    python3 -c "import alembic.Abc" 2>/dev/null && echo "✓ Alembic Python bindings working" || {
        echo "⚠ Warning: Could not verify Alembic import"
        echo "You may need to run: export PYTHONPATH=\"$ALEMBIC_PYTHONPATH:\$PYTHONPATH\""
    }

else
    echo "⚠ Homebrew Alembic not found"
    echo ""
    echo "Please install Alembic via Homebrew:"
    echo "  brew install alembic"
    echo ""
    echo "Then run this setup script again."
    exit 1
fi

echo ""
echo "===================================="
echo "Setup Complete!"
echo "===================================="
echo ""
echo "To run the converter:"
echo "  GUI Mode:  ./run.sh"
echo "  CLI Mode:  python a2j.py input.abc output.jsx"
echo ""
echo "For detailed macOS instructions, see: MACOS_SETUP.md"
echo ""
