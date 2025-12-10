#!/usr/bin/env python3
"""
Local Network Image Gallery Server
===================================
Run with: python script.py
Then open browser to: http://[your-local-ip]:[port]

This script runs a simple, zero-dependency web server that creates a gallery
of images from the directory it is run in. It is designed to be portable
and easy to use.

Install Pillow for full metadata features:
pip install Pillow

Developed by Dilhara Jayawardhana
"""

# --- Core Imports ---
import socket
import mimetypes
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote, urlparse

# --- Optional Imports for Enhanced Features ---
try:
    # Pillow is used for advanced image metadata (dimensions, color palette, etc.)
    from PIL import Image
    from collections import Counter
    PIL_AVAILABLE = True
except ImportError:
    # If Pillow is not installed, the server will still run but with fewer features.
    PIL_AVAILABLE = False

# --- Global Configuration ---
# Set of recognized image file extensions.
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg', '.ico', '.tiff', '.tif'}


# --- Utility Functions ---

def get_local_ip():
    """
    Finds the local IP address of the machine.
    This is used to display a network-accessible URL to the user.
    """
    try:
        # Connect to a public DNS server to find the primary network interface.
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        # Fallback to localhost if the IP cannot be determined.
        return "127.0.0.1"


def find_available_port(start_port=8000):
    """
    Finds an available TCP port to bind the server to, starting from `start_port`.
    This avoids conflicts if the default port is already in use.
    """
    port = start_port
    while port < 65535:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            # If the port is in use, try the next one.
            port += 1
    # Fallback to the starting port if no available port is found.
    return start_port


def get_color_palette(img, num_colors=5):
    """
    Extracts a dominant color palette from a Pillow Image object.
    Requires Pillow to be installed.
    """
    # Create a copy and convert to RGB to ensure consistency.
    img = img.copy().convert('RGB')
    # Resize to a small thumbnail for faster processing.
    img.thumbnail((100, 100))
    # Get all pixel data and reduce color depth to group similar colors.
    pixels = list(img.getdata())
    reduced = [(r // 32 * 32, g // 32 * 32, b // 32 * 32) for r, g, b in pixels]
    # Count the occurrences of each reduced color.
    color_counts = Counter(reduced)
    # Get the most common colors.
    dominant = color_counts.most_common(num_colors)
    # Format the colors as hex strings.
    return [f'#{r:02x}{g:02x}{b:02x}' for (r, g, b), _ in dominant]


def get_histogram_data(img):
    """
    Generates RGB histogram data from a Pillow Image object.
    Requires Pillow to be installed.
    """
    img = img.convert('RGB')
    img.thumbnail((200, 200))
    # Get histogram for all color channels.
    histogram = img.histogram()
    # Split into individual R, G, B channels.
    r_hist, g_hist, b_hist = histogram[0:256], histogram[256:512], histogram[512:768]
    # Normalize the histogram values to a 0-100 scale for easier rendering.
    max_val = max(max(r_hist), max(g_hist), max(b_hist))
    if max_val > 0:
        r_hist = [int(v * 100 / max_val) for v in r_hist]
        g_hist = [int(v * 100 / max_val) for v in g_hist]
        b_hist = [int(v * 100 / max_val) for v in b_hist]
    # Downsample the data for a smaller payload and faster rendering.
    return {'r': r_hist[::4], 'g': g_hist[::4], 'b': b_hist[::4]}


def format_file_size(size):
    """
    Formats a file size in bytes into a human-readable string (KB, MB, GB).
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def get_image_metadata(file_path):
    """
    Gathers metadata for a given image file.
    If Pillow is available, it extracts advanced data like dimensions and color palette.
    """
    metadata = {
        'filename': file_path.name,
        'size': file_path.stat().st_size,
        'size_formatted': format_file_size(file_path.stat().st_size),
    }
    if PIL_AVAILABLE:
        try:
            with Image.open(file_path) as img:
                metadata.update({
                    'dimensions': f"{img.width}×{img.height}",
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'palette': get_color_palette(img),
                    'histogram': get_histogram_data(img)
                })
        except Exception as e:
            # If Pillow fails to process the file, record the error.
            metadata['error'] = str(e)
    return metadata


def get_html():
    """
    Returns the main HTML content for the gallery page.
    All CSS and JavaScript are embedded within this single HTML string for portability.
    """
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Image Gallery</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            /* --- CSS styles are embedded here for portability --- */
            * { margin: 0; padding: 0; box-sizing: border-box; }
            :root {
                --bg-primary: #0a0a0a; --bg-secondary: #151515; --text-primary: #ffffff;
                --text-secondary: #a0a0a0; --text-tertiary: #666666; --accent: #3b82f6;
                --accent-hover: #2563eb; --card-bg: #1a1a1a; --border: rgba(255, 255, 255, 0.1);
            }
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                background: var(--bg-primary); color: var(--text-primary); overflow-x: hidden;
                -webkit-font-smoothing: antialiased;
            }
            .welcome-screen {
                position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                background: var(--bg-primary); display: flex; justify-content: center;
                align-items: center; z-index: 2000; opacity: 1; transition: opacity 0.5s;
            }
            .welcome-screen.hidden { opacity: 0; pointer-events: none; }
            .welcome-content { text-align: center; max-width: 600px; padding: 40px; }
            .welcome-icon { font-size: 5rem; margin-bottom: 30px; animation: float 3s ease-in-out infinite; }
            @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-20px); } }
            .welcome-title {
                font-size: 3rem; font-weight: 700; margin-bottom: 16px; letter-spacing: -0.02em;
                background: linear-gradient(135deg, #3b82f6, #8b5cf6);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            }
            .welcome-subtitle { font-size: 1.2rem; color: var(--text-secondary); margin-bottom: 40px; }
            .welcome-button {
                background: var(--accent); border: none; color: white; padding: 16px 48px;
                border-radius: 12px; font-size: 1.1rem; font-weight: 600; cursor: pointer;
                transition: all 0.3s; box-shadow: 0 8px 24px rgba(59, 130, 246, 0.3);
            }
            .welcome-button:hover {
                background: var(--accent-hover); transform: translateY(-2px);
                box-shadow: 0 12px 32px rgba(59, 130, 246, 0.4);
            }
            .header {
                position: sticky; top: 0; background: rgba(10, 10, 10, 0.95);
                backdrop-filter: blur(20px); border-bottom: 1px solid var(--border);
                padding: 20px 30px; z-index: 100; display: flex; justify-content: space-between;
            }
            .header h1 { font-size: 1.5rem; font-weight: 600; display: flex; gap: 10px; }
            .header .count { font-size: 0.9rem; color: var(--text-secondary); }
            .gallery {
                column-count: 5; column-gap: 16px; padding: 30px; max-width: 100%;
            }
            @media (max-width: 1800px) { .gallery { column-count: 4; } }
            @media (max-width: 1400px) { .gallery { column-count: 3; } }
            @media (max-width: 1000px) { .gallery { column-count: 2; column-gap: 12px; padding: 20px; } }
            @media (max-width: 600px) { .gallery { column-gap: 10px; padding: 15px; } .welcome-title { font-size: 2rem; } }
            @media (max-width: 400px) { .gallery { column-count: 1; } }
            .gallery-item {
                break-inside: avoid; margin-bottom: 16px; border-radius: 12px;
                background: var(--card-bg); cursor: pointer; border: 1px solid var(--border);
                transition: transform 0.3s, box-shadow 0.3s;
            }
            .gallery-item:hover { transform: translateY(-4px); box-shadow: 0 12px 40px rgba(59, 130, 246, 0.3); border-color: var(--accent); }
            .gallery-item img { width: 100%; display: block; opacity: 0; transition: opacity 0.4s; }
            .gallery-item img.loaded { opacity: 1; }
            .skeleton {
                position: absolute; width: 100%; height: 200px;
                background: linear-gradient(90deg, #1a1a1a 25%, #252525 50%, #1a1a1a 75%);
                background-size: 200% 100%; animation: shimmer 1.5s infinite;
            }
            @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
            .image-metadata { padding: 12px; border-top: 1px solid var(--border); font-size: 0.75rem; }
            .metadata-row { display: flex; justify-content: space-between; margin-bottom: 8px; }
            .metadata-label { color: var(--text-tertiary); font-weight: 500; text-transform: uppercase; font-size: 0.65rem; }
            .metadata-value { color: var(--text-secondary); }
            .color-palette { display: flex; gap: 4px; margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border); }
            .color-swatch { flex: 1; height: 24px; border-radius: 4px; cursor: pointer; border: 1px solid rgba(255,255,255,0.1); transition: transform 0.2s; }
            .color-swatch:hover { transform: scale(1.1); }
            .histogram { margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border); height: 40px; }
            .histogram-canvas { width: 100%; height: 100%; display: block; }
            .fullscreen {
                display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                background: rgba(0,0,0,0.97); z-index: 1000; opacity: 0; transition: opacity 0.3s;
            }
            .fullscreen.active { display: flex; opacity: 1; }
            .fullscreen-content { display: flex; width: 100%; height: 100%; }
            .fullscreen-image-container { flex: 1; display: flex; justify-content: center; align-items: center; padding: 80px 20px; }
            .fullscreen-image-container img { max-width: 100%; max-height: 100%; object-fit: contain; border-radius: 8px; }
            .fullscreen-sidebar { width: 350px; background: var(--card-bg); border-left: 1px solid var(--border); overflow-y: auto; padding: 80px 24px 24px; }
            @media (max-width: 1024px) { .fullscreen-sidebar { display: none; } }
            .sidebar-section { margin-bottom: 24px; }
            .sidebar-section h3 { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: var(--text-tertiary); margin-bottom: 12px; }
            .sidebar-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 0.85rem; }
            .sidebar-label { color: var(--text-secondary); font-weight: 500; }
            .sidebar-value { color: var(--text-primary); text-align: right; }
            .sidebar-palette { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin-top: 12px; }
            .sidebar-color { aspect-ratio: 1; border-radius: 8px; cursor: pointer; border: 1px solid rgba(255,255,255,0.1); transition: transform 0.2s; }
            .sidebar-color:hover { transform: scale(1.1); }
            .sidebar-histogram { margin-top: 12px; height: 120px; }
            .back-button {
                position: fixed; top: 24px; left: 24px; background: var(--card-bg);
                border: 1px solid var(--border); color: var(--text-primary); padding: 12px 24px;
                border-radius: 12px; cursor: pointer; font-size: 15px; font-weight: 500;
                z-index: 1001; display: flex; gap: 8px; transition: all 0.2s;
            }
            .back-button:hover { background: var(--accent); border-color: var(--accent); }
            .loader { text-align: center; padding: 60px 20px; color: var(--text-secondary); }
            .spinner { width: 40px; height: 40px; border: 3px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 16px; }
            @keyframes spin { to { transform: rotate(360deg); } }
            .empty-state { text-align: center; padding: 100px 20px; color: var(--text-secondary); }
        </style>
    </head>
    <body>
        <!-- Welcome screen shown on first visit -->
        <div class="welcome-screen" id="welcome-screen">
            <div class="welcome-content">
                <h1 class="welcome-title">AirGallery</h1>
                <p class="welcome-subtitle">Discover your collection with style</p>
                <button class="welcome-button" onclick="enterGallery()">Open Gallery</button>
            </div>
        </div>

        <!-- Main header -->
        <div class="header"><h1><span>AirGallery</span></h1><div class="count" id="image-count">Loading...</div></div>
        
        <!-- Grid for displaying image thumbnails -->
        <div class="gallery" id="gallery"></div>

        <!-- Loading indicator shown while fetching images -->
        <div class="loader" id="loader"><div class="spinner"></div><div>Loading images...</div></div>

        <!-- Fullscreen image viewer -->
        <div class="fullscreen" id="fullscreen" onclick="hideFullscreen()">
            <button class="back-button" onclick="hideFullscreen();event.stopPropagation();"><span>←</span><span>Back</span></button>
            <div class="fullscreen-content" onclick="event.stopPropagation()">
                <div class="fullscreen-image-container" onclick="hideFullscreen()"><img id="fullscreen-img" src="" alt=""></div>
                <div class="fullscreen-sidebar">
                    <div class="sidebar-section"><h3>Details</h3><div id="sidebar-details"></div></div>
                    <div class="sidebar-section"><h3>Color Palette</h3><div class="sidebar-palette" id="sidebar-palette"></div></div>
                    <div class="sidebar-section"><h3>Histogram</h3><div class="sidebar-histogram"><canvas id="sidebar-histogram" width="302" height="120"></canvas></div></div>
                </div>
            </div>
        </div>

        <script>
            // --- Frontend JavaScript logic ---
            let images = [], loadedCount = 0, metadataCache = {}, galleryStarted = false;
            const BATCH_SIZE = 12; // Number of images to load at a time

            // Hides the welcome screen and starts loading images.
            function enterGallery() {
                const w = document.getElementById('welcome-screen');
                w.classList.add('hidden');
                setTimeout(() => w.style.display = 'none', 500);
                if (!galleryStarted) {
                    galleryStarted = true;
                    fetchImages();
                }
            }

            // Fetches the list of all image filenames from the server.
            async function fetchImages() {
                try {
                    const r = await fetch('/api/images'), d = await r.json();
                    images = d.images;
                    document.getElementById('image-count').textContent = d.total + ' image' + (d.total !== 1 ? 's' : '');
                    images.length === 0 ? showEmptyState() : loadNextBatch();
                } catch (e) {
                    document.getElementById('loader').innerHTML = '<div style="color:#ef4444;">Failed to load images</div>';
                }
            }

            // Fetches (and caches) metadata for a specific image.
            async function fetchMetadata(n) {
                if (metadataCache[n]) return metadataCache[n];
                try {
                    const r = await fetch('/api/metadata/' + n), d = await r.json();
                    metadataCache[n] = d;
                    return d;
                } catch (e) {
                    return null;
                }
            }

            // Displays a message when no images are found.
            function showEmptyState() {
                document.getElementById('loader').style.display = 'none';
                document.getElementById('gallery').innerHTML = '<div class="empty-state"><h2>No images found</h2><p>Add images and refresh</p></div>';
            }

            // Loads and displays the next batch of images.
            function loadNextBatch() {
                const g = document.getElementById('gallery'), s = loadedCount, e = Math.min(s + BATCH_SIZE, images.length);
                for (let i = s; i < e; i++) {
                    const n = images[i], it = document.createElement('div');
                    it.className = 'gallery-item';
                    const sk = document.createElement('div');
                    sk.className = 'skeleton'; // Placeholder for lazy loading
                    const im = document.createElement('img');
                    im.dataset.src = '/image/' + n; // Store real source in data attribute
                    im.alt = n;
                    const md = document.createElement('div');
                    md.className = 'image-metadata';
                    md.innerHTML = '<div style="color:#666;">Loading...</div>';
                    it.appendChild(sk);
                    it.appendChild(im);
                    it.appendChild(md);
                    g.appendChild(it);
                    
                    // Fetch metadata for the item
                    fetchMetadata(n).then(d => {
                        if (d) updateItemMetadata(it, d);
                    });
                    
                    it.onclick = () => showFullscreen(n);
                }
                loadedCount = e;
                if (loadedCount >= images.length) {
                    document.getElementById('loader').style.display = 'none';
                }
                observeImages(); // Set up IntersectionObserver for new images
            }

            // Populates a gallery item with its metadata.
            function updateItemMetadata(it, d) {
                const md = it.querySelector('.image-metadata');
                let h = '';
                if (d.dimensions) h += '<div class="metadata-row"><span class="metadata-label">Dimensions</span><span class="metadata-value">' + d.dimensions + '</span></div>';
                h += '<div class="metadata-row"><span class="metadata-label">Size</span><span class="metadata-value">' + d.size_formatted + '</span></div>';
                if (d.format) h += '<div class="metadata-row"><span class="metadata-label">Format</span><span class="metadata-value">' + d.format + '</span></div>';
                md.innerHTML = h;

                // Add color palette if available
                if (d.palette && d.palette.length > 0) {
                    const p = document.createElement('div');
                    p.className = 'color-palette';
                    d.palette.forEach(c => {
                        const s = document.createElement('div');
                        s.className = 'color-swatch';
                        s.style.backgroundColor = c;
                        s.title = c;
                        p.appendChild(s);
                    });
                    md.appendChild(p);
                }

                // Add histogram if available
                if (d.histogram) {
                    const hd = document.createElement('div');
                    hd.className = 'histogram';
                    const cv = document.createElement('canvas');
                    cv.className = 'histogram-canvas';
                    cv.width = 256;
                    cv.height = 40;
                    hd.appendChild(cv);
                    md.appendChild(hd);
                    drawHistogram(cv, d.histogram);
                }
            }

            // Renders a histogram on a canvas element.
            function drawHistogram(cv, hd) {
                const ctx = cv.getContext('2d'), w = cv.width, h = cv.height;
                ctx.clearRect(0, 0, w, h);
                [{ data: hd.r, color: 'rgba(239,68,68,0.6)' }, { data: hd.g, color: 'rgba(16,185,129,0.6)' }, { data: hd.b, color: 'rgba(59,130,246,0.6)' }].forEach(ch => {
                    ctx.fillStyle = ch.color;
                    const bw = w / ch.data.length;
                    ch.data.forEach((v, i) => {
                        const bh = (v / 100) * h;
                        ctx.fillRect(i * bw, h - bh, bw, bh);
                    });
                });
            }

            // Sets up an IntersectionObserver to lazy-load images when they enter the viewport.
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(e => {
                    if (e.isIntersecting) {
                        const im = e.target, src = im.dataset.src;
                        if (src) {
                            im.src = src;
                            im.onload = () => {
                                im.classList.add('loaded');
                                const sk = im.parentElement.querySelector('.skeleton');
                                if (sk) sk.remove();
                            };
                            delete im.dataset.src; // Remove data-src to prevent re-loading
                        }
                        imageObserver.unobserve(im);
                    }
                });
            }, { rootMargin: '200px' });

            // Attaches the observer to all images that have a data-src attribute.
            function observeImages() {
                document.querySelectorAll('img[data-src]').forEach(im => imageObserver.observe(im));
            }

            // Implements infinite scroll by loading the next batch when the user nears the bottom.
            let isLoadingMore = false;
            window.addEventListener('scroll', () => {
                if (isLoadingMore || loadedCount >= images.length) return;
                const sp = window.innerHeight + window.scrollY, th = document.documentElement.scrollHeight - 1000;
                if (sp >= th) {
                    isLoadingMore = true;
                    setTimeout(() => {
                        loadNextBatch();
                        isLoadingMore = false;
                    }, 100);
                }
            });

            // Shows the fullscreen viewer for a specific image.
            async function showFullscreen(n) {
                document.getElementById('fullscreen-img').src = '/image/' + n;
                document.getElementById('fullscreen').classList.add('active');
                document.body.style.overflow = 'hidden';
                const d = await fetchMetadata(n);
                if (d) updateSidebarMetadata(d);
            }

            // Populates the fullscreen sidebar with detailed metadata.
            function updateSidebarMetadata(d) {
                let h = '<div class="sidebar-row"><span class="sidebar-label">Filename</span><span class="sidebar-value">' + d.filename + '</span></div>';
                if (d.dimensions) h += '<div class="sidebar-row"><span class="sidebar-label">Dimensions</span><span class="sidebar-value">' + d.dimensions + '</span></div>';
                h += '<div class="sidebar-row"><span class="sidebar-label">Size</span><span class="sidebar-value">' + d.size_formatted + '</span></div>';
                if (d.format) h += '<div class="sidebar-row"><span class="sidebar-label">Format</span><span class="sidebar-value">' + d.format + '</span></div>';
                if (d.mode) h += '<div class="sidebar-row"><span class="sidebar-label">Mode</span><span class="sidebar-value">' + d.mode + '</span></div>';
                document.getElementById('sidebar-details').innerHTML = h;
                
                const p = document.getElementById('sidebar-palette');
                p.innerHTML = '';
                if (d.palette && d.palette.length > 0) d.palette.forEach(c => {
                    const cd = document.createElement('div');
                    cd.className = 'sidebar-color';
                    cd.style.backgroundColor = c;
                    cd.title = c;
                    cd.onclick = () => navigator.clipboard.writeText(c);
                    p.appendChild(cd);
                });

                if (d.histogram) {
                    const cv = document.getElementById('sidebar-histogram');
                    drawHistogram(cv, d.histogram);
                }
            }

            // Hides the fullscreen viewer.
            function hideFullscreen() {
                document.getElementById('fullscreen').classList.remove('active');
                document.body.style.overflow = '';
            }

            // Adds a keyboard shortcut to close the fullscreen viewer.
            document.addEventListener('keydown', e => {
                if (e.key === 'Escape') hideFullscreen();
            });
        </script>
    </body>
    </html>"""


class ImageGalleryHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for the image gallery server.
    This class defines how to handle different GET requests.
    """
    def log_message(self, format, *args):
        """Suppresses the default logging to keep the console clean."""
        pass

    def do_GET(self):
        """
        Handles all GET requests by routing them based on the URL path.
        """
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path in ['/', '/index.html']:
            # Serve the main gallery page.
            self.serve_gallery()
        elif path == '/api/images':
            # Serve the list of image filenames.
            self.serve_image_list()
        elif path.startswith('/api/metadata/'):
            # Serve metadata for a specific image.
            self.serve_metadata(path[14:])
        elif path.startswith('/image/'):
            # Serve an actual image file.
            self.serve_image(path[7:])
        else:
            # Handle unknown paths.
            self.send_error(404)

    def serve_image_list(self):
        """
        Scans the script's directory for image files and returns a JSON list.
        """
        script_dir = Path(__file__).parent
        images = [f.name for f in script_dir.iterdir()
                  if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS]
        images.sort()

        response = json.dumps({'images': images, 'total': len(images)})
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def serve_metadata(self, filename):
        """
        Returns a JSON object with metadata for the requested image.
        """
        script_dir = Path(__file__).parent
        file_path = script_dir / filename

        if not file_path.is_file():
            self.send_error(404)
            return

        metadata = get_image_metadata(file_path)
        response = json.dumps(metadata)

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        # Cache metadata to reduce server load.
        self.send_header('Cache-Control', 'public, max-age=3600')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def serve_gallery(self):
        """
        Serves the main HTML page.
        """
        html = get_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def serve_image(self, filename):
        """
        Serves the raw binary data for an image file.
        """
        script_dir = Path(__file__).parent
        file_path = script_dir / filename

        if not file_path.is_file() or file_path.suffix.lower() not in IMAGE_EXTENSIONS:
            self.send_error(404)
            return

        try:
            with open(file_path, 'rb') as f:
                content = f.read()

            # Guess the MIME type of the image.
            mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            self.send_response(200)
            self.send_header('Content-type', mime_type)
            self.send_header('Content-length', len(content))
            # Set a long cache time for images as they are static.
            self.send_header('Cache-Control', 'public, max-age=31536000')
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, str(e))


def main():
    """
    Main function to set up and run the HTTP server.
    """
    port = find_available_port()
    local_ip = get_local_ip()

    server = HTTPServer(('0.0.0.0', port), ImageGalleryHandler)

    # --- Startup Messages ---
    print("=" * 60)
    print("Image Gallery Server Started")
    print("=" * 60)
    print(f"Local access:   http://localhost:{port}")
    print(f"Network access: http://{local_ip}:{port}")
    print("=" * 60)
    if PIL_AVAILABLE:
        print("PIL/Pillow detected - Full metadata features enabled")
    else:
        print("PIL/Pillow not found - Install with: pip install Pillow")
        print("  (Basic features work without Pillow)")
    print("=" * 60)
    print("Press Ctrl+C to stop the server")
    print("=" * 60)

    try:
        # Start the server and keep it running until interrupted.
        server.serve_forever()
    except KeyboardInterrupt:
        # Handle graceful shutdown on Ctrl+C.
        print("\n\nServer stopped.")
        server.shutdown()


if __name__ == '__main__':
    # This ensures the main function is called only when the script is executed directly.
    main()
