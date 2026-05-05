#!/bin/bash
# Double-click to start the Flux generator + open browser.
# Close the Terminal window (or Ctrl+C) to stop it.

cd "$HOME/dino_art" || { echo "dino_art folder not found"; sleep 5; exit 1; }
source venv/bin/activate

# Open browser once the server is up (give it a moment to bind the port)
( sleep 4 && open "http://localhost:8888" ) &

python flux/comfyui_server.py --port 8888
