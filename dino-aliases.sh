#!/bin/bash
# Dino Art CLI shortcuts
# Add to ~/.zshrc:  source /Users/ericeldridge/dino_art/dino-aliases.sh

DINO_DIR="/Users/ericeldridge/dino_art"

alias feedback="python3 $DINO_DIR/unified_feedback.py"
alias winners="python3 $DINO_DIR/unified_feedback.py --winners"
alias history="python3 $DINO_DIR/unified_feedback.py --history"
alias trends="python3 $DINO_DIR/unified_feedback.py --trends"
alias generate="python3 $DINO_DIR/generate_prompt.py"

# `prompt`        — print the locked T. rex MJ prompt (5 refs + locked params)
# `prompt | pbcopy` — copy it straight to the clipboard
# `prompt "Mosasaurus"` — once another species is added to refs/locked_refs.json
prompt() {
    python3 "$DINO_DIR/tools/print_locked_prompt.py" "${1:-Tyrannosaurus rex}"
}
