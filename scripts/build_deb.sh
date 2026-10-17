#!/usr/bin/env bash
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

APP_NAME="pulse-telemetry"
VERSION="1.0.0"
ARCH="amd64"
DEB_NAME="${APP_NAME}_${VERSION}_${ARCH}.deb"

RELEASE_DIR="${PROJECT_ROOT}/releases"
BUILD_DIR="${PROJECT_ROOT}/build"
STAGE_ROOT=$(mktemp -d /tmp/deb-build-XXXXXX)
PKG_DIR="${STAGE_ROOT}/${APP_NAME}_${VERSION}_${ARCH}"

echo "==> Project root: ${PROJECT_ROOT}"
echo "==> Cleaning old build artifacts..."
rm -rf build dist "${RELEASE_DIR}/${DEB_NAME}"
mkdir -p "${RELEASE_DIR}" "${BUILD_DIR}"

# 1. Build PyInstaller bundle
echo "==> Freezing application with PyInstaller..."
uv run pyinstaller --noconfirm --onedir --windowed \
    --name "${APP_NAME}" \
    --specpath "${BUILD_DIR}" \
    --add-data "${PROJECT_ROOT}/Open_Sans:Open_Sans" \
    --add-data "${PROJECT_ROOT}/assets:assets" \
    app.py

# 2. Setup standard Linux packaging filesystem
echo "==> Assembling deb package structure..."
mkdir -p "${PKG_DIR}/opt/${APP_NAME}"
mkdir -p "${PKG_DIR}/usr/bin"
mkdir -p "${PKG_DIR}/usr/share/applications"
mkdir -p "${PKG_DIR}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${PKG_DIR}/DEBIAN"

# Copy binary & runtime assets
cp -a "dist/${APP_NAME}/." "${PKG_DIR}/opt/${APP_NAME}/"
ln -s "/opt/${APP_NAME}/${APP_NAME}" "${PKG_DIR}/usr/bin/${APP_NAME}"

# Install desktop icon
cp "${PROJECT_ROOT}/assets/icon.png" "${PKG_DIR}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"

# 3. Generate Desktop Entry
cat << EOF > "${PKG_DIR}/usr/share/applications/${APP_NAME}.desktop"
[Desktop Entry]
Name=Pulse Telemetry
Comment=Hardware and GPU Realtime Monitor
Exec=/usr/bin/${APP_NAME}
Icon=${APP_NAME}
Terminal=false
Type=Application
Categories=System;Monitor;Utility;
StartupWMClass=pulse-telemetry
EOF

# 4. Generate Control File
cat << EOF > "${PKG_DIR}/DEBIAN/control"
Package: ${APP_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Depends: libxcb-cursor0
Maintainer: Vishva Ramamurthy
Description: Realtime hardware and GPU monitoring dashboard
 Modern PyQt6 desktop telemetry dashboard for CPU, RAM, and NVIDIA GPUs.
EOF

# 5. Fix permissions & Build Package
chmod -R 755 "${PKG_DIR}"
chmod 644 "${PKG_DIR}/DEBIAN/control"
chmod 644 "${PKG_DIR}/usr/share/applications/${APP_NAME}.desktop"
chmod 644 "${PKG_DIR}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"

echo "==> Building .deb package..."
dpkg-deb --build --root-owner-group "${PKG_DIR}" "${RELEASE_DIR}/${DEB_NAME}"
rm -rf "${STAGE_ROOT}"

echo "✅ Linux package generated at: ${RELEASE_DIR}/${DEB_NAME}"