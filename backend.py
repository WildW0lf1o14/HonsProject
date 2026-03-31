# =========================================
# BACKEND: ENCRYPTION + BENCHMARKING API
# =========================================

# Flask handles API routing (frontend <-> backend communication)
from flask import Flask, request, jsonify, send_file

# Standard libraries for data handling and system operations
import json, os, time, base64, csv

# Pandas is used for reading Excel files
import pandas as pd

# Cryptography library provides AES-based encryption (Fernet)
from cryptography.fernet import Fernet

# Create Flask app instance
app = Flask(__name__)

# =========================================
# DATABASE SETUP (LOCAL JSON STORAGE)
# =========================================

# File used to store records (simple lightweight database)
DB_FILE = "database.json"

# Create the database file if it doesn't exist
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump([], f)

# Load database contents into memory
def load_db():
    with open(DB_FILE, "r") as f:
        return json.load(f)

# Save updated database back to file
def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# =========================================
# ENCRYPTION SYSTEM
# =========================================

# Generate encryption key (NOTE: In production, store this securely!)
KEY = Fernet.generate_key()

# Create encryption object
cipher = Fernet(KEY)

# Global variable to store current encryption mode
ENCRYPTION_MODE = "AES"

# -----------------------------------------
# MODE 1: AES ENCRYPTION (SECURE BASELINE)
# -----------------------------------------

def aes_encrypt(text):
    """Encrypt text using AES (Fernet)"""
    return cipher.encrypt(text.encode()).decode()

def aes_decrypt(text):
    """Decrypt AES-encrypted text"""
    return cipher.decrypt(text.encode()).decode()

# -----------------------------------------
# MODE 2: LLM-STYLE ENCRYPTION (SIMULATION)
# -----------------------------------------

def llm_encrypt(text):
    """
    Simulates LLM behaviour using:
    - Tokenisation (splitting words)
    - Random reordering (like attention shuffling)
    - Encoding (base64)
    
    NOTE: Not secure and not perfectly reversible
    """
    words = text.split()

    # Randomly reorder words
    import random
    random.shuffle(words)

    # Join with delimiter
    transformed = "_".join(words)

    # Encode into base64 for obfuscation
    return base64.b64encode(transformed.encode()).decode()

def llm_decrypt(text):
    """
    Attempts to reverse LLM-style transformation
    NOTE: Original order is lost → intentional limitation
    """
    decoded = base64.b64decode(text).decode()
    return decoded.replace("_", " ")

# -----------------------------------------
# MODE 3: HYBRID ENCRYPTION
# -----------------------------------------

def hybrid_encrypt(text):
    """
    Combines:
    1. AES encryption (secure)
    2. LLM-style transformation (extra obfuscation)
    """
    return llm_encrypt(aes_encrypt(text))

def hybrid_decrypt(text):
    """
    Reverse hybrid process:
    1. Undo LLM transformation
    2. Decrypt AES
    """
    return aes_decrypt(llm_decrypt(text))

# -----------------------------------------
# ENCRYPTION SWITCH
# -----------------------------------------

def encrypt(text):
    """Route encryption based on selected mode"""
    if ENCRYPTION_MODE == "AES":
        return aes_encrypt(text)
    elif ENCRYPTION_MODE == "LLM":
        return llm_encrypt(text)
    elif ENCRYPTION_MODE == "HYBRID":
        return hybrid_encrypt(text)

def decrypt(text):
    """Route decryption based on selected mode"""
    if ENCRYPTION_MODE == "AES":
        return aes_decrypt(text)
    elif ENCRYPTION_MODE == "LLM":
        return llm_decrypt(text)
    elif ENCRYPTION_MODE == "HYBRID":
        return hybrid_decrypt(text)

# =========================================
# BENCHMARKING + LOGGING
# =========================================

def benchmark(text):
    """
    Measures:
    - Encryption time
    - Decryption time
    - Validates output
    
    Returns structured performance data
    """

    # Measure encryption time
    start = time.time()
    encrypted = encrypt(text)
    enc_time = time.time() - start

    # Measure decryption time
    start = time.time()
    decrypted = decrypt(encrypted)
    dec_time = time.time() - start

    # Log results for later analysis
    log_results(ENCRYPTION_MODE, enc_time, dec_time)

    return {
        "encrypted": encrypted,
        "decrypted": decrypted,
        "encryption_time": enc_time,
        "decryption_time": dec_time
    }

def log_results(mode, enc, dec):
    """
    Stores results in CSV file
    Used for:
    - Graphing
    - Report analysis
    """

    file_exists = os.path.isfile("results.csv")

    with open("results.csv", "a", newline="") as f:
        writer = csv.writer(f)

        # Write header if file is new
        if not file_exists:
            writer.writerow(["Mode", "Encryption Time", "Decryption Time"])

        # Write data row
        writer.writerow([mode, enc, dec])

# =========================================
# API ROUTES
# =========================================

@app.route("/set_mode", methods=["POST"])
def set_mode():
    """
    Sets encryption mode from frontend dropdown
    """
    global ENCRYPTION_MODE
    mode = request.json.get("mode")

    if mode in ["AES", "LLM", "HYBRID"]:
        ENCRYPTION_MODE = mode
        return jsonify({"message": f"Mode set to {mode}"})

    return jsonify({"error": "Invalid mode"}), 400


@app.route("/benchmark", methods=["POST"])
def run_benchmark():
    """
    Runs benchmark on user-provided text input
    """
    text = request.json.get("text", "")
    return jsonify(benchmark(text))


@app.route("/benchmark_file", methods=["POST"])
def benchmark_file():
    """
    Handles uploaded files:
    - TXT / CSV
    - Excel (XLSX / XLS)
    
    Converts file → string → runs benchmark
    """
    file = request.files["file"]

    if file.filename.endswith(".txt") or file.filename.endswith(".csv"):
        content = file.read().decode()

    elif file.filename.endswith(".xlsx") or file.filename.endswith(".xls"):
        df = pd.read_excel(file)
        content = df.to_string()

    else:
        return jsonify({"error": "Unsupported file type"}), 400

    return jsonify(benchmark(content))


@app.route("/download_results")
def download_results():
    """
    Allows user to download CSV results
    for external analysis (Excel/report)
    """
    return send_file("results.csv", as_attachment=True)


# =========================================
# RUN SERVER
# =========================================
if __name__ == "__main__":
    app.run(debug=True)
