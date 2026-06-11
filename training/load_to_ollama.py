import subprocess
from pathlib import Path

GGUF_PATH = "F:/naveen/AGI_Start/training/navix_model.gguf"
MODELFILE  = "F:/naveen/AGI_Start/training/Modelfile"

modelfile_content = '''FROM F:/naveen/AGI_Start/training/navix_model.gguf

TEMPLATE """[INST] {{ .System }}

{{ .Prompt }} [/INST]"""

SYSTEM """You are NAVIX, Naveen's personal AI friend. Talk like a close friend. Be warm, casual, helpful. You know Naveen is building AI in Chennai. Keep responses under 3 sentences. No bullet points. No markdown. Talk like a real person."""

PARAMETER temperature 0.8
PARAMETER top_p 0.9
PARAMETER stop "[/INST]"
PARAMETER stop "</s>"
'''

with open(MODELFILE, "w", encoding="utf-8") as f:
    f.write(modelfile_content)

print("Recreating model with correct template...")
result = subprocess.run(
    ["ollama", "create", "navix-personality", "-f", MODELFILE],
    capture_output=True, timeout=120
)
print("Done" if result.returncode == 0 else "Failed")

# test
print("Testing...")
test = subprocess.run(
    ["ollama", "run", "navix-personality", "hey how are you"],
    capture_output=True, text=True, timeout=60,
    env={**__import__('os').environ, "PYTHONIOENCODING": "utf-8"}
)
print("Response:", test.stdout[:300])