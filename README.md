# 🎥 Shinobi NVR — Docker + Cloudflare Tunnel + Microsoft 365 SSO

> **Enterprise-grade IP camera surveillance system** deployed via Docker, secured through Cloudflare Zero Trust, and authenticated with Microsoft 365 — no VPN required, no open firewall ports.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Phase 1 — Shinobi in Docker](#phase-1--shinobi-in-docker)
- [Phase 2 — Cloudflare Tunnel Setup](#phase-2--cloudflare-tunnel-setup)
- [Phase 3 — Microsoft 365 SSO via Cloudflare Access](#phase-3--microsoft-365-sso-via-cloudflare-access)
- [Phase 4 — Adding Axis Cameras (RTSP/ONVIF)](#phase-4--adding-axis-cameras-rtsponvif)
- [Phase 5 — User Access Management](#phase-5--user-access-management)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)
- [Author](#author)

---

## Overview

This project documents the deployment of **Shinobi NVR** (Network Video Recorder) as a containerized solution for enterprise environments. The setup provides:

- 📦 **Containerized deployment** via Docker Compose — portable and reproducible
- 🔒 **Zero Trust security** via Cloudflare Tunnel — no exposed ports or VPN needed
- 🔑 **Microsoft 365 SSO** — employees authenticate with their existing corporate credentials
- 📷 **Axis camera integration** — RTSP/ONVIF support for Axis IP camera systems
- 🌐 **Remote access** — secure access from anywhere without VPN

### Use Case

Designed for small-to-medium businesses already using **Microsoft 365** who want to deploy a professional surveillance system that integrates seamlessly with their existing identity infrastructure.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        EMPLOYEE DEVICE                          │
│                   browser → camera.company.com                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CLOUDFLARE ACCESS                            │
│              Zero Trust Identity Gateway                        │
│         Validates Microsoft 365 Login (@company.com)            │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Authorized only
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CLOUDFLARE TUNNEL                             │
│              Encrypted outbound tunnel (no open ports)          │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Internal tunnel
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ON-PREMISE SERVER                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Docker Compose Stack                        │   │
│  │   ┌─────────────┐   ┌──────────┐   ┌────────────────┐  │   │
│  │   │  Shinobi    │   │ MariaDB  │   │  cloudflared   │  │   │
│  │   │  NVR :8080  │◄──│ :3306    │   │  (tunnel agent)│  │   │
│  │   └──────┬──────┘   └──────────┘   └────────────────┘  │   │
│  └──────────┼────────────────────────────────────────────── ┘  │
│             │ RTSP :554 / ONVIF :80                            │
│  ┌──────────▼──────────────────────────────────────────────┐   │
│  │              IP Cameras (LAN)                            │   │
│  │   Axis M3046-V  ·  Axis M3106-L  ·  etc.               │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Server Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |
| CPU | 4 cores | 8 cores |
| RAM | 4 GB | 8 GB+ |
| Storage | 100 GB | 500 GB+ (for recordings) |
| Network | 100 Mbps LAN | 1 Gbps LAN |

### Required Accounts & Services

- ✅ **Cloudflare account** (Free plan is sufficient)
- ✅ **Domain registered in Cloudflare DNS** (e.g., `company.com`)
- ✅ **Microsoft 365 tenant** with admin access (for Azure AD app registration)
- ✅ **Docker & Docker Compose** installed on the server

### Install Docker on Ubuntu

```bash
# Install Docker
curl -fsSL https://get.docker.com | sudo sh

# Add your user to the docker group
sudo usermod -aG docker $USER

# Install Docker Compose plugin
sudo apt install -y docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

---

## Phase 1 — Shinobi in Docker

### 1.1 — Create the project directory

```bash
mkdir -p ~/shinobi-nvr && cd ~/shinobi-nvr
mkdir -p volumes/config volumes/videos volumes/db
```

### 1.2 — Create the Docker Compose file

```bash
nano docker-compose.yml
```

Paste the following content:

```yaml
version: "3.8"

services:
  shinobi:
    image: registry.gitlab.com/shinobi-systems/shinobi:latest
    container_name: shinobi_nvr
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - PLUGIN_KEYS={}
      - DB_HOST=shinobi_db
      - DB_PORT=3306
      - DB_USER=shinobi
      - DB_PASSWORD=shinobiSecurePass123
      - DB_NAME=shinobi
    volumes:
      - ./volumes/config:/config
      - ./volumes/videos:/opt/shinobi/videos
      - /etc/localtime:/etc/localtime:ro
    depends_on:
      shinobi_db:
        condition: service_healthy
    networks:
      - shinobi_net

  shinobi_db:
    image: mariadb:10.11
    container_name: shinobi_db
    restart: unless-stopped
    environment:
      - MYSQL_ROOT_PASSWORD=rootSecurePass123
      - MYSQL_DATABASE=shinobi
      - MYSQL_USER=shinobi
      - MYSQL_PASSWORD=shinobiSecurePass123
    volumes:
      - ./volumes/db:/var/lib/mysql
    healthcheck:
      test: ["CMD", "healthcheck.sh", "--connect", "--innodb_initialized"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - shinobi_net

  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: cloudflared_tunnel
    restart: unless-stopped
    command: tunnel --no-autoupdate run
    environment:
      - TUNNEL_TOKEN=${CLOUDFLARE_TUNNEL_TOKEN}
    networks:
      - shinobi_net

networks:
  shinobi_net:
    driver: bridge
```

### 1.3 — Create the environment file

```bash
nano .env
```

```env
CLOUDFLARE_TUNNEL_TOKEN=your_tunnel_token_here
```

> ⚠️ **Important:** Add `.env` to your `.gitignore` — never commit tokens to a repository.

```bash
echo ".env" >> .gitignore
```

### 1.4 — Start the stack

```bash
docker compose up -d
```

### 1.5 — Verify containers are running

```bash
docker compose ps
```

Expected output:
```
NAME               STATUS          PORTS
shinobi_nvr        Up              0.0.0.0:8080->8080/tcp
shinobi_db         Up (healthy)    3306/tcp
cloudflared_tunnel Up              
```

### 1.6 — Access Shinobi locally and create your account

Open your browser and navigate to:
```
http://localhost:8080/super
```

Default superuser credentials:
- **Email:** `admin@shinobi.video`
- **Password:** `admin`

> ⚠️ **Change the superuser password immediately after first login.**

Create a regular user account for daily use via **Accounts → Add**.

---

## Phase 2 — Cloudflare Tunnel Setup

### 2.1 — Log in to Cloudflare Zero Trust

Go to [https://one.dash.cloudflare.com](https://one.dash.cloudflare.com) and navigate to:

**Networks → Tunnels → Create a tunnel**

### 2.2 — Create the tunnel

1. Choose **Cloudflared** as the connector type
2. Name your tunnel: `shinobi-nvr`
3. Copy the **tunnel token** shown on screen
4. Paste it into your `.env` file as `CLOUDFLARE_TUNNEL_TOKEN`

### 2.3 — Configure the public hostname

In the tunnel configuration, add a **Public Hostname**:

| Field | Value |
|-------|-------|
| Subdomain | `cameras` |
| Domain | `company.com` |
| Service Type | `HTTP` |
| URL | `shinobi:8080` |

> The service URL uses the Docker container name `shinobi` because `cloudflared` runs in the same Docker network.

### 2.4 — Restart the stack to apply the token

```bash
docker compose down && docker compose up -d
```

### 2.5 — Verify tunnel is active

```bash
docker logs cloudflared_tunnel
```

You should see:
```
Registered tunnel connection connIndex=0 ...
```

Your Shinobi instance is now accessible at:
```
https://cameras.company.com
```

---

## Phase 3 — Microsoft 365 SSO via Cloudflare Access

### 3.1 — Register an app in Azure Active Directory

1. Go to [https://portal.azure.com](https://portal.azure.com)
2. Navigate to **Azure Active Directory → App registrations → New registration**
3. Fill in:
   - **Name:** `Shinobi NVR - Cloudflare Access`
   - **Supported account types:** `Accounts in this organizational directory only`
   - **Redirect URI:** `https://YOURTEAM.cloudflareaccess.com/cdn-cgi/access/callback`

> Replace `YOURTEAM` with your Cloudflare Zero Trust team name found at **Settings → Custom Pages**.

4. Click **Register**

### 3.2 — Collect Azure AD credentials

After registration, note down:
- **Application (client) ID** → this is your `Client ID`
- **Directory (tenant) ID** → this is your `Tenant ID`

Then go to **Certificates & secrets → New client secret**:
- Description: `Cloudflare Access`
- Expiry: `24 months`
- Copy the **Value** immediately → this is your `Client Secret`

### 3.3 — Configure API permissions

In your app registration, go to **API permissions → Add a permission**:
- **Microsoft Graph → Delegated permissions**
- Add: `email`, `openid`, `profile`
- Click **Grant admin consent**

### 3.4 — Add Microsoft 365 as Identity Provider in Cloudflare

In Cloudflare Zero Trust, go to:
**Settings → Authentication → Add new → Azure AD**

Fill in:

| Field | Value |
|-------|-------|
| Name | `Microsoft 365` |
| App ID | Your Azure Client ID |
| Client Secret | Your Azure Client Secret |
| Directory ID | Your Azure Tenant ID |

Click **Test** to verify the connection, then **Save**.

### 3.5 — Create an Access Policy for Shinobi

In Cloudflare Zero Trust, go to:
**Access → Applications → Add an application → Self-hosted**

Fill in:

| Field | Value |
|-------|-------|
| Application name | `Shinobi NVR` |
| Session duration | `8 hours` |
| Application domain | `cameras.company.com` |

Under **Policies → Add a policy**:

| Field | Value |
|-------|-------|
| Policy name | `Company Employees` |
| Action | `Allow` |
| Include | `Emails ending in` → `@company.com` |

Click **Save**.

### 3.6 — Test the full authentication flow

Open an incognito browser window and navigate to:
```
https://cameras.company.com
```

You should be redirected to the Microsoft 365 login page. After authenticating with a `@company.com` account, you will be forwarded to Shinobi.

---

## Phase 4 — Adding Axis Cameras (RTSP/ONVIF)

### 4.1 — Verify camera connectivity

Before adding cameras to Shinobi, test RTSP connectivity from the server:

```bash
# Test RTSP stream with ffprobe
docker run --rm jrottenberg/ffmpeg \
  -rtsp_transport tcp \
  -i "rtsp://root:PASSWORD@CAMERA_IP:554/axis-media/media.amp" \
  -t 1 -f null -
```

### 4.2 — Known RTSP URLs for Axis cameras

| Stream | URL |
|--------|-----|
| Main stream (H.264) | `rtsp://root:PASSWORD@CAMERA_IP:554/axis-media/media.amp` |
| Sub stream (lower res) | `rtsp://root:PASSWORD@CAMERA_IP:554/axis-media/media.amp?resolution=640x360` |
| MJPEG fallback | `http://root:PASSWORD@CAMERA_IP/axis-cgi/mjpg/video.cgi` |

### 4.3 — Add camera in Shinobi

In the Shinobi web interface:

1. Click **+** (Add Monitor) in the left sidebar
2. Fill in **Identity** section:
   - Mode: `Watch-Only` (or `Record` for recording)
   - Monitor ID: `axis-cam-01`
   - Name: `Axis M3046-V - Entrance`

3. Fill in **Input** section:
   - Input Type: `H.264 / H.265 / H.265+`
   - Automatic: `Yes`
   - Full URL Path: `rtsp://root:PASSWORD@CAMERA_IP:554/axis-media/media.amp`
   - RTSP Transport: `TCP`
   - ONVIF: `Yes`
   - ONVIF Port: `80`

4. Use the **Probe** button to verify the stream before saving

5. Click **Save**

### 4.4 — Verified stream specs (Axis M3046-V)

After a successful probe, you should see:

```
codec_name     : h264
width          : 2560
height         : 1440
display_ratio  : 16:9
profile        : High
```

---

## Phase 5 — User Access Management

### 5.1 — Access control layers

This setup has two independent access control layers:

```
Layer 1: Cloudflare Access
  └── Controls WHO can reach the Shinobi URL
  └── Enforced by Microsoft 365 login (@company.com)

Layer 2: Shinobi User Accounts  
  └── Controls WHAT each user can see/do inside Shinobi
  └── Managed in Shinobi Superuser Panel
```

### 5.2 — Create view-only user accounts in Shinobi

Access the superuser panel:
```
https://cameras.company.com/super
```

Click **Accounts → Add** and configure:

| Field | Recommended Value |
|-------|------------------|
| Email | employee's work email |
| Max Number of Cameras | `0` (cannot add cameras) |
| Permissions | `Watch Only` |
| Number of Days to keep Videos | `15` |

### 5.3 — Recommended permission matrix

| Role | Watch Live | View Recordings | Add Cameras | Manage Users |
|------|-----------|----------------|-------------|--------------|
| Security Team | ✅ | ✅ | ✅ | ❌ |
| Manager | ✅ | ✅ | ❌ | ❌ |
| Employee | ✅ | ❌ | ❌ | ❌ |
| IT Admin | ✅ | ✅ | ✅ | ✅ |

---

## Security Considerations

### ✅ What this setup protects

- **No open inbound firewall ports** — Cloudflare Tunnel uses outbound connections only
- **No VPN required** — access is secured at the identity layer
- **MFA enforced** — Microsoft 365 MFA applies automatically
- **Session expiry** — Cloudflare Access sessions expire after 8 hours
- **Domain-restricted access** — only `@company.com` accounts can authenticate

### ⚠️ Additional hardening recommendations

```bash
# 1. Restrict Shinobi to only accept connections from cloudflared container
# In docker-compose.yml, remove the ports mapping for shinobi:
#   Remove: ports: - "8080:8080"
# This makes Shinobi unreachable directly, only via the tunnel

# 2. Enable Ubuntu firewall
sudo ufw default deny incoming
sudo ufw allow ssh
sudo ufw enable
# Do NOT open port 8080 — cloudflared connects internally via Docker network

# 3. Keep containers updated
docker compose pull && docker compose up -d
```

### 🔐 Secrets management

- Never commit `.env` files or tokens to Git
- Rotate the Cloudflare Tunnel token periodically
- Rotate the Azure AD client secret before expiry (set a calendar reminder)
- Use strong, unique passwords for the MariaDB and Shinobi superuser

---

## Troubleshooting

### Tunnel not connecting

```bash
# Check cloudflared logs
docker logs cloudflared_tunnel --tail 50

# Verify the token in .env is correct and not expired
cat .env
```

### Shinobi not starting

```bash
# Check all container logs
docker compose logs --tail 50

# Check if database is healthy
docker compose ps shinobi_db
```

### Camera stream not loading

```bash
# Test RTSP directly from the host
ffprobe -rtsp_transport tcp \
  -i "rtsp://root:PASSWORD@CAMERA_IP:554/axis-media/media.amp"

# Check if camera is reachable
ping CAMERA_IP

# Verify RTSP port is open on camera
nc -zv CAMERA_IP 554
```

### Microsoft 365 login failing

- Verify the **Redirect URI** in Azure AD matches exactly: `https://YOURTEAM.cloudflareaccess.com/cdn-cgi/access/callback`
- Confirm **admin consent** was granted for Microsoft Graph permissions
- Check that the user's email domain matches the Cloudflare Access policy rule

---

## Project Structure

```
shinobi-nvr/
├── docker-compose.yml       # Main stack definition
├── .env                     # Secrets (never commit)
├── .gitignore               # Excludes .env and volumes
├── README.md                # This document
└── volumes/
    ├── config/              # Shinobi configuration (auto-generated)
    ├── videos/              # Camera recordings
    └── db/                  # MariaDB data (auto-generated)
```

---

## Author

**Gustavo Carvalho**
IT Infrastructure & Cloud Engineer | Montreal, Canada

- 15+ years in IT infrastructure
- Specializations: Azure, Docker, Fortinet, Intune, SentinelOne
- Currently transitioning into Cloud & DevOps roles

> *This project is part of my public portfolio documenting real-world enterprise IT solutions.*

---

## License

MIT License — feel free to use, adapt, and share with attribution.

---

*Built with: Shinobi NVR · Docker · Cloudflare Zero Trust · Microsoft Azure AD · Axis IP Cameras · Ubuntu Server*
