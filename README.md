# 📺 TV Slideshow System (DevOps Portfolio Project)

## 🚀 Overview

This project demonstrates a lightweight **real-time distributed system**
designed for local networks, simulating key DevOps concepts such as
service communication, event-driven architecture, and system
orchestration.

It allows centralized control of multiple display clients (TV screens)
through a web-based interface.

------------------------------------------------------------------------

## 🧠 DevOps Concepts Demonstrated

-   Event-driven architecture (Server-Sent Events)
-   Stateless service design with shared in-memory state
-   REST API design
-   Real-time system synchronization
-   Network-based service discovery (local IP access)
-   Separation of concerns (control vs display clients)
-   Lightweight service deployment (no dependencies)

------------------------------------------------------------------------

## 🏗️ Architecture

              ┌──────────────────────┐
              │   Control Panel      │
              │  (Web Client)        │
              └─────────┬────────────┘
                        │ HTTP / REST
                        ▼
              ┌──────────────────────┐
              │   Python Server      │
              │  (State + API + SSE) │
              └─────────┬────────────┘
                        │ SSE (Real-time events)
                        ▼
              ┌──────────────────────┐
              │   TV Display Client  │
              │  (Fullscreen UI)     │
              └──────────────────────┘

------------------------------------------------------------------------

## ⚙️ Tech Stack

-   Backend: Python (Standard Library)
-   Frontend: HTML, CSS, JavaScript
-   Communication: HTTP + SSE (Server-Sent Events)
-   Deployment: Local network service

------------------------------------------------------------------------

## 📦 Features

-   Real-time image slideshow
-   Remote control (play, pause, next, previous)
-   Dynamic configuration (delay control)
-   Live alert messaging system
-   Multi-client synchronization
-   Zero external dependencies

------------------------------------------------------------------------

## ▶️ Run the Project

``` bash
python server.py
```

Access:

-   Control Panel → http://localhost:8765/control
-   TV Display → http://localhost:8765/tv

------------------------------------------------------------------------

## 🔌 API Design

  Endpoint       Method   Description
  -------------- -------- -------------------------
  /api/images    POST     Upload images
  /api/delay     POST     Update slideshow timing
  /api/alert     POST     Send alert
  /api/command   POST     Playback control
  /events        GET      Real-time stream

------------------------------------------------------------------------

## 🔄 Real-Time Communication

This system uses **Server-Sent Events (SSE)** instead of polling,
enabling:

-   Low-latency updates
-   Reduced network overhead
-   Simple real-time streaming

------------------------------------------------------------------------

## 🧩 Why This Project Matters (DevOps Perspective)

This project simulates real-world patterns such as:

-   Microservice-like communication
-   Control plane vs data plane separation
-   Stateless API with shared runtime state
-   Event broadcasting to multiple clients
-   Lightweight service deployment without containers

------------------------------------------------------------------------

## 🔮 Next Steps (Planned Improvements)

-   Docker containerization
-   Reverse proxy (NGINX)
-   Authentication layer
-   Persistent storage (Redis / DB)
-   Cloud deployment (AWS / GCP)

------------------------------------------------------------------------

## 👨‍💻 Author

Gustavo Carvalho\
DevOps / Cloud Engineer (in transition)
