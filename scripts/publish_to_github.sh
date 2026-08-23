#!/bin/bash
# =====================================================================
# DOCUMENT-NAVIGATOR-CLASSIC-V2 - GITHUB PUBLICATION SCRIPT
# Baseline Date: 23 August 2026
# Status: EXPERIMENTAL BASELINE / WORK IN PROGRESS
# =====================================================================

GITHUB_REPO_URL="${1:-PASTE_GITHUB_REPOSITORY_URL_HERE}"

# Ensure we are in the root directory
if [ ! -f "core/src/dle_core.py" ]; then
    echo "ERROR: Could not find core/src/dle_core.py. Please run this from the monorepo root."
    exit 1
fi

# Basic check for secrets
echo ">>> Checking for potential secrets..."
if grep -r -i -E "(api_key|password|secret|token).*=.*['\"][a-zA-Z0-9_-]{10,}['\"]" core/ pipeline/ tests/ 2>/dev/null; then
    echo "WARNING: Potential secrets found! Please review."
    read -p "Continue anyway? (y/n): " confirm
    if [ "$confirm" != "y" ]; then
        exit 1
    fi
else
    echo ">>> Secret check passed."
fi

# Run test suite
echo ">>> Running test suite before release..."
pytest -q
if [ $? -ne 0 ]; then
    echo "ERROR: Tests failed! Aborting publication."
    exit 1
fi
echo ">>> All tests passed."

# Git operations
echo ">>> Initializing Git..."
git init
git add .
git commit -m "Initial experimental baseline — Document-Navigator-Classic-v2"
git branch -M main

# Remote connection
if [ "$GITHUB_REPO_URL" == "PASTE_GITHUB_REPOSITORY_URL_HERE" ]; then
    echo "====================================================================="
    echo "SUCCESS: Local repository is ready and committed to 'main'."
    echo "To push to your remote GitHub repository, run:"
    echo "  git remote add origin <YOUR_GITHUB_REPO_URL>"
    echo "  git push -u origin main"
    echo "====================================================================="
else
    echo ">>> Pushing to GitHub repository: $GITHUB_REPO_URL ..."
    git remote add origin "$GITHUB_REPO_URL"
    git push -u origin main
    echo ">>> Publication complete!"
fi
