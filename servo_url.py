
import subprocess
import time
import re
import os
import threading

def start_cloudflare_tunnel(port=8000):
    print("☁️ Starting Cloudflare Tunnel...")

    CLOUDFLARED_PATH = r"C:\Program Files\cloudflared\cloudflared.exe"

    # Command with protocol fallback
    cmd = [CLOUDFLARED_PATH, "tunnel", "--url", f"http://localhost:{port}", "--protocol", "http2"]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    url = None
    for _ in range(30):  # Wait max ~30s
        line = process.stdout.readline()
        if not line:
            continue
        print("🟡", line.strip())
        match = re.search(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com", line)
        if match:
            url = match.group(0)
            break
        time.sleep(1)

    if url:
        print(f"\n✅ Cloudflare Tunnel URL: {url}")
        inject_url_to_files(url)
        print("🌐 Tunnel is now live. FastAPI should be accessible externally.")
        threading.Thread(target=process.wait).start()  # Keep tunnel alive in background
        return url
    else:
        print("❌ Failed to detect Cloudflare URL. Terminating...")
        process.terminate()
        return None

def inject_url_to_files(url):
    for file in []:
        update_url_in_file(file, "SERVEO_URL", url)

def update_url_in_file(file_path, key, value):
    print(f"🔧 Updating {file_path} with {key} = \"{value}\"")
    if not os.path.exists(file_path):
        print(f"⚠️ {file_path} not found.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{key} ="):
            lines[i] = f'{key} = "{value}"\n'
            updated = True
            break

    if not updated:
        lines.insert(0, f'{key} = "{value}"\n')

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"✅ {file_path} updated.")

# === MAIN ===
if __name__ == "__main__":
    serveo_url = start_cloudflare_tunnel(port=8000)
    if serveo_url:
        print("✅ Tunnel setup complete.")
    else:
        print("❌ Tunnel setup failed.")
