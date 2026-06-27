# 📺 TV Slideshow

A lightweight, zero-dependency local network slideshow system. Run a Python server, open the display on any screen, and control everything — images, videos, timing, and live alerts — from any device on your Wi-Fi.

---

## ✨ Features

- **Mixed media slideshows** — images and videos in the same playlist
- **Wide format support** — JPG, PNG, GIF, WEBP, BMP, SVG, AVIF, TIFF, HEIC and videos MP4, MOV, AVI, MKV, WEBM, M4V and more
- **Up to 50 files** per session
- **Framing editor** — zoom, pan, fit mode and background color for each image or video individually
- **Live alert system** — send timed or pinned messages that overlay the slideshow instantly
- **Real-time control** — all changes sync to the display via SSE with no page reload
- **No internet required** — runs entirely on your local network
- **No dependencies** — pure Python 3.7+, no pip install needed
- **Multi-language UI** — Portuguese, French and English

---

## 🗂 File Structure

```
TVSlideshow/
├── server.py          # Python HTTP server + SSE event broadcaster
├── tv-control.html    # Control panel (open on phone, tablet, or PC)
└── tv-display.html    # Display screen (open on the TV/monitor)
```

All three files must be in the same folder.

---

## 🚀 Quick Start

### 1. Start the server

**Windows**
```cmd
cd C:\path\to\TVSlideshow
python server.py
```

**macOS / Linux**
```bash
cd ~/path/to/TVSlideshow
python3 server.py
```

The terminal will print your local IP:
```
╔══════════════════════════════════════════════════╗
║           📺  TV SLIDESHOW SERVER               ║
╠══════════════════════════════════════════════════╣
║  Control Panel  → http://192.168.1.10:8765/control
║  TV Display     → http://192.168.1.10:8765/tv
╚══════════════════════════════════════════════════╝
```

### 2. Open the TV display

On the machine connected to the TV, open a browser and go to:
```
http://localhost:8765/tv
```
Press **F11** for fullscreen.

### 3. Open the control panel

On any device on the same Wi-Fi network:
```
http://192.168.1.10:8765/control   ← use YOUR server IP
```

The network badge in the top right turns **green** when connected.

---

## 🖥 Requirements

| Item | Requirement |
|------|-------------|
| Python | 3.7 or higher |
| Browser | Chrome, Edge or Firefox (recent version) |
| Network | All devices on the same Wi-Fi or LAN |
| Dependencies | None — standard library only |

---

## 🎛 Control Panel — Features

### Slideshow
- Upload images and videos by clicking the drop zone or dragging files onto it
- Thumbnails appear immediately; videos show a **VID** badge
- Click **✏** on any thumbnail to open the framing editor

### Framing Editor
- Available for both images and videos
- **Fit modes:** Cover · Contain · Stretch · Original
- **Zoom** slider (10% – 300%)
- **Position X / Y** sliders to pan the content
- **Background color** for letterbox/pillarbox areas
- Changes apply instantly to the TV display

### Timing
- Interval slider from **1s to 60s** between slides
- Previous / Pause / Play / Next controls
- Pause stops auto-advance; videos continue looping

### Alert System
- Type a message and choose a duration (0 = infinite)
- **Send** — displays the alert for the set duration, then auto-closes
- **Pin** — permanent overlay, only removed manually via Cancel
- **Cancel** — removes the alert from the TV immediately

---

## 🌐 How It Works

```
┌─────────────────────────────┐
│   PC running server.py      │
│   (e.g. 192.168.1.10:8765)  │
│                             │
│  serves /control            │
│  serves /tv                 │
│  holds shared state         │
└──────────┬──────────────────┘
           │  Local Wi-Fi / LAN
     ┌─────┴──────┐
     ▼            ▼
  Phone/PC      Laptop on TV
  /control      /tv
```

The server uses **Server-Sent Events (SSE)** to push updates to the display in real time. No WebSocket, no polling, no external services.

---

## 🔧 Troubleshooting

| Symptom | Fix |
|---------|-----|
| Badge stays grey / "LOCAL" | Make sure you're accessing via the IP URL (`192.168.x.x:8765/control`), not by opening the HTML file directly |
| Upload works but TV doesn't update | Reload the TV page (F5) and check the server terminal for errors |
| Video doesn't play on TV | Videos use a temporary browser URL — don't move or delete the source file while the session is active |
| "Connection refused" in browser | The server is not running. Re-run `python3 server.py` |
| Port 8765 already in use | Edit `server.py`, change `PORT = 8765` to another port (e.g. `8766`) |
| Windows Firewall blocking access | Allow Python through the firewall: Settings → Windows Firewall → Allow an app → Python |

---

## 📡 API Reference

The server exposes a simple REST API on port 8765.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tv` | Serves tv-display.html |
| GET | `/control` | Serves tv-control.html |
| GET | `/api/state` | Returns current server state as JSON |
| GET | `/api/images` | Returns all uploaded images/videos |
| POST | `/api/images` | Updates the slideshow content |
| POST | `/api/delay` | Sets the slide interval (ms) |
| POST | `/api/alert` | Sends or pins an alert |
| POST | `/api/alert/clear` | Clears the current alert |
| POST | `/api/command` | Sends playback command (next/prev/pause/play) |
| GET | `/events` | SSE stream for real-time updates |

---

## 📋 Supported Formats

**Images:** JPG · JPEG · PNG · GIF · WEBP · BMP · SVG · AVIF · TIFF · TIF · HEIC · HEIF

**Videos:** MP4 · MOV · AVI · MKV · WEBM · M4V · WMV · FLV · 3GP · TS · MTS · M2TS · OGV · MPEG · MPG

---

## 📄 License

MIT License — free to use, modify and distribute.
