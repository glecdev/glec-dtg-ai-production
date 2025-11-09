# 3D Truck Models

## 📦 Model Files (Not Included in Git)

Due to file size limitations, 3D model files are not included in this repository.

### Available Models

| File Name | Size | Description |
|-----------|------|-------------|
| `T6DZCYCBHTUL84Q6I1B5HXWR5.glb` | 843 KB | Volvo truck model (primary) |
| `XNLAAK0QA9Q0VS7TCLBMCUCTO.glb` | 1.9 MB | Alternative truck design |
| `71FPHAHJXY9GYZA1FHF0SC1G5.glb` | 1.7 MB | Truck variant (detailed) |
| `ALY4HDWJZWM0UMGJGSV3MRD6O.glb` | 840 KB | Truck variant (compact) |
| `42UP3JGPDSXPMMETDJFZUZ9RQ.glb` | 228 KB | Lightweight truck model |

**Total Size**: ~5.5 MB

## 🎯 Features

- **Format**: GLB (GL Transmission Format Binary)
- **Compatibility**: Three.js, Babylon.js, Unity, Unreal Engine
- **Optimization**: Real-time rendering optimized
- **Materials**: PBR (Physically Based Rendering)
- **Textures**: Embedded in GLB files

## 🚀 Usage

### In HTML/JavaScript
```javascript
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

const loader = new GLTFLoader();
loader.load('models_3d/T6DZCYCBHTUL84Q6I1B5HXWR5.glb', (gltf) => {
    scene.add(gltf.scene);
});
```

### In Android WebView
```kotlin
// Load HTML with 3D viewer
webView.loadUrl("file:///android_asset/dtg-3d-viewer.html")

// Models are loaded from:
// file:///android_asset/models_3d/T6DZCYCBHTUL84Q6I1B5HXWR5.glb
```

## 📥 Obtaining Models

For access to the 3D model files:
1. Contact project maintainers
2. Models are available in local repository: `/Users/kevin/Downloads/GLEC DTG AI/3d-truck-implementation/truck-assets/`
3. Alternative: Use free truck models from [Sketchfab](https://sketchfab.com/search?q=truck&type=models&features=downloadable)

## 🔧 Model Specifications

- **Vertices**: 10K - 50K per model
- **Triangles**: 20K - 100K per model
- **Texture Resolution**: 2K - 4K
- **Animation**: None (static models)
- **LOD (Level of Detail)**: Not included

---

**Note**: These models are optimized for the DTG 3D viewer dashboard and provide realistic truck visualization for the digital tachograph system.
