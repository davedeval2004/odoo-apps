# Web Camera Widget — Odoo 19

**Author:** Flowient Technology ([flowient.in](https://flowient.in))
**Version:** 19.0.1.0.0
**License:** LGPL-3
**Price:** $5.00 USD

## Overview

Capture images directly from your device's camera inside any Odoo 19 form view — no plugins, no file uploads, no switching apps. Works on desktop webcams and mobile cameras (front + rear).

## Features

- **One-click capture** — Camera icon button appears on any image field using `widget="camera"`.
- **Live preview** — Real-time camera feed in a dialog before you snap.
- **Retake / Confirm workflow** — Preview your capture, retake if needed, then confirm.
- **Front / Rear camera toggle** — Switch cameras on mobile with a single tap.
- **Cross-platform** — Chrome, Firefox, Safari, Edge, iOS, Android, Linux, Windows.
- **Responsive** — Works on desktop and mobile viewports.
- **Zero dependencies** — Uses the browser's native `getUserMedia` API. No external libraries.

## Installation

1. Copy `camera_capture_widget` folder into your Odoo 19 custom addons directory.
2. Restart the Odoo server.
3. Activate developer mode → Apps → Update Apps List.
4. Search for "Web Camera Widget" and click Install.

## Usage

### Option 1: XML View Definition

Add `widget="camera"` to any Binary or Image field in a form view:

```xml
<field name="image_1920" widget="camera"/>
```

### Option 2: Odoo Studio

Open the form view in Studio, click on the image field, and set the Widget to **Camera Image**.

### Built-in Demo

This module includes a view override that automatically applies the camera widget to the **Contact form** image field. After installation, open any contact and you'll see the camera button on the profile photo.

## Technical Details

| Item | Detail |
|------|--------|
| Technical name | `camera_capture_widget` |
| Odoo version | 19.0 |
| Python dependencies | None |
| JS framework | OWL 2 (Odoo 19 native) |
| Template strategy | `t-inherit-mode="primary"` on `web.ImageField` |
| Field types | Binary (`binary`) |

### Architecture

```
camera_capture_widget/
├── __init__.py
├── __manifest__.py
├── static/
│   ├── description/
│   │   ├── banner.png
│   │   ├── icon.png
│   │   └── index.html
│   └── src/
│       ├── js/
│       │   └── camera_capture_widget.js      # OWL components (CameraDialog + CameraImageField)
│       ├── scss/
│       │   └── camera_capture_widget.scss     # Widget and dialog styles
│       └── xml/
│           └── camera_capture_widget.xml      # OWL templates
├── views/
│   └── res_partner_views.xml          # Demo: applies widget to Contact form
└── README.md
```

### Key Components

- **`CameraDialog`** — OWL Component that manages the camera stream, capture, retake, and confirm flow. Uses `navigator.mediaDevices.getUserMedia()`.
- **`CameraImageField`** — Extends `ImageField` with a camera trigger button. Registered as the `camera` field widget.
- **Template inheritance** — Uses `t-inherit-mode="primary"` to create a new template derived from `web.ImageField` (not `extension`, which would modify the original).

## Browser Requirements

The camera widget requires HTTPS in production (browsers block `getUserMedia` on insecure origins). Localhost is exempt during development.

## Support

For bug reports or questions:
- Email: info@flowient.in
- Website: [flowient.in](https://flowient.in)

---

© 2025 Flowient Technology. All rights reserved.
