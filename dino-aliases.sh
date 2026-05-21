#!/bin/bash
# Dino Art CLI shortcuts
# Add to ~/.zshrc:  source /Users/ericeldridge/dino_art/dino-aliases.sh

DINO_DIR="/Users/ericeldridge/dino_art"

alias feedback="python3 $DINO_DIR/unified_feedback.py"
alias winners="python3 $DINO_DIR/unified_feedback.py --winners"
alias history="python3 $DINO_DIR/unified_feedback.py --history"
alias trends="python3 $DINO_DIR/unified_feedback.py --trends"
alias generate="python3 $DINO_DIR/generate_prompt.py"

# `prompt`                        — locked T. rex prompt (prints to terminal + auto-copies to clipboard)
# `prompt --with-images`          — include image-prompt URLs inline (Discord workflow)
# `prompt --cam wormseye`         — inject a camera angle; auto-relaxes composition refs
# `prompt --cam list`             — show all camera presets
# `prompt "Mosasaurus"`           — once species is added to refs/locked_refs.json
# `prompt "Mosasaurus" --cam pov` — species + camera together
# `pp`                            — short alias for `prompt`
prompt() {
    local args=("Tyrannosaurus rex")
    if [ $# -gt 0 ]; then
        args=("$@")
    fi
    python3 "$DINO_DIR/tools/print_locked_prompt.py" "${args[@]}" | tee >(pbcopy >/dev/null)
    echo
    echo "✓ copied to clipboard"
}
alias pp=prompt
