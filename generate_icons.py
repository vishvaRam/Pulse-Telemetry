import os
import sys
from PyQt6 import QtCore, QtGui, QtWidgets

def create_brand_icon():
    app = QtWidgets.QApplication(sys.argv) if not QtWidgets.QApplication.instance() else QtWidgets.QApplication.instance()
    
    os.makedirs("assets", exist_ok=True)
    size = 256
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtCore.Qt.GlobalColor.transparent)

    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

    # 1. Dark Rounded Badge Background
    bg_path = QtGui.QPainterPath()
    bg_path.addRoundedRect(12.0, 12.0, float(size - 24), float(size - 24), 54.0, 54.0)
    
    # Subtle gradient background (#121215 to #09090b)
    bg_grad = QtGui.QLinearGradient(0, 0, 0, size)
    bg_grad.setColorAt(0.0, QtGui.QColor("#18181e"))
    bg_grad.setColorAt(1.0, QtGui.QColor("#0a0a0d"))
    painter.fillPath(bg_path, bg_grad)

    # Outline border
    pen_border = QtGui.QPen(QtGui.QColor("#27272a"), 4.0)
    painter.setPen(pen_border)
    painter.drawPath(bg_path)

    # 2. Subtle Grid Guideline
    pen_grid = QtGui.QPen(QtGui.QColor("#22222b"), 2, QtCore.Qt.PenStyle.DashLine)
    painter.setPen(pen_grid)
    painter.drawLine(35, 128, size - 35, 128)

    # 3. Dynamic Telemetry Pulse Curve (Cyan / Emerald)
    pulse_path = QtGui.QPainterPath()
    points = [
        (35, 128),
        (75, 128),
        (95, 145),
        (115, 65),   # Sharp upward peak
        (135, 185),  # Deep downward dip
        (155, 105),  # Rebound peak
        (175, 128),
        (221, 128)
    ]

    pulse_path.moveTo(*points[0])
    for pt in points[1:]:
        pulse_path.lineTo(*pt)

    # Stroke the glowing line
    line_grad = QtGui.QLinearGradient(35, 0, 221, 0)
    line_grad.setColorAt(0.0, QtGui.QColor("#38bdf8")) # Sky cyan
    line_grad.setColorAt(1.0, QtGui.QColor("#4ade80")) # Emerald green

    pen_wave = QtGui.QPen(line_grad, 10.0, QtCore.Qt.PenStyle.SolidLine, QtCore.Qt.PenCapStyle.RoundCap, QtCore.Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen_wave)
    painter.drawPath(pulse_path)

    # 4. Beacon Indicator Dot with Glow
    glow_brush = QtGui.QBrush(QtGui.QColor("#4ade80"))
    painter.setBrush(glow_brush)
    painter.setPen(QtGui.QPen(QtGui.QColor("#ffffff"), 3.0))
    painter.drawEllipse(QtCore.QPointF(221, 128), 9.0, 9.0)

    painter.end()

    # Save PNG (Used by Ubuntu & Qt Window)
    png_path = os.path.join("assets", "icon.png")
    pixmap.save(png_path, "PNG")
    print(f"✅ Generated: {png_path}")

    # Generate Multi-size Windows .ico
    ico_path = os.path.join("assets", "icon.ico")
    icon = QtGui.QIcon()
    for s in [16, 32, 48, 64, 128, 256]:
        scaled = pixmap.scaled(s, s, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
        icon.addPixmap(scaled)
    pixmap.save(ico_path, "ICO")
    print(f"✅ Generated: {ico_path}")

if __name__ == "__main__":
    create_brand_icon()