#!/bin/bash
# ESP32 Motion Detector Server - Automated Setup for Linux/Raspberry Pi
# ======================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    log_warning "Running as root. It's recommended to run as normal user."
fi

# Banner
echo "================================================"
echo " ESP32 Motion Detector Server - Setup Script"
echo "================================================"
echo ""

# Detect platform
if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model; then
    PLATFORM="raspberry_pi"
    log_info "Detected platform: Raspberry Pi"
else
    PLATFORM="linux"
    log_info "Detected platform: Linux"
fi

# Step 1: Check Python version
log_info "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is not installed!"
    log_info "Please install Python 3.8 or higher:"
    log_info "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    log_info "  Fedora: sudo dnf install python3 python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    log_error "Python $REQUIRED_VERSION or higher is required (found: $PYTHON_VERSION)"
    exit 1
fi

log_success "Python $PYTHON_VERSION found"

# Step 2: Check/Install system dependencies
log_info "Checking system dependencies..."

MISSING_PACKAGES=()

# Check for pip
if ! command -v pip3 &> /dev/null; then
    MISSING_PACKAGES+=("python3-pip")
fi

# Check for venv (optional but recommended)
if ! python3 -c "import venv" &> /dev/null; then
    MISSING_PACKAGES+=("python3-venv")
fi

# Check for libnotify (for Linux notifications)
if [ "$PLATFORM" = "linux" ]; then
    if ! command -v notify-send &> /dev/null; then
        MISSING_PACKAGES+=("libnotify-bin")
    fi
fi

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    log_warning "Missing system packages: ${MISSING_PACKAGES[*]}"
    log_info "To install them, run:"

    if command -v apt &> /dev/null; then
        log_info "  sudo apt update && sudo apt install ${MISSING_PACKAGES[*]}"
    elif command -v dnf &> /dev/null; then
        log_info "  sudo dnf install ${MISSING_PACKAGES[*]}"
    elif command -v pacman &> /dev/null; then
        log_info "  sudo pacman -S ${MISSING_PACKAGES[*]}"
    fi

    read -p "Do you want to install them now? (requires sudo) [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v apt &> /dev/null; then
            sudo apt update && sudo apt install -y "${MISSING_PACKAGES[@]}"
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y "${MISSING_PACKAGES[@]}"
        elif command -v pacman &> /dev/null; then
            sudo pacman -S --noconfirm "${MISSING_PACKAGES[@]}"
        fi
        log_success "System packages installed"
    else
        log_warning "Skipping system package installation. Some features may not work."
    fi
fi

# Step 3: Create virtual environment (optional but recommended)
read -p "Do you want to create a Python virtual environment? (recommended) [Y/n]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    if [ ! -d "venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv venv
        log_success "Virtual environment created"
    else
        log_info "Virtual environment already exists"
    fi

    log_info "Activating virtual environment..."
    source venv/bin/activate
    VENV_ACTIVE=true
    log_success "Virtual environment activated"
else
    VENV_ACTIVE=false
    log_warning "Skipping virtual environment. Installing globally."
fi

# Step 4: Upgrade pip
log_info "Upgrading pip..."
python3 -m pip install --upgrade pip

# Step 5: Install Python dependencies
log_info "Installing Python dependencies..."

# Install base requirements
log_info "Installing base requirements..."
pip3 install -r requirements.txt

# Install platform-specific requirements
if [ "$PLATFORM" = "linux" ]; then
    log_info "Installing Linux-specific requirements..."
    if [ -f requirements-linux.txt ]; then
        pip3 install -r requirements-linux.txt 2>/dev/null || log_warning "No additional Linux requirements"
    fi
fi

log_success "Python dependencies installed"

# Step 6: Download face recognition models
log_info "Downloading face recognition models..."

if [ ! -f models/face_detection_yunet_2023mar.onnx ] || [ ! -f models/face_recognition_sface_2021dec.onnx ]; then
    python3 models/download_models.py
    log_success "Face recognition models downloaded"
else
    log_info "Face recognition models already exist"
fi

# Verify models
if [ ! -f models/face_detection_yunet_2023mar.onnx ] || [ ! -f models/face_recognition_sface_2021dec.onnx ]; then
    log_error "Failed to download face recognition models!"
    log_info "Please download them manually from:"
    log_info "  https://github.com/opencv/opencv_zoo/tree/master/models/face_detection_yunet"
    log_info "  https://github.com/opencv/opencv_zoo/tree/master/models/face_recognition_sface"
    exit 1
fi

# Step 7: Create config.yaml if it doesn't exist
if [ ! -f config.yaml ]; then
    log_warning "config.yaml not found. Creating default config..."

    # Generate auth token
    AUTH_TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

    # Create config from template
    cat > config.yaml << EOF
# ESP32 Motion Detector - Server Configuration
# Auto-generated by setup script
# ==============================================

server:
  host: '0.0.0.0'
  port: 5000
  debug: false
  log_level: 'INFO'
  log_file: 'server.log'

security:
  # Generated authentication token
  auth_token: '$AUTH_TOKEN'
  require_auth_for_stream: true

storage:
  image_dir: './captured_images'
  max_images: 1000
  max_age_days: 30

notifications:
  enabled: true
  backend: 'linux_notify'  # linux_notify or disabled for headless
  sound: true

face_recognition:
  enabled: true  # Models downloaded
  db_path: './faces.db'
  faces_dir: './faces_db'

  threshold_strict: 0.35
  threshold_loose: 0.50
  margin_strict: 0.15
  margin_loose: 0.08

  min_face_size: 10000
  min_quality_score: 0.6

  auto_learning:
    enabled: true
    max_samples_per_person: 15
    cooldown_seconds: 60
    only_green_matches: true
    replace_strategy: 'oldest'

  auto_create_person: true
  new_person_name_template: 'Unbekannt #{count}'

stream:
  target_fps: 10
  jpeg_quality: 80
EOF

    log_success "config.yaml created with auth token: $AUTH_TOKEN"
    log_warning "IMPORTANT: Save this auth token! You'll need it for ESP32/client configuration."
    echo "$AUTH_TOKEN" > .auth_token
    log_info "Auth token also saved to .auth_token file"
else
    log_info "config.yaml already exists"

    # Extract existing token
    if command -v grep &> /dev/null; then
        EXISTING_TOKEN=$(grep "auth_token:" config.yaml | cut -d "'" -f 2 | head -n 1)
        if [ ! -z "$EXISTING_TOKEN" ] && [ "$EXISTING_TOKEN" != "YOUR_SECRET_TOKEN_CHANGE_ME_12345" ]; then
            log_info "Existing auth token found: $EXISTING_TOKEN"
        else
            log_warning "Please update the auth_token in config.yaml!"
            NEW_TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
            log_info "You can use this generated token: $NEW_TOKEN"
        fi
    fi
fi

# Step 8: Create necessary directories
log_info "Creating necessary directories..."
mkdir -p captured_images
mkdir -p faces_db
log_success "Directories created"

# Step 9: Test server startup (optional)
echo ""
read -p "Do you want to test the server startup? [Y/n]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    log_info "Starting server (press Ctrl+C to stop)..."
    log_info "Server will be available at: http://localhost:5000"

    # Get server IP
    if command -v hostname &> /dev/null; then
        SERVER_IP=$(hostname -I | awk '{print $1}')
        if [ ! -z "$SERVER_IP" ]; then
            log_info "Network access: http://$SERVER_IP:5000"
        fi
    fi

    echo ""
    python3 app.py
else
    log_info "Skipping server test"
fi

# Final instructions
echo ""
echo "================================================"
log_success "Setup completed successfully!"
echo "================================================"
echo ""
log_info "Next steps:"
echo ""
echo "1. Start the server:"
if [ "$VENV_ACTIVE" = true ]; then
    echo "   source venv/bin/activate  # Activate virtual environment"
fi
echo "   python3 app.py"
echo ""
echo "2. Configure your ESP32-CAM or Raspberry Pi client:"
echo "   - Use the auth token from config.yaml"
echo "   - Set server IP to your machine's IP address"
echo ""
echo "3. Open the web interface:"
echo "   http://localhost:5000"
echo ""

if [ "$PLATFORM" = "linux" ]; then
    echo "4. (Optional) Install as systemd service:"
    echo "   See: deploy/linux/systemd/"
    echo ""
fi

log_info "For more information, see README.md and docs/"
