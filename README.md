# AirGallery - A Local Network Image Gallery Server

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-active-success.svg)]()

A beautiful, modern web-based image gallery server that runs locally on your network. Built with Python and zero external dependencies (except optional Pillow for advanced features), it serves images from any folder with an elegant dark-themed UI featuring lazy loading, color palette extraction, RGB histograms, and detailed metadata display.

Perfect for photographers, designers, or anyone who wants to share images across devices on their local network without cloud services.

---

## Table of Contents

- [Features](#-features)
- [Motivation](-motivation)
- [Installation](#-installation)
- [Usage](#-usage)
- [Configuration](#-configuration)
- [Project Structure](#-project-structure)
- [Technical Details](#-technical-details)
- [Contributing](#-contributing)
- [License](#-license)
- [Credits](#-credits)
- [Contact](#-contact)

---

## Features

- Modern Dark UI. Sleek interface with Inter font and smooth animations.
- Welcome Screen. Professional landing page with animated entry.
- Smart Lazy Loading. Images load only when needed, reducing bandwidth usage.
- Color Palette Extraction. Automatically extracts five dominant colors per image.
- RGB Histogram. Visual representation of color distribution.
- Rich Metadata Display. Dimensions, file size, format, and color mode.
- Infinite Scroll. Seamless batch loading while browsing.
- Fully Responsive. Optimized for mobile, tablet, desktop, and 4K screens.
- Fullscreen Viewer. Click any image for fullscreen view with a detailed sidebar.
- Keyboard Navigation. Press ESC to exit fullscreen view.
- Local Network Access. Share images with any device on the same network.
- Privacy First. No cloud uploads; all files remain local.
- Zero Dependencies. Works with Python standard library; Pillow optional.
- One Command Launch. Run the script and access the gallery immediately.
---
## Motivation

This project was born out of a critical need in my professional photography workflow. Working without a dedicated, hardware-calibrated reference monitor on my desktop made it difficult to judge final color grades with confidence. However, modern smartphones often feature high-quality, factory-calibrated displays (such as OLED or Retina screens) that are excellent for color verification.

I developed this web application to utilize my mobile device as a wireless reference monitor. It hosts a local server on my PC, allowing me to instantly view high-resolution exports on my phone via the local network. Crucially, this acts as a "zero-copy" viewer. images are streamed directly from the host machine, eliminating the need to transfer, download, or clutter my phone's storage with temporary files just to check colors.

---
## Installation

### Prerequisites

- **Python 3.8 or higher**
- **PIL/Pillow** (Optional, but recommended for full features)

### Step-by-Step Installation

1. **Download the script**
   
   Save `server.py` to any folder containing images.

2. **Install Pillow (Optional but Recommended)**
   
   For color palette extraction, histograms, and advanced metadata:
   
   ```bash
   pip install Pillow
   ```
   
   > **Note:** The gallery works without Pillow but will show basic file info only.

3. **Verify Python Installation**
   
   ```bash
   python --version
   # or
   python3 --version
   ```
   
   Ensure version is 3.8 or higher.

### Quick Start

```bash
# Navigate to your image folder
cd /path/to/your/images

# Place the script in the same folder
# Then run:
python server.py
```

That's it! The server will start and display the access URLs.

---

## Usage

### Starting the Server

```bash
python server.py
```

**Output:**
```
============================================================
AirGallery Server Started
============================================================
Local access:   http://localhost:8000
Network access: http://192.168.1.100:8000
============================================================
✓ PIL/Pillow detected - Full metadata features enabled
============================================================
Press Ctrl+C to stop the server
============================================================
```

### Accessing the Gallery

1. **From the same computer:**
   - Open your browser and go to `http://localhost:8000`

2. **From other devices on your network:**
   - Use the Network access URL (e.g., `http://192.168.1.100:8000`)
   - Works on phones, tablets, other computers, smart TVs, etc.

### Interface Overview

#### Welcome Screen
![Welcome Screen](https://via.placeholder.com/800x500/0a0a0a/3b82f6?text=Welcome+Screen)

- Click **"Open Gallery"** to enter

#### Gallery View
![Gallery View](https://via.placeholder.com/800x500/0a0a0a/ffffff?text=Gallery+Grid)

- **Masonry grid layout** (Pinterest-style)
- **Hover effects** on desktop
- **Metadata cards** below each image showing:
  - Dimensions (e.g., 1920×1080)
  - File size (e.g., 2.4 MB)
  - Format (JPEG, PNG, etc.)
  - Color palette (5 swatches)
  - RGB histogram

#### Fullscreen View
![Fullscreen View](https://via.placeholder.com/800x500/000000/ffffff?text=Fullscreen+View)

- **Click any image** to view fullscreen
- **Sidebar** (desktop only) shows:
  - Complete metadata
  - Larger color palette
  - Full-size histogram
- **Click palette colors** to copy hex codes
- **Press ESC** or click "Back" to return

### Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

---

## Configuration

### Environment Variables

None required! The script works out-of-the-box.

### Customization Options

You can modify these constants in the script:

```python
# Port Settings (line ~29)
def find_available_port(start_port=8000):
    # Change 8000 to your preferred starting port

# Image Extensions (line ~23)
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg', '.ico', '.tiff', '.tif'}
# Add or remove extensions as needed

# Batch Loading Size (JavaScript section)
const BATCH_SIZE = 12;
# Change to load more/fewer images per batch
```

### Network Binding

The server binds to `0.0.0.0` (all network interfaces) by default. This is safe for local networks but should not be exposed to the internet.

---

## Project Structure

```
your-image-folder/
│
├── server.py    # Main server script (single file)
├── image1.jpg                  # Your images
├── image2.png
├── photo.webp
└── ...
```

**That's it!** Just one Python file alongside your images.

### Script Architecture

```
server.py
│
├── Import Section
│   ├── Standard library (http.server, json, etc.)
│   └── Optional: PIL/Pillow for metadata
│
├── Helper Functions
│   ├── get_local_ip()           # Network IP detection
│   ├── find_available_port()    # Auto port selection
│   ├── get_color_palette()      # Color extraction
│   ├── get_histogram_data()     # RGB histogram
│   ├── get_image_metadata()     # Metadata extraction
│   └── format_file_size()       # Human-readable sizes
│
├── HTML/CSS/JS
│   └── get_html()               # Embedded web interface
│
├── HTTP Handler
│   ├── serve_gallery()          # Serve main page
│   ├── serve_image_list()       # API: Image list
│   ├── serve_metadata()         # API: Metadata
│   └── serve_image()            # Serve image files
│
└── Main Entry Point
    └── main()                   # Start server
```

---

## Technical Details

### Supported Image Formats

- **Raster:** JPG, JPEG, PNG, GIF, WebP, BMP, TIFF, TIF
- **Vector:** SVG
- **Icon:** ICO

### Performance Features

- **Lazy Loading:** Images load 200px before entering viewport
- **Batch Processing:** Loads 12 images at a time
- **Infinite Scroll:** Automatically loads more as you scroll
- **Caching:** Browser caches images for 1 year
- **Metadata Caching:** Metadata cached in memory per session

### Browser Compatibility

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

### API Endpoints

The server provides REST-like endpoints:

```
GET /                        # Main gallery page
GET /api/images              # JSON list of all images
GET /api/metadata/{filename} # JSON metadata for specific image
GET /image/{filename}        # Serve image file
```

### Color Palette Algorithm

Uses simplified k-means clustering:
1. Resize image to 100×100px
2. Reduce color space (32 bins per channel)
3. Count color frequencies
4. Return 5 most common colors

### Histogram Generation

1. Resize image to 200×200px for performance
2. Extract RGB histograms (256 values per channel)
3. Normalize to 0-100 scale
4. Sample every 4th value (64 data points per channel)
5. Render as overlapping bars with transparency

---

## Contributing

Contributions are welcome! Here's how you can help:

### Reporting Issues

- Use GitHub Issues to report bugs
- Include Python version, OS, and steps to reproduce
- Attach screenshots if relevant

### Suggesting Features

- Open a GitHub Issue with the `enhancement` label
- Describe the feature and use case
- Explain why it would benefit users

### Submitting Pull Requests

1. **Fork** the repository
2. **Create a branch** for your feature (`git checkout -b feature/amazing-feature`)
3. **Make your changes**
   - Follow PEP 8 style guidelines for Python
   - Keep JavaScript/CSS consistent with existing style
   - Add comments for complex logic
4. **Test thoroughly**
   - Test with and without Pillow
   - Test on mobile and desktop
   - Verify all metadata features work
5. **Commit** your changes (`git commit -m 'Add amazing feature'`)
6. **Push** to your branch (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

### Code Standards

- Python: PEP 8 compliant
- JavaScript: ES6+ syntax
- CSS: BEM-like naming for classes
- Comments: Explain "why," not "what"

---

## License

This project is licensed under the **MIT License**.

See [LICENSE](LICENSE) file for full details.

---

## Credits

### Built With

- **Python** - Core language and HTTP server
- **PIL/Pillow** - Image processing and metadata extraction
- **Inter Font** - Typography by Rasmus Andersson
- **Google Fonts** - Font delivery

### Inspiration

- Pinterest's masonry layout
- Modern dark mode designs
- Minimalist photography galleries

### Libraries Used

- `http.server` - Built-in HTTP server
- `json` - JSON serialization
- `pathlib` - File path handling
- `PIL.Image` - Image processing (optional)
- `collections.Counter` - Color frequency analysis

---

## Contact

### Maintainer

**Your Name**
- GitHub: [@dilharajay](https://github.com/dilharajay)
- linkedin: [dilharapjayawardhana](https://www.linkedin.com/in/dilharapjayawardhana/)

### Support

- **Issues:** [GitHub Issues](https://github.com/dilharajay/airgallery/issues)
- **Discussions:** [GitHub Discussions](https://github.com/dilharajay/airgallery/discussions)

### Links

- **Repository:** [https://github.com/dilharajay/airgallery](https://github.com/dilharajay/airgallery)
- **Demo:** [Coming soon]

---

## Show Your Support

If you find this project useful, please consider:

- **Starring** the repository
- **Reporting** bugs
- **Suggesting** features
- **Contributing** code
- **Sharing** with others

---

## Stats

![GitHub stars](https://img.shields.io/github/stars/dilharajay/airgallery?style=social)
![GitHub forks](https://img.shields.io/github/forks/dilharajay/airgallery?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/dilharajay/airgallery?style=social)

---

**Made with ❤️ and Python**

*Last updated: December 2024*
