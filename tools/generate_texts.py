#!/usr/bin/env python3
"""
Generate order text sentences for plant delivery game.

Sends prompts to local Ollama LLM to generate Finnish sentences with placeholders.
The sentences can then be used with any plant name or amount.

Output is saved to data/order_sentences.yaml

Run with: uv run python tools/generate_texts.py
"""

import re
import requests
import time
from pathlib import Path
from tqdm import tqdm
import yaml

# =============================================================================
# CONFIGURATION - Change these values as needed
# =============================================================================

OLLAMA_HOST = "172.23.64.1"
OLLAMA_PORT = 11434
MODEL = "translategemma:4b"

# Final placeholder names in the output YAML
PLANT_PLACEHOLDER = "{order_plant_name}"
AMOUNT_PLACEHOLDER = "{order_amount}"

# =============================================================================
# PATHS
# =============================================================================

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_FILE = DATA_DIR / "order_sentences.yaml"

# =============================================================================
# PROMPTS - Sent directly to the model as-is
# =============================================================================

PLANT_PROMPTS = [
    "Ilmaise suomeksi yhdellä lauseella tämä asia: I would very much like to have this green dream plant called {plant-name-placeholder}",
    "Ilmaise suomeksi yhdellä lauseella tämä asia: I absolutely must have {plant-name-placeholder}",
    "Ilmaise suomeksi yhdellä lauseella tämä ajatus: For many years I've neglected the thought but now I finally want {plant-name-placeholder}",
    "Ilmaise suomeksi yhdellä lauseella tämä asia: I really want {plant-name-placeholder} for my place",
    "Ilmaise suomeksi yhdellä lauseella tämä asia: I have decided that I need {plant-name-placeholder}",
    "Ilmaise suomeksi yhdellä lauseella tämä asia: I would like to order {plant-name-placeholder}",
    "Ilmaise suomeksi yhdellä lauseella tämä asia: I feel that {plant-name-placeholder} would be perfect for me",
    "Ilmaise suomeksi yhdellä lauseella tämä asia: I have been thinking about getting {plant-name-placeholder}",
    "Ilmaise suomeksi yhdellä lauseella tämä asia: I would be happy to receive {plant-name-placeholder}",
    "Ilmaise suomeksi yhdellä lauseella tämä asia: I am interested in {plant-name-placeholder}",
    "Ilmaise suomeksi yhdellä lauseella tämä asia: I kinda want {plant-name-placeholder}",
    "Ilmaise suomeksi yhdellä lauseella tämä asia: I've been wanting {plant-name-placeholder} for a while",
    "Ilmaise suomeksi yhdellä lauseella tämä asia: I think {plant-name-placeholder} would be nice",
    "Ilmaise suomeksi yhdellä lauseella tämä asia: I'd love to have {plant-name-placeholder}",
    "Ilmaise suomeksi yhdellä lauseella tämä asia: Maybe it's time to get {plant-name-placeholder}",
    "Ilmaise suomeksi yhdellä lauseella tämä asia: For a long time I've admired plants from afar, and now I feel ready to finally welcome {plant-name-placeholder} into my life",
    "Ilmaise suomeksi yhdellä lauseella tämä asia: After much thought and hesitation, I've come to realize that what I truly want is {plant-name-placeholder}",
    "Ilmaise suomeksi yhdellä lauseella tämä asia: I've been dreaming about adding more greenery to my space, and {plant-name-placeholder} feels like the perfect choice",
    "Ilmaise suomeksi yhdellä lauseella tämä asia: Over the years my interest has grown slowly, and now I sincerely wish to have {plant-name-placeholder}",
    "Ilmaise suomeksi yhdellä lauseella tämä asia: I've finally decided to follow my heart and ask for {plant-name-placeholder}",
]

AMOUNT_PROMPTS = [
    "Ilmaise suomeksi hyvin lyhyesti tämä asia: I need number {number-placeholder}",
    "Ilmaise suomeksi hyvin lyhyesti tämä asia: I'm thinking of the amount {number-placeholder}",
    "Ilmaise suomeksi hyvin lyhyesti tämä asia: For this place, I think we need {number-placeholder}",
    "Ilmaise suomeksi hyvin lyhyesti tämä asia: We will require {number-placeholder}",
    "Ilmaise suomeksi hyvin lyhyesti tämä asia: Please send {number-placeholder}",
    "Ilmaise suomeksi hyvin lyhyesti tämä asia: The quantity should be {number-placeholder}",
    "Ilmaise suomeksi hyvin lyhyesti tämä asia: I would like {number-placeholder}",
    "Ilmaise suomeksi hyvin lyhyesti tämä asia: Order amount is {number-placeholder}",
    "Ilmaise suomeksi hyvin lyhyesti tämä asia: We need about {number-placeholder}",
    "Ilmaise suomeksi hyvin lyhyesti tämä asia: Let's take {number-placeholder}",
    "Ilmaise suomeksi hyvin lyhyesti tämä asia: Let's go with {number-placeholder}",
    "Ilmaise suomeksi hyvin lyhyesti tämä asia: Maybe {number-placeholder} is enough",
    "Ilmaise suomeksi hyvin lyhyesti tämä asia: How about {number-placeholder}",
    "Ilmaise suomeksi hyvin lyhyesti tämä asia: Just {number-placeholder} please",
    "Ilmaise suomeksi hyvin lyhyesti tämä asia: I'll take {number-placeholder}",
    "Ilmaise suomeksi hyvin lyhyesti tämä asia: We need {number-placeholder} ASAP",
    "Ilmaise suomeksi hyvin lyhyesti tämä asia: Send {number-placeholder} now",
    "Ilmaise suomeksi hyvin lyhyesti tämä asia: Urgently need {number-placeholder}",
    "Ilmaise suomeksi hyvin lyhyesti tämä asia: We are short {number-placeholder}",
    "Ilmaise suomeksi hyvin lyhyesti tämä asia: Please deliver {number-placeholder} immediately",
]


def test_connection():
    """Test connection to Ollama server."""
    try:
        response = requests.get(
            f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/version",
            timeout=10
        )
        version = response.json().get("version", "unknown")
        print(f"Connected to Ollama v{version}")
        return True
    except Exception as e:
        print(f"Failed to connect to Ollama: {e}")
        return False


def preload_model():
    """Preload the model to warm it up."""
    try:
        payload = {"model": MODEL}
        result = requests.post(
            f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/chat",
            json=payload,
            timeout=480
        ).json()
        load_time = result.get("load_duration", 0) / 1e9
        if load_time > 0:
            print(f"Model loaded ({load_time:.1f}s)")
        else:
            print("Model already loaded")
    except Exception as e:
        print(f"Preload warning: {e}")


def call_ollama(prompt):
    """Send a prompt to Ollama and return the response text."""
    url = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/chat"

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": {"temperature": 0.7}
    }

    try:
        response = requests.post(url, json=payload, timeout=180)
        response.raise_for_status()

        result = response.json()
        message = result.get("message", {})
        content = message.get("content", "").strip()

        return content

    except requests.exceptions.Timeout:
        return None
    except Exception as e:
        tqdm.write(f"Error: {e}")
        return None


def format_time(seconds):
    """Format seconds into human-readable time."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"


def has_placeholder(text):
    """Check if text contains a placeholder like {something} or [something]."""
    if re.search(r'\{[^}]+\}', text):
        return True
    if re.search(r'\[[^\]]+\]', text):
        return True
    return False


def normalize_placeholder(text, sentence_type):
    """
    Replace any {something} or [something] with the correct placeholder.
    If no placeholder found, append the correct one at the end.
    """
    # Determine which placeholder to use
    if sentence_type == "plant":
        final_placeholder = PLANT_PLACEHOLDER
    else:
        final_placeholder = AMOUNT_PLACEHOLDER

    # Replace {anything} with the correct placeholder
    result = re.sub(r'\{[^}]+\}', final_placeholder, text)

    # Replace [anything] with the correct placeholder
    result = re.sub(r'\[[^\]]+\]', final_placeholder, result)

    # If still no placeholder, append it at the end
    if final_placeholder not in result:
        result = result.rstrip('.') + " " + final_placeholder + "."

    return result


def remove_duplicates(sentences):
    """Remove duplicate sentences."""
    seen = set()
    unique_sentences = []
    for entry in sentences:
        key = (entry["sentence_type"], entry["phrase"])
        if key not in seen:
            seen.add(key)
            unique_sentences.append(entry)
    return unique_sentences


def save_output(sentences):
    """Save sentences to YAML file."""
    data = {"sentences": sentences}

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

    print(f"Saved {len(sentences)} sentences to {OUTPUT_FILE}")


def main():
    """Main entry point."""
    print("=" * 60)
    print("GENERATE ORDER TEXT SENTENCES")
    print("=" * 60)
    print(f"Model: {MODEL}")
    print(f"Host: {OLLAMA_HOST}:{OLLAMA_PORT}")
    print(f"Output: {OUTPUT_FILE}")
    print("=" * 60)

    # Test connection
    print("\nTesting connection...")
    if not test_connection():
        print("Cannot connect to Ollama. Make sure it's running.")
        return

    # Preload model
    print(f"\nPreloading {MODEL}...")
    preload_model()

    # Calculate total work
    total_prompts = len(PLANT_PROMPTS) + len(AMOUNT_PROMPTS)
    print(f"\nPlant prompts: {len(PLANT_PROMPTS)}")
    print(f"Amount prompts: {len(AMOUNT_PROMPTS)}")
    print(f"Total prompts: {total_prompts}")

    sentences = []
    start_time = time.time()

    # Process all prompts with a single progress bar
    all_prompts = []
    for prompt in PLANT_PROMPTS:
        all_prompts.append(("plant", prompt))
    for prompt in AMOUNT_PROMPTS:
        all_prompts.append(("amount", prompt))

    with tqdm(total=total_prompts, desc="Generating", unit="prompt") as pbar:
        for sentence_type, prompt in all_prompts:
            # Send prompt as-is to the model
            response = call_ollama(prompt)

            if response:
                # Normalize placeholder to the correct format
                phrase = normalize_placeholder(response, sentence_type)
                sentences.append({
                    "sentence_type": sentence_type,
                    "phrase": phrase
                })
                tqdm.write(f"  [{sentence_type}] {phrase[:70]}...")
            else:
                tqdm.write(f"  Failed: {prompt[:50]}...")

            pbar.update(1)
            time.sleep(0.2)

    # Remove duplicates
    print("\nRemoving duplicates...")
    original_count = len(sentences)
    sentences = remove_duplicates(sentences)
    removed_count = original_count - len(sentences)
    if removed_count > 0:
        print(f"Removed {removed_count} duplicates")

    # Save output
    print("\n" + "=" * 60)
    save_output(sentences)

    # Summary
    elapsed = time.time() - start_time
    plant_count = 0
    amount_count = 0
    for s in sentences:
        if s["sentence_type"] == "plant":
            plant_count = plant_count + 1
        else:
            amount_count = amount_count + 1

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Plant sentences: {plant_count}")
    print(f"  Amount sentences: {amount_count}")
    print(f"  Total sentences: {len(sentences)}")
    print(f"  Total time: {format_time(elapsed)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
