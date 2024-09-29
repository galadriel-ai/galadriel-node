#!/bin/bash
#

# Install pre-commit hook
cp scripts/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
echo "pre-commit hook installed"

# Install pommit-msg hook
cp scripts/commit-msg .git/hooks/commit-msg
chmod +x .git/hooks/commit-msg
echo "commit-msg hook installed"

# Install pre-push hook
cp scripts/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-push
echo "pre-push hook installed"

