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

### Code Style

This project uses:
- **Black** for code formatting
- **isort** for import sorting
- **mypy** for type checking

Run formatting:
```bash
black .
isort .
mypy periflow
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OBS Studio** for virtual camera support
- **VB-Audio** for virtual audio cable
- **PyInstaller** for creating standalone executables
- **All contributors** who have helped improve Periflow

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/Periflow_PC_Client/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/Periflow_PC_Client/discussions)
- **Email:** yourusername@example.com

---

<div align="center">
Made with ❤️ by the Periflow Team
</div>
