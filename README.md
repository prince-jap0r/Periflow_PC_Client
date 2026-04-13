# Periflow PC Client

> **Remote control your Windows PC from your Android phone over local Wi-Fi**

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

## 📋 Overview

**Periflow** is a lightweight, open-source system for controlling your Windows PC using an Android phone over a local network. Stream your camera and microphone to your phone, and control your PC remotely with touch gestures and keyboard input—all without requiring an internet connection or any complex setup.

Perfect for:
- 🎤 Remote presentations
- 🖱️ Wireless keyboard/mouse replacement
- 📱 Mobile device testing
- 🎬 Media control from the couch
- 🎮 Game console-like remote control

## ✨ Features

- **📹 Live Video Streaming** - Capture PC screen and stream to Android device
- **🔊 Audio Streaming** - Stream PC audio to phone (UDP/TCP transport)
- **⌨️ Remote Input Control** - Mouse, keyboard, and text input from phone
- **🔌 Zero Internet Required** - Works entirely on local Wi-Fi/LAN
- **⚡ Low Latency** - Direct network communication for responsive control
- **📦 Single-File Executable** - No Python installation or dependencies needed
- **🔐 Local Network Safe** - Only accessible within your private network
- **⚙️ Settings Persistence** - Save your preferred resolution, audio quality, and frame rate
- **🛡️ Windows Firewall Integration** - Automatic firewall rule management (Admin mode)
- **📊 Live Diagnostics** - Real-time logging and status monitoring

## 🏗️ How It Works

### System Architecture

```
┌─────────────────────┐                    ┌──────────────────────┐
│  Android Device     │   Wi-Fi/LAN        │  Windows PC          │
│  (Periflow App)     │◄───────────────►│  (Periflow Client)  │
│                     │   TCP (Control)    │                      │
│                     │   UDP (Audio)      │  - Mouse/Keyboard   │
│                     │                    │  - Camera/Mic Input │
└─────────────────────┘                    └──────────────────────┘
        │                                           │
        │  Send:                                    │  Capture:
        ├─ Touch Input                              ├─ Video Frames (OBS Virtual Camera)
        ├─ Keyboard Events                          ├─ Audio PCM (VB-CABLE)
        └─ Control Commands                         └─ Input Events

```

### Communication Protocol

**Framed Message Format:**
```
[4-byte length] + [JSON Metadata] + [Binary Body]
```

**Handshake (TCP):**
```json
Client:
{
  "type": "handshake",
  "token": "PERIFLOW_CONNECT",
  "client_name": "Periflow Android"
}

Server ACK:
{
  "type": "handshake_ack",
  "accepted": true,
  "server_version": "1.0.0",
  "protocol_version": 1,
  "audio_transport": "udp",
  "audio_port": 5001,
  "supported_resolutions": ["480p", "720p", "1080p"],
  "supported_fps": [15, 24, 30]
}
```

**Message Types:**
- `video_frame` - JPEG encoded video data
- `audio_frame` - PCM audio data
- `mouse_move` - Absolute or relative mouse position
- `mouse_click` - Mouse button press/release
- `mouse_scroll` - Scroll wheel events
- `key_press` / `key_release` - Keyboard input
- `text_input` - Direct text insertion
- `ping` / `pong` - Keep-alive mechanism

## 🚀 Getting Started

### Prerequisites

**PC Side (Windows):**
- Windows 10 or later
- (Optional but recommended) [OBS Virtual Camera](https://obsproject.com/) - for video streaming
- (Optional but recommended) [VB-CABLE](https://vb-audio.com/Cable/) - for audio streaming

**Android Side:**
- Android 6.0 or later
- Periflow Android app (available separately)

**Network:**
- Both devices on the same Wi-Fi network (LAN/local network only)
- Ports 5000 (TCP) and 5001 (UDP) accessible on the PC

### Installation (PC)

1. **Download** the latest `Periflow_PC.exe` from [Releases](https://github.com/yourusername/Periflow_PC_Client/releases)
2. **Run** the executable (no installation required)
3. **Allow firewall exceptions** if prompted by Windows Defender
4. The UI will display your PC's IP address and port

### Usage (PC Client)

1. **Start the Client:**
   - Launch `Periflow_PC.exe`
   - The app will auto-detect your local IP address
   - Note the endpoint displayed (e.g., `192.168.1.100:5000`)

2. **Configure Settings (Optional):**
   - **Resolution:** Choose 480p, 720p, or 1080p
   - **Frame Rate:** Select 15, 24, or 30 FPS
   - **Audio Quality:** Mono or Stereo at 22.05kHz or 44.1kHz
   - **Audio Transport:** UDP (recommended) or TCP fallback
   - **Enable/Disable:** Toggle video, audio, and control features

3. **Manage Firewall (Windows Admin):**
   - Click "Configure Firewall" to automatically add necessary rules
   - Or manually add rules for ports 5000 (TCP) and 5001 (UDP)

4. **Monitor Live:**
   - Watch the live log for connection status
   - Check diagnostic info (FPS, resolution, audio status)
   - Verify client connection and address

### Usage (Android App)

1. **Connect:**
   - Enter your PC's IP address and port (shown in Periflow desktop app)
   - Tap "Connect"

2. **Control:**
   - Swipe to move mouse
   - Tap to click
   - Two-finger swipe to scroll
   - Use keyboard for text input

3. **Stream:**
   - View live video feed from your PC
   - Hear audio from your PC through phone speakers

## ⚙️ System Requirements

| Component | Requirement |
|-----------|------------|
| **OS** | Windows 10 or later |
| **RAM** | 512 MB minimum (1 GB recommended) |
| **Python** | None (bundled in .exe) |
| **Network** | WiFi/LAN, both devices on same network |
| **Ports** | 5000 (TCP), 5001 (UDP) - customizable |

## 🔐 Security Considerations

### ⚠️ Important Warnings

**NETWORK SCOPE:**
- Periflow operates **only on local networks** (LAN/WiFi)
- Do NOT expose ports 5000 or 5001 to the internet (Port Forwarding)
- Should only be trusted within your home/office network

**AUTHENTICATION:**
- Currently uses a simple token-based handshake (`PERIFLOW_CONNECT`)
- No user/password authentication
- Assumes all devices on your local network are trusted

**ATTACK SURFACE:**
- Any device on your network can attempt to connect
- No end-to-end encryption (relies on network isolation)
- Mouse/keyboard control could be abused to launch malware

### 🛡️ Security Recommendations

1. **Use Private Networks Only:**
   - Disable auto-connect on public WiFi
   - Only connect on home/office networks you trust

2. **Firewall Configuration:**
   - Keep Windows Firewall enabled
   - Restrict ports 5000/5001 to local subnet only
   - Run as Administrator for auto firewall rules

3. **Network Isolation:**
   - Use a separate guest network if available
   - Don't connect on networks you don't fully trust
   - Consider using a VPN on untrusted networks

4. **Physical Security:**
   - Don't leave PC unattended with active Periflow session
   - Monitor the live log for unexpected connections

### Future Security Enhancements

- [ ] PIN-based pairing system
- [ ] Device fingerprinting
- [ ] Message signing/verification
- [ ] Rate limiting on input events
- [ ] Connection timeout and auto-disconnect
- [ ] Optional TLS encryption for LAN
- [ ] User authentication system

## 📦 Architecture & Components

### Core Modules

| Module | Purpose |
|--------|---------|
| `server.py` | TCP server, connection management, message dispatch |
| `protocol.py` | Framed message encoding/decoding, handshake logic |
| `services/` | Video, Audio, Control workers (queue-based) |
| `ui.py` | Tkinter desktop UI, settings, live logging |
| `config.py` | Settings persistence (%APPDATA%\Periflow\settings.json) |
| `models.py` | Data structures, presets, settings |
| `system.py` | Windows integration (Firewall, admin check, IP resolution) |

### Service Architecture

Each service runs in a separate queue-based worker thread:
- **VideoService**: Captures frames, handles encoding
- **AudioService**: Listens for audio packets, manages playback
- **ControlService**: Processes mouse/keyboard events

This prevents network I/O from blocking media processing.

### Settings Persistence

Settings are saved to:
```
%APPDATA%\Periflow\settings.json
```

Example:
```json
{
  "server_port": 5000,
  "audio_port": 5001,
  "audio_transport": "udp",
  "resolution": "720p",
  "fps": 24,
  "audio_quality": "Mono 44.1 kHz"
}
```

## 🔧 Building from Source

### Prerequisites

- Python 3.9 or later
- pip or uv package manager

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/Periflow_PC_Client.git
   cd Periflow_PC_Client
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app:**
   ```bash
   python main.py
   ```

### Building Standalone EXE

Using PyInstaller:
```bash
PyInstaller Periflow_PC.spec
```

Output: `dist/Periflow_PC.exe`

## 📝 Development

### Running Tests

```bash
python -m pytest tests/
```

### Code Structure

```
Periflow_PC_Client/
├── periflow/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── config.py            # Settings management
│   ├── models.py            # Data structures
│   ├── protocol.py          # Message protocol
│   ├── server.py            # TCP server
│   ├── ui.py                # Tkinter UI
│   ├── system.py            # Windows integration
│   ├── resources.py         # Asset locator
│   └── services/
│       ├── video.py         # Video streaming
│       ├── audio.py         # Audio streaming
│       ├── control.py       # Input control
│       └── _worker.py       # Base worker thread
├── tests/                   # Unit tests
├── build_assets/            # UI assets
├── requirements.txt         # Dependencies
└── README.md               # This file
```

### Development Workflow

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make changes and test locally: `python main.py`
3. Run tests: `pytest`
4. Submit a pull request with a clear description

## 🐛 Troubleshooting

### App Won't Start

- Ensure you have Windows 10 or later
- Check that Python 3.9+ is installed (if building from source)
- Look for error messages in the console

### Can't Connect from Android

1. Verify both devices are on **same Wi-Fi network**
2. Check that PC endpoint is **correct** (shown in Periflow)
3. Confirm **ports 5000/5001 are open** (firewall may block)
4. Try disabling Windows Firewall temporarily to test
5. Check device firewall (third-party antivirus software)

### Audio/Video Not Streaming

- **Video:** Install [OBS Virtual Camera](https://obsproject.com/)
- **Audio:** Install [VB-CABLE](https://vb-audio.com/Cable/)
- Configure the devices in audio/video settings

### Firewall Issues

- Run Periflow as Administrator for auto-configuration
- Manually check Windows Firewall rules:
  ```powershell
  netsh advfirewall firewall show rule name="Periflow*"
  ```

### Performance Issues

- **High CPU:** Reduce resolution or frame rate
- **Stuttering:** Switch to lower resolution (480p) or lower FPS (15)
- **Audio latency:** Switch audio transport to UDP

## 📋 Future Roadmap

- [ ] PIN-based secure pairing
- [ ] Clipboard sharing
- [ ] File transfer
- [ ] Multi-client support
- [ ] iOS app
- [ ] Web dashboard
- [ ] VPN tunnel support
- [ ] End-to-end encryption option
- [ ] Device sleep/wake control
- [ ] Screen recording feature

## 🤝 Contributing

We welcome contributions! To contribute:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes with clear commit messages
4. **Test** thoroughly
5. **Submit** a Pull Request with description

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024-2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

## 🙋 Support & FAQ

### Q: Is this safe to use?

**A:** Periflow is designed for trusted local networks only. Do not expose to the internet. It's suitable for home/office environments where all network devices are trusted.

### Q: Can I use this over internet/4G?

**A:** Not recommended. Periflow is built for low-latency local networks. Internet connectivity will cause severe lag and security risks.

### Q: Does it work on Mac/Linux?

**A:** Currently Windows-only. The PC client uses Windows-specific APIs (pynput, ctypes). Mac/Linux ports are possible future enhancements.

### Q: Can multiple phones connect?

**A:** Not in this version. Periflow supports one active client per server instance.

### Q: How do I change ports?

**A:** Edit the settings in the Periflow UI or manually modify `%APPDATA%\Periflow\settings.json`.

### Q: What dependencies are required?

**A:** The .exe bundle includes all dependencies. From source, install `requirements.txt`:
- opencv-python-headless
- numpy
- Pillow
- PyAudio
- pynput
- pyvirtualcam

## 📧 Contact

- **Issues:** [GitHub Issues](https://github.com/yourusername/Periflow_PC_Client/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/Periflow_PC_Client/discussions)

## 🙏 Acknowledgments

- **OBS Project** - Virtual camera streaming
- **VB-Audio** - Virtual audio cable
- **pynput** - Cross-platform input simulation
- Built with ❤️ for the open-source community

---

**Made with ❤️ by the Periflow Team**

**Last Updated:** April 2026  
**Current Version:** 1.0.0
