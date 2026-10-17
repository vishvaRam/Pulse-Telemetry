# Pulse Telemetry ⚡

A modern, high-performance desktop hardware and GPU telemetry dashboard built with **Python**, **PyQt6**, **psutil**, and **NVIDIA NVML** (`nvidia-ml-py`).

Pulse Telemetry delivers real-time system monitoring with smooth, antialiased cubic-bezier wave graphs, comprehensive NVIDIA GPU telemetry, kernel concurrency statistics, and responsive dark/light/OLED themes.

---

## 🌟 Key Features

- **⚡ Real-Time Hardware Telemetry**

  - **CPU Utilization**: Live overall load percentage, logical core count, and current clock frequency (MHz).
  - **Physical Memory (RAM)**: Real-time memory consumption, percentage, and total capacity.
  - **NVIDIA GPU Core & VRAM**: Direct hardware queries via NVML for core load (%), dedicated VRAM allocation, GPU core temperature (°C), and real-time power draw (W).
  - **GPU Power-Saving & D3Cold State Resilient**: Gracefully detects dynamic standby/sleep states on hybrid and modern NVIDIA laptops without throwing exceptions.
  - **Kernel Concurrency**: Active Process ID (PID) count and total kernel thread tracking.
  - **Network Bandwidth**: Live download/upload speed gauges (MB/s) and aggregated bandwidth throughput (Mbps).
- **🎨 Modern & Responsive UI**

  - **Custom Sub-Pixel Antialiased Wave Graphs**: Smooth cubic-bezier curve rendering with dynamic gradient area fills and live beacon indicators.
  - **Always on Top (Pin Window)**: Keep the telemetry dashboard pinned over full-screen games, benchmarks, and workflows.
  - **Customizable Themes**: Built-in support for **Dark**, **OLED Black**, and **Light** modes.
  - **Dynamic Font & UI Scaling**: Integrated Open Sans typography with adjustable base font scaling.
  - **Configurable Polling Rates**: Choose between `0.5s` (High Speed), `1.0s` (Normal), and `2.0s` (Battery Saver).
- **📦 Cross-Platform Packaging Ready**

  - Native Linux `.deb` installer generation with full FreeDesktop desktop entry and icons.
  - Windows `.exe` single-file bundling support with custom multi-resolution icons.

---

## 📁 Project Structure

```plaintext
pulse-telemetry/
├── assets/                 # Application icon assets (.ico and .png)
│   ├── icon.ico
│   └── icon.png
├── Open_Sans/              # Bundled Open Sans font suite (OFL licensed)
├── releases/               # Packaged distributions (e.g., .deb installer)
├── scripts/
│   └── build_deb.sh        # Automated Debian (.deb) package build pipeline
├── app.py                  # Main PyQt6 dashboard application & telemetry engine
├── generate_icons.py       # Vector-based icon generator using QPainter
├── gpu_stress.py           # Pure ctypes CUDA driver GPU stress utility
├── requirements.txt        # Python package dependencies
├── RUN.md                  # Packaging and build execution commands
└── README.md               # Project documentation
```

---

## 🛠️ Prerequisites

- **Python**: `>= 3.9`
- **Linux** (Debian/Ubuntu, Fedora, Arch) or **Windows 10/11**
- *(Optional)* **NVIDIA GPU** with proprietary drivers installed for NVML telemetry and CUDA support.

---

## 🚀 Installation & Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/pulse-telemetry.git
cd pulse-telemetry
```

### 2. Set Up Virtual Environment

Using standard Python virtual environments:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Or using [`uv`](https://github.com/astral-sh/uv) (recommended for high speed):

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### 3. Run the Dashboard

```bash
python app.py
# or with uv
uv run app.py
```

---

## 📦 Building & Installing Packages

### 🐧 Linux (.deb Package)

To build a standalone Debian package:

```bash
chmod +x ./scripts/build_deb.sh
./scripts/build_deb.sh
```

To install the generated `.deb` package:

```bash
sudo apt install ./releases/pulse-telemetry_1.0.0_amd64.deb
```

Once installed, **Pulse Telemetry** will appear in your system applications menu with full icon and desktop launcher support.

### 🪟 Windows (.exe Executable)

To freeze and compile a standalone, windowed `.exe` binary:

```bash
uv run pyinstaller --noconfirm --onefile --windowed \
    --name "PulseTelemetry_1.0.0" \
    --specpath "build" \
    --distpath "releases" \
    --icon "$(pwd -W)/assets/icon.ico" \
    --hidden-import "pynvml" \
    --add-data "$(pwd -W)/Open_Sans;Open_Sans" \
    --add-data "$(pwd -W)/assets;assets" \
    app.py
```

The resulting binary will be placed inside the `releases/` folder.

---

## 🧪 Built-in Utilities

### 1. GPU Stress Tester (`gpu_stress.py`)

A lightweight, zero-dependency CUDA driver stress utility utilizing pure Python `ctypes` (`libcuda.so.1` / `nvcuda.dll`). It allocates dedicated VRAM buffers and pumps asynchronous memory operations to test GPU telemetry under heavy load without needing external benchmarking software:

```bash
python gpu_stress.py
```

*(Press `Ctrl+C` to terminate the stress test and cleanly release allocated VRAM.)*

### 2. Icon Generator (`generate_icons.py`)

Generates high-resolution application branding icons (`icon.png` and multi-layered `icon.ico` from 16x16 up to 256x256) programmatically using PyQt6 vector paths:

```bash
python generate_icons.py
```

---

## ⚙️ Configuration & Settings

Click the **⚙ (Gear)** icon in the top header to configure:

- **Pin Window (Always on Top)**: Toggle keeping the window persistently above other active applications.
- **Theme Selection**: Switch on the fly between `Dark`, `OLED Black`, and `Light`.
- **Font Scale**: Dynamic UI font scaling slider (`10pt` - `18pt`).
- **Telemetry Frequency**:
  - `0.5s` (High Speed / Responsive)
  - `1.0s` (Normal - Default)
  - `2.0s` (Battery Saver / Low Overhead)

User preferences are persisted across application restarts using `QSettings`.

---

## 📄 License

This project is licensed under the MIT License. The bundled Open Sans fonts are distributed under the [SIL Open Font License 1.1](Open_Sans/OFL.txt).
