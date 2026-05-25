#!/bin/bash
# setup.sh - Passman Multi-Platform Installer
# Works on: Linux, Mac, Windows (Git Bash / WSL)

set -e

# Colors (soporte básico, en Windows pueden no funcionar)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Detectar SO
detect_os() {
    case "$(uname -s)" in
        Linux*)     echo "linux";;
        Darwin*)    echo "mac";;
        MINGW*|MSYS*|CYGWIN*) echo "windows";;
        *)          echo "unknown";;
    esac
}

OS=$(detect_os)
echo -e "${BLUE}🔐 Passman - Password Manager Installer${NC}"
echo -e "${BLUE}Detected OS: ${OS}${NC}"
echo "========================================="

# Verificar Python
check_python() {
    if command -v python3 &> /dev/null; then
        echo -e "${GREEN}✅ Python3 found: $(python3 --version)${NC}"
        return 0
    elif command -v python &> /dev/null; then
        echo -e "${GREEN}✅ Python found: $(python --version)${NC}"
        PYTHON_CMD="python"
        return 0
    else
        echo -e "${RED}❌ Python not found. Please install Python 3.7+${NC}"
        if [ "$OS" = "windows" ]; then
            echo "   Download from: https://www.python.org/downloads/"
            echo "   Make sure to check 'Add Python to PATH' during installation"
        else
            echo "   Ubuntu/Debian: sudo apt install python3 python3-venv"
            echo "   Fedora: sudo dnf install python3"
            echo "   Mac: brew install python3"
        fi
        exit 1
    fi
}

check_python

# Usar python3 o python según disponibilidad
if [ -z "$PYTHON_CMD" ]; then
    PYTHON_CMD="python3"
fi

# Crear entorno virtual
echo -e "${YELLOW}📦 Creating virtual environment...${NC}"

# En Windows, el comando venv es el mismo
$PYTHON_CMD -m venv passman_env

# Activar según SO
activate_venv() {
    if [ "$OS" = "windows" ]; then
        # Windows Git Bash
        source passman_env/Scripts/activate 2>/dev/null || source passman_env/bin/activate
    else
        # Linux/Mac
        source passman_env/bin/activate
    fi
}

activate_venv

# Instalar dependencias
echo -e "${YELLOW}📥 Installing dependencies...${NC}"
pip install --upgrade pip
pip install cryptography pyperclip

# Crear launcher multiplataforma
echo -e "${YELLOW}🚀 Creating launcher...${NC}"

if [ "$OS" = "windows" ]; then
    # Launcher para Windows (.bat)
    cat > passman.bat << 'EOF'
@echo off
cd /d "%~dp0"
call passman_env\Scripts\activate.bat
python passman.py
pause
EOF
    echo -e "${GREEN}✅ Created passman.bat${NC}"
    
    # También crear .sh para Git Bash/WSL
    cat > passman << 'EOF'
#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/passman_env/Scripts/activate"
python "$DIR/passman.py"
EOF
    chmod +x passman 2>/dev/null || true
    echo -e "${GREEN}✅ Created passman (for Git Bash/WSL)${NC}"
else
    # Launcher para Linux/Mac
    cat > passman << 'EOF'
#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/passman_env/bin/activate"
python3 "$DIR/passman.py"
EOF
    chmod +x passman
    echo -e "${GREEN}✅ Created passman launcher${NC}"
fi

echo ""
echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""
echo -e "${BLUE}To run Passman:${NC}"
if [ "$OS" = "windows" ]; then
    echo "  Double-click passman.bat"
    echo "  OR in Git Bash: ./passman"
else
    echo "  ./passman"
fi
echo ""
echo -e "${BLUE}To install globally:${NC}"
if [ "$OS" = "windows" ]; then
    echo "  Add the folder to your PATH environment variable"
else
    echo "  sudo ln -s $(pwd)/passman /usr/local/bin/"
    echo "  passman"
fi
