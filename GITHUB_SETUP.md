# GitHub Repository Setup Instructions

Since GitHub CLI is not installed, please follow these manual steps to set up your GitHub repository:

## Option 1: Using GitHub Web Interface

1. Go to https://github.com/new
2. Repository name: `dual_asset_bot`
3. Description: `Binance Dual Investment Auto Trading Bot with AI-powered decision making`
4. Choose: Public or Private (as you prefer)
5. DO NOT initialize with README, .gitignore, or license
6. Click "Create repository"

## Option 2: Install GitHub CLI First

```bash
# On macOS:
brew install gh

# On Ubuntu/Debian:
sudo apt install gh

# On Windows:
winget install --id GitHub.cli
```

## After Creating Repository

Run these commands in your terminal:

```bash
# Add remote repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/dual_asset_bot.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Enable Auto-Push (Optional but Recommended)

To automatically push to GitHub after every commit:

```bash
# Create git hook for auto-push
cat > .git/hooks/post-commit << 'EOF'
#!/bin/bash
# Auto-push to GitHub after every commit
echo "🔄 Auto-pushing to GitHub..."
git push origin main
if [ $? -eq 0 ]; then
    echo "✅ Successfully backed up to GitHub"
else
    echo "⚠️ GitHub push failed - manual push may be required"
fi
EOF

chmod +x .git/hooks/post-commit
```

## Verification

After setup, verify with:
```bash
git remote -v
```

You should see:
```
origin  https://github.com/YOUR_USERNAME/dual_asset_bot.git (fetch)
origin  https://github.com/YOUR_USERNAME/dual_asset_bot.git (push)
```