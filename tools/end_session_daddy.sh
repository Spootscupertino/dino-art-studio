#!/usr/bin/env bash
#
# end_session.sh — close a Claude Code session cleanly.
#
# Run from inside the session worktree. Auto-detects the branch.
# Fast-forward-merges into main, pushes, then removes the worktree and
# deletes the branch (locally + on origin). Refuses to run from main.
#
# Usage:
#   tools/end_session.sh                 # interactive confirm
#   tools/end_session.sh --yes           # skip confirm
#
set -euo pipefail

MAIN_DIR="/Users/ericeldridge/dino_art"
BRANCH="$(git branch --show-current)"
WORKTREE="$(git rev-parse --show-toplevel)"

if [ "$BRANCH" = "main" ]; then
  echo "✖ refusing to run on main"
  exit 1
fi

if [ "$WORKTREE" = "$MAIN_DIR" ]; then
  echo "✖ refusing to run from the main worktree at $MAIN_DIR"
  exit 1
fi

echo "Session branch:   $BRANCH"
echo "Worktree:         $WORKTREE"
echo "Will fast-forward main → $BRANCH, push, remove worktree, delete branch."

if [ "${1:-}" != "--yes" ]; then
  read -r -p "Proceed? [y/N] " ans
  [ "$ans" = "y" ] || [ "$ans" = "Y" ] || { echo "aborted"; exit 1; }
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "✖ working tree dirty — commit or stash first:"
  git status --short
  exit 1
fi

echo "→ pushing $BRANCH (in case of unpushed commits)"
git push origin "$BRANCH"

echo "→ switching to main worktree"
cd "$MAIN_DIR"

echo "→ fast-forward merging $BRANCH into main"
git merge "$BRANCH" --ff-only

echo "→ pushing main"
git push origin main

echo "→ removing worktree $WORKTREE"
git worktree remove "$WORKTREE"

echo "→ deleting local branch $BRANCH"
git branch -d "$BRANCH"

echo "→ deleting remote branch $BRANCH (best-effort, may already be gone on mirror)"
git push origin --delete "$BRANCH" || true

echo ""
echo "✓ session closed. main is now:"
git log -1 --oneline
