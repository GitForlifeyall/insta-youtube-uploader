import io
import time
import subprocess
from PIL import Image
import xml.etree.ElementTree as ET
import re

def is_button_rendered_at_coords(adb_exe: str, target: str, cx: int = 627, cy: int = 1112, radius: int = 25) -> bool:
    """
    Takes an instantaneous screencap via adb and checks if a bright rendered button exists around (cx, cy).
    """
    try:
        res = subprocess.run([adb_exe, "-s", target, "exec-out", "screencap", "-p"], capture_output=True, timeout=5.0)
        if res.returncode != 0 or not res.stdout:
            return False
        img = Image.open(io.BytesIO(res.stdout)).convert("RGB")
        w, h = img.size
        if cx >= w or cy >= h:
            return False

        # Sample a grid of pixels around (cx, cy)
        bright_count = 0
        total_samples = 0
        for dx in range(-radius, radius + 1, 5):
            for dy in range(-radius, radius + 1, 5):
                px = cx + dx
                py = cy + dy
                if 0 <= px < w and 0 <= py < h:
                    total_samples += 1
                    r, g, b = img.getpixel((px, py))
                    # Check if pixel is bright (white/light button background or text)
                    if (r + g + b) / 3 > 140:
                        bright_count += 1

        # If at least 30% of pixels in the button region are bright/white, button is rendered
        ratio = bright_count / max(1, total_samples)
        return ratio >= 0.25
    except Exception as e:
        return False

def dump_ui_nodes_clean(adb_exe: str, target: str):
    subprocess.run([adb_exe, "-s", target, "shell", "rm -f /sdcard/window_dump.xml"], capture_output=True)
    subprocess.run([adb_exe, "-s", target, "shell", "uiautomator dump --compressed /sdcard/window_dump.xml"], capture_output=True, timeout=4.0)
    res = subprocess.run([adb_exe, "-s", target, "shell", "cat /sdcard/window_dump.xml"], capture_output=True, text=True, errors="ignore")
    if not res.stdout or "<hierarchy" not in res.stdout:
        return []
    try:
        root = ET.fromstring(res.stdout)
        nodes = []
        for elem in root.iter("node"):
            b = elem.attrib.get("bounds", "")
            m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", b)
            cx, cy = ((int(m.group(1)) + int(m.group(3))) // 2, (int(m.group(2)) + int(m.group(4))) // 2) if m else (None, None)
            nodes.append({
                "text": elem.attrib.get("text", ""),
                "desc": elem.attrib.get("content-desc", ""),
                "res_id": elem.attrib.get("resource-id", ""),
                "class": elem.attrib.get("class", ""),
                "cx": cx,
                "cy": cy,
                "bounds": b
            })
        return nodes
    except Exception:
        return []

if __name__ == "__main__":
    target = "127.0.0.1:5555"
    print("Testing button detection on", target)
    rendered = is_button_rendered_at_coords("adb", target, 627, 1112)
    print("Button rendered (pixel check):", rendered)
    nodes = dump_ui_nodes_clean("adb", target)
    print(f"Clean UI nodes found: {len(nodes)}")
