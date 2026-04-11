# Periflow - Product Requirements Document (PRD)

**Version:** 1.1.0  
**Last Updated:** April 2026  
**Platform:** Android + Windows PC Client  

---

## 1. Project Overview

### 1.1 Product Summary
Periflow is a lightweight Android-to-PC remote control application that enables users to control their Windows computer using their Android phone's touchpad and keyboard over a local Wi-Fi network. The app streams touch input, keyboard events, and optional camera/microphone data to a PC server application.

### 1.2 Target Users
- PC users who want wireless remote control
- Presentations and media control scenarios
- Basic PC control without physical keyboard/mouse

### 1.3 Core Value Proposition
- **Zero setup** - No internet required, works on local Wi-Fi
- **Low latency** - Direct local network communication
- **Portable PC client** - Single .exe file, no Python installation needed

---

## 2. Technical Architecture

### 2.1 System Diagram
```
┌─────────────────┐              ┌─────────────────┐
│   Android      │  Wi-Fi/LAN     │   Windows PC   │
│   Periflow     │◄────────────►│   PC Client   │
│   App         │   TCP/UDP     │   (Python)    │
└─────────────────┘              └─────────────────┘
       │                                  │
       │  1. Touch Events                 │
       │  2. Keyboard Input           │
       │  3. Optional Audio         │
       │  (config only)            │
       ▼                         ▼
┌─────────────────┐              ┌─────────────────┐
│  AdMob Ads      │              │  Mouse/Keyboard│
│  (Monetization)│              │  Input Events │
└─────────────────┘              └─────────────────┘
```

### 2.2 Technology Stack

| Component | Technology |
|----------|-----------|
| Mobile App | Flutter 3.11+ |
| State Management | Provider |
| Networking | Socket (TCP + UDP) |
| Protocol | Custom binary framing |
| PC Client | Python (PyInstaller bundled) |
| Ads | Google AdMob SDK |

### 2.3 Network Configuration

| Setting | Default Value |
|---------|------------|
| TCP Control Port | 5000 |
| UDP Audio Port | 5001 |
| Protocol Version | 1 |
| Reconnect Delay | 5 seconds |
| Ping Interval | 4 seconds |

---

## 3. Feature Specification

### 3.1 Core Features (Current)

#### 3.1.1 Remote Control
- **Touchpad Mode**
  - Single finger: Mouse movement
  - Tap: Left click
  - Long press: Right click
  - Two-finger scroll: Mouse scroll
  
- **Keyboard Mode**
  - Text input relay to PC
  - Special keys: Enter, Tab, Esc, Arrow keys
  - Alt + key combinations

#### 3.1.2 Connection Management
- Manual IP entry (192.168.x.x format)
- Auto-scan for PC server on local subnet
- Auto-reconnect on Wi-Fi drop (enabled by default)
- Connection status indicator

#### 3.1.3 AdMob Integration
- **Active Ad Formats:**
  | Format | Unit ID | Placement |
  |-------|--------|----------|
  | Fixed Banner | `ca-app-pub-3940256099942544/6300978111` | Header area |
  | Interstitial | `ca-app-pub-3940256099942544/1033173712` | Preloaded, 2-min cooldown |
  | Rewarded | `ca-app-pub-3940256099942544/5224354917` | User-initiated |

- **Compliance:**
  - GDPR/UMP consent handling
  - Non-personalized ads only
  - No ads on startup/exit

### 3.2 PC Client Features

| Feature | Status |
|---------|-------|
| Remote Control | ✅ Active |
| Touchpad Input | ✅ Active |
| Keyboard Relay | ✅ Active |
| Video Stream | ⚠️ Config only (disabled) |
| Audio Stream | ⚠️ Config only (disabled) |

---

## 4. UI/UX Specification

### 4.1 Android App Layout

```
┌────────────────────────────────────────┐
│  [Icon]  Periflow              │ ← Header (compact)
│  ● Connected                   │
├────────────────────────────────────────┤
│  [Ad Banner]                  │ ← AdMob Banner
├────────────────────────────────────────┤
│  ┌──────────────────────────┐  │
│  │ Connection Card       │  │
│  │ [IP:Port Input]     │  │
│  │ [Connect Button]    │  │
│  └──────────────────────────┘  │
│                                │
│  ┌──────────────────────────┐  │
│  │ Touchpad / Keyboard   │  │ ← Main Control
│  │ [Mode Toggle]      │  │
│  └──────────────────────────┘  │
└────────────────────────────────────────┘
```

### 4.2 Visual Design

| Element | Value |
|---------|-------|
| Primary Color | `#2F7CFF` (Blue) |
| Accent Color | `#76A5FF` (Light Blue) |
| Background | `#0C0E13` (Dark) |
| Surface | `#17181D` (Dark Panel) |
| Connected Status | `#49D76B` (Green) |
| Disconnected Status | `#FF6B7C` (Red) |
| Typography | Space Grotesk |

### 4.3 PC Client UI

- Standard Tkinter window (820x620)
- Server Status card with endpoint display
- Network configuration (TCP/UDP ports)
- Event log with timestamps
- Start/Stop server controls

---

## 5. Android Permissions

| Permission | Purpose |
|-----------|---------|
| `INTERNET` | TCP/UDP communication |
| `ACCESS_NETWORK_STATE` | Wi-Fi status check |
| `ACCESS_WIFI_STATE` | Local IP discovery |
| `CHANGE_WIFI_MULTICAST_STATE` | Subnet scanning |
| `CAMERA` | Future video streaming |
| `RECORD_AUDIO` | Future audio streaming |
| `WAKE_LOCK` | Keep alive during stream |
| `FOREGROUND_SERVICE` | Background operation |
| `FOREGROUND_SERVICE_CAMERA/MICROPHONE` | Android 14+ |
| `POST_NOTIFICATIONS` | Android 13+ |

---

## 6. File Structure

```
Periflow/
├── pubspec.yaml                    # Flutter dependencies
├── android/
│   └── app/src/main/
│       └── AndroidManifest.xml  # Permissions
├── lib/
│   ├── main.dart                # Entry point
│   ├── config.dart             # App & AdMob config
│   └── app/
│       ├── app_controller.dart      # State management
│       ├── models.dart            # Data models
│       ├── app_theme.dart        # Dark theme
│       ├── periflow_app.dart    # MaterialApp
│       ├── screens/
│       │   ├── home_shell.dart    # Main UI
│       │   └── root_screen.dart  # Router
│       └── services/
│           ├── admob_service.dart      # AdMob
│           ├── connection_service.dart  # Socket
│           └── periflow_protocol.dart # Binary protocol

Periflow_PC_Client/
├── main.py                     # Entry point
├── periflow/
│   ├── ui.py                 # Tkinter UI
│   ├── server.py             # TCP/UDP server
│   ├── models.py            # Settings
│   ├── config.py           # Config
│   ├── protocol.py        # Binary protocol
│   └���─ services/
│       ├── control.py       # Input injection
│       ├── audio.py       # Audio (disabled)
│       └── video.py       # Video (disabled)
├── Periflow_PC_Simple.spec   # PyInstaller spec
└── dist/
    └── Periflow_PC_Client.exe  # Portable exe
```

---

## 7. Known Limitations

### 7.1 Current Constraints
- **No video streaming** - UI exists but not implemented in PC client
- **No audio streaming** - UI exists but not implemented in PC client
- **No rewarded interstitial** - Config ready but needs UI button
- **No native ads** - Config ready but needs UI placement

### 7.2 Platform Constraints
- Android only (iOS not configured)
- Local Wi-Fi required (no internet remote)
- Same subnet required for auto-scan

---

## 8. AdMob Revenue Potential

### 8.1 Ad Format Coverage
| Format | Implementation | Revenue Potential |
|--------|---------------|-----------------|
| Banner | Header (always on) | Medium |
| Interstitial | Screen transitions | High |
| Rewarded | User-initiated | High |
| App Open | Not implemented | Medium |

### 8.2 Optimization Recommendations
1. Add Rewarded Interstitial button in settings
2. Implement App Open ads with native extension
3. Add Native ads in scroll areas
4. Consider rewarded video for full feature unlock

---

## 9. Build Commands

### 9.1 Android App
```bash
flutter clean
flutter pub get
flutter build apk --debug
flutter build apk --release
```

### 9.2 PC Client
```bash
python -m PyInstaller Periflow_PC_Simple.spec --noconfirm --clean
# Output: dist/Periflow_PC_Client.exe (~12MB)
```

---

## 10. Testing Checklist

- [ ] Connect to PC via IP
- [ ] Connect via auto-scan
- [ ] Touchpad mouse movement
- [ ] Touchpad tap (left click)
- [ ] Touchpad long press (right click)
- [ ] Keyboard text input
- [ ] Auto-reconnect on Wi-Fi drop
- [ ] AdMob banner loads
- [ ] AdMob interstitial shows
- [ ] PC Client exe runs without Python

---

## 11. Appendix: AdMob Unit IDs

### Android (Test IDs)
| Format | Unit ID |
|--------|--------|
| Banner | `ca-app-pub-3940256099942544/6300978111` |
| Interstitial | `ca-app-pub-3940256099942544/1033173712` |
| Rewarded | `ca-app-pub-3940256099942544/5224354917` |
| Rewarded Interstitial | `ca-app-pub-3940256099942544/5354046379` |
| Native | `ca-app-pub-3940256099942544/2247696110` |

### Production Notes
- Replace test IDs with real Ad Unit IDs before release
- Set up AdMob account and link to Google Play
- Configure payment details in AdMob console

---

*Document generated for Periflow v1.1.0*