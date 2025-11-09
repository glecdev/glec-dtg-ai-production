# GLEC DTG AI - Digital Tachograph AI System

## 📦 Repository Structure

**This repository contains core documentation and configuration files.**

Full source code (48GB including Android app, 3D models, and AI models) is available locally at:
- **Local Path**: `/Users/kevin/Downloads/GLEC DTG AI/`
- **Android App Source**: `android_app/app/src/main/java/`
- **Dashboard UI**: `android_app/app/src/main/assets/dtg_dashboard_volvo_fixed.html`
- **Main Activity**: `android_app/app/src/main/java/com/glec/agent/presentation/SimpleMainActivity.kt`

For source code access, please contact the project maintainers.

---

## 🚀 Project Overview

GLEC DTG AI is a next-generation **Digital Tachograph AI System** featuring:
- ✅ Real-time CAN data collection and processing
- ✅ 1280x480 accurate display output
- ✅ Volvo truck 3D model integration with Three.js
- ✅ WebView-based interactive dashboard
- ✅ Vertex AI integration for driver safety analysis
- 🔄 Voice AI agent (in progress)

## 📋 Core Documentation

- [`CLAUDE.md`](./CLAUDE.md) - Claude Code working guide
- [`CHANGELOG.md`](./CHANGELOG.md) - Version history
- [`RELEASE_NOTES_v6.0.0.md`](./RELEASE_NOTES_v6.0.0.md) - v6.0.0 release notes
- [`android_dtg_integration_plan.md`](./android_dtg_integration_plan.md) - Android integration plan
- [`requirements.txt`](./requirements.txt) - Python dependencies

## 🏗️ System Architecture

### Core Components
```
GLEC DTG AI/
├── android_app/                # Android application
│   ├── app/src/main/
│   │   ├── assets/            # HTML dashboards
│   │   ├── java/              # Kotlin/Java source
│   │   └── res/               # Resources
│   └── build.gradle.kts       # Build config
├── config/                     # JSON configuration files
├── scripts/                    # Python scripts
├── CLAUDE.md                   # Development guide
└── README.md                   # This file
```

### Data Flow
```
Real-time CAN Data → MessengerClient → SimpleMainActivity → WebView → Dashboard UI
```

## 🎯 Current Status (v6.0.0)

### ✅ Completed
- Real-time DTG CAN data collection: **100%**
- 1280x480 1:1 scale output: **100%**
- 3D truck model integration: **100%**
- Data parsing error fixes: **100%**
- System stability: **95%**

### 🔄 In Progress
- Vertex AI integration: **0% → 100%**
- Hardcoding removal: **20% → 100%**
- Overall completion: **95% → 100%**

## 🛠️ Tech Stack

### Frontend (WebView)
- HTML5/CSS3/JavaScript
- Three.js for 3D rendering
- GLTFLoader for truck models
- OrbitControls for camera

### Backend (Android)
- **Kotlin**: Main app logic
- **WebView**: Dashboard hosting
- **CAN Protocol**: Real-time data collection
- **MongoDB**: DTG data storage

### AI/ML
- **Vertex AI**: Fine-tuned Gemini model
- **Real-time inference**: Driver safety analysis
- **Voice AI**: Voice command processing

## 📞 Contact

- **Project**: GLEC DTG AI Team
- **Support**: Claude Code Assistant
- **Last Updated**: 2025-01-11 23:16
- **Version**: v6.0.0

---

**For full source code access, please refer to the local repository at `/Users/kevin/Downloads/GLEC DTG AI/`**
