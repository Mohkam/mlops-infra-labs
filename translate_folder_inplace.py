import subprocess
import sys
import time
import requests
import socket
from pathlib import Path
from tqdm import tqdm

# -------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------
SOURCE_FOLDER = r"C:/repos/ai-platform-lab/mlops-infra-labs"   # Project root
PORT = 1234                              # Default port, will check availability
CHUNK_SIZE = 2000
FILE_EXTENSIONS = {".*"}                 # Use ".*" for all files
EXCLUDE_DIRS = {'.git', '__pycache__', 'node_modules', '.venv', 'venv',
                '.idea', '.vscode'}
# -------------------------------------------------------------------

API_URL = f"http://localhost:{PORT}/v1/chat/completions"
SCRIPT_NAME = Path(__file__).name

def is_port_in_use(port):
    """Check if a port is already listening on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def get_available_llms():
    """Run `lms ls` and return a list of model IDs for LLMs (excluding embeddings)."""
    try:
        result = subprocess.run(["lms", "ls"], capture_output=True, text=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print("Error running 'lms ls'. Is LM Studio installed and in PATH?")
        sys.exit(1)

    lines = result.stdout.splitlines()
    models = []
    capture = False
    for line in lines:
        if line.startswith("LLM"):
            capture = True
            continue
        if capture:
            if line.startswith("EMBEDDING") or line.startswith("---") or line.strip() == "":
                break
            parts = line.strip().split()
            if parts and '/' in parts[0]:
                models.append(parts[0])
    return models

def choose_model(models):
    if not models:
        print("No LLMs found via `lms ls`. Please download a model first.")
        sys.exit(1)
    print("Available LLMs:")
    for i, m in enumerate(models, 1):
        print(f"  {i}. {m}")
    if len(models) == 1:
        choice = input("Use this model? (Y/n): ").strip().lower()
        if choice and choice != 'y':
            sys.exit(0)
        return models[0]
    idx = input(f"Select model number (1-{len(models)}): ").strip()
    try:
        idx = int(idx)
        if 1 <= idx <= len(models):
            return models[idx-1]
    except:
        pass
    print("Invalid selection. Exiting.")
    sys.exit(1)

def start_server(model_id, port):
    # Check if port is already in use (maybe LM Studio GUI left a server running)
    if is_port_in_use(port):
        print(f"Port {port} is already in use. Attempting to use existing server...")
        try:
            r = requests.get(f"http://localhost:{port}/v1/models", timeout=5)
            if r.status_code == 200:
                print("Existing server is responsive. Will reuse it.")
                return None  # No process to manage
        except:
            print("Existing server on that port is not responding as expected.")
            alt_port = port + 1
            print(f"Trying alternative port {alt_port}.")
            return start_server(model_id, alt_port)

    # Start new server
    print(f"Starting LM Studio server with model '{model_id}' on port {port}...")
    # Show output in real time to catch errors immediately
    proc = subprocess.Popen(
        ["lms", "load", model_id, "--port", str(port)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )

    # Read output line by line until we see the server is listening, or timeout
    start_time = time.time()
    while True:
        line = proc.stdout.readline()
        if line:
            print(f"[lms] {line.rstrip()}")
        # Check if the API is ready
        try:
            r = requests.get(f"http://localhost:{port}/v1/models", timeout=0.5)
            if r.status_code == 200:
                print("Server is ready.")
                return proc
        except requests.ConnectionError:
            pass
        if proc.poll() is not None:
            # Process ended
            print("lms process exited unexpectedly.")
            return None
        if time.time() - start_time > 120:
            print("Timeout waiting for server to start.")
            proc.terminate()
            return None

def translate_text(text, max_retries=3):
    prompt = (
        "Translate the following Korean text to English. "
        "Return only the translation, without any additional comments or explanations.\n\n"
        f"Korean text:\n{text}"
    )
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": len(text) * 3,
    }
    for attempt in range(max_retries):
        try:
            resp = requests.post(API_URL, json=payload, timeout=120)
            resp.raise_for_status()
            translation = resp.json()["choices"][0]["message"]["content"].strip()
            return translation
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Retrying after error: {e}")
                time.sleep(2)
            else:
                raise
    return ""

def chunk_text(text, size):
    chunks = []
    while len(text) > size:
        split_pos = text.rfind("\n", 0, size)
        if split_pos == -1:
            split_pos = text.rfind(" ", 0, size)
        if split_pos == -1:
            split_pos = size
        chunks.append(text[:split_pos])
        text = text[split_pos:].lstrip()
    if text:
        chunks.append(text)
    return chunks

def translate_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except (UnicodeDecodeError, PermissionError, OSError) as e:
        tqdm.write(f"  Skipping unreadable file: {filepath.name} ({e})")
        return

    if not content.strip():
        return

    chunks = chunk_text(content, CHUNK_SIZE)
    translated_chunks = []
    print(f"  Translating {filepath.name} ({len(chunks)} chunk(s))...")
    for chunk in tqdm(chunks, desc="    Chunks", leave=False):
        translated_chunks.append(translate_text(chunk))

    translated_content = "".join(translated_chunks)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(translated_content)

def should_skip(file_path):
    if file_path.name == SCRIPT_NAME:
        return True
    return bool(set(file_path.parts).intersection(EXCLUDE_DIRS))

def main():
    # 1. Get available LLMs
    models = get_available_llms()
    model_id = choose_model(models)

    # 2. Start server (or reuse existing)
    server_proc = start_server(model_id, PORT)

    # If server couldn't start, exit
    if server_proc is None and not is_port_in_use(PORT):
        print("Failed to start server. Aborting.")
        sys.exit(1)

    try:
        src = Path(SOURCE_FOLDER)
        if not src.exists():
            print(f"Source folder '{src}' does not exist.")
            sys.exit(1)

        files = []
        for f in src.rglob("*"):
            if f.is_file() and not should_skip(f):
                if ".*" in FILE_EXTENSIONS or f.suffix.lower() in FILE_EXTENSIONS:
                    files.append(f)

        if not files:
            print("No matching files found.")
            return

        print(f"Found {len(files)} file(s) to translate in-place.")
        print("WARNING: This will OVERWRITE all original files with English translations.")
        response = input("Type YES to confirm: ")
        if response.strip().upper() != "YES":
            print("Aborted.")
            return

        for filepath in tqdm(files, desc="Files"):
            try:
                translate_file(filepath)
            except Exception as e:
                tqdm.write(f"Error translating {filepath}: {e}")

        print("Done. All files have been translated in-place.")
    finally:
        if server_proc:
            server_proc.terminate()
            server_proc.wait()
            print("Server stopped.")
        else:
            print("External server left running (not managed by this script).")

if __name__ == "__main__":
    main()