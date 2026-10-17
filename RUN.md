### To build for .deb

```Shell
chmod +x ./scripts/build_deb.sh
./scripts/build_deb.sh
```

### To install the build .deb

```Shell
sudo apt install ./releases/pulse-telemetry_1.0.0_amd64.deb
```

### To build for .exe

```Shell
uv run pyinstaller --noconfirm --onefile --windowed \
    --name "PulseTelemetry_1.0.0" \
    --specpath "build" \
    --distpath "releases" \
    --icon "assets/icon.ico" \
    --collect-all "pynvml" \
    --add-data "Open_Sans;Open_Sans" \
    --add-data "assets;assets" \
    app.py
```
