#!/bin/bash
# SpectrumSnek GitHub Upload Script
# This script initializes the repository and prepares it for GitHub upload

echo "🐍📻 SpectrumSnek GitHub Upload Script"
echo "======================================"

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "radio_scanner" ]; then
    echo "❌ Error: Not in the correct SpectrumSnek directory"
    echo "Please run this script from the radiotools directory"
    exit 1
fi

echo "✅ Found SpectrumSnek project files"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first:"
    echo "  Ubuntu/Debian: sudo apt install git"
    echo "  CentOS/RHEL: sudo yum install git"
    echo "  macOS: brew install git"
    exit 1
fi

echo "✅ Git is installed"

# Check if already a git repository
if [ -d ".git" ]; then
    echo "⚠️  Git repository already exists. Checking status..."
    git status --porcelain > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Repository is clean and ready"
    else
        echo "⚠️  Repository has uncommitted changes. Please commit or stash them first."
        exit 1
    fi
else
    echo "📝 Initializing Git repository..."
    git init
    echo "✅ Git repository initialized"
fi

# Add all files
echo "📦 Adding files to repository..."
git add .

# Check if there are files to commit
if git diff --cached --quiet; then
    echo "⚠️  No files to commit. Repository might already be up to date."
else
    # Create the commit
    echo "💾 Creating initial commit..."
    git commit -m "🐍📻 Initial release: SpectrumSnek - Python-powered radio spectrum toolkit!

✨ Features:
• RTL-SDR Spectrum Analyzer - Real-time spectrum visualization
• ADS-B Aircraft Tracker - Aviation surveillance & tracking  
• Traditional Radio Scanner - Frequency bank scanning with squelch
• Frequency Bank Editor - XML-based frequency management
• Web Interfaces - Remote control for all tools
• Modular Architecture - Extensible plugin system

🛠️ Tech Stack:
• Python 3.8+ with scientific computing (numpy, scipy)
• RTL-SDR hardware support via pyrtlsdr
• Flask web interfaces with real-time updates
• Curses-based terminal UI
• Comprehensive testing & documentation

🎯 Perfect for:
• Ham radio operators & SDR enthusiasts
• Aviation spotters & air traffic monitoring
• Emergency communications scanning
• Radio frequency research & education"

    echo "✅ Initial commit created"
fi

echo ""
echo "🎯 Repository is ready! Now you need to:"
echo ""
echo "1. Create a GitHub repository named 'spectrumsnek'"
echo "   Go to https://github.com → New repository"
echo "   Name: spectrumsnek"
echo "   Description: 🐍📻 A Python-powered radio spectrum analysis toolkit using RTL-SDR"
echo "   Make it Public, don't initialize with README"
echo ""
echo "2. Connect to GitHub and push:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/spectrumsnek.git"
echo "   git push -u origin main"
echo ""
echo "3. Or if using GitHub CLI:"
echo "   gh repo create spectrumsnek --public --source=. --remote=origin --push"
echo ""
echo "🐍📻 Your SpectrumSnek is ready to slither onto GitHub!"
echo "   Don't forget to add topics: python, rtl-sdr, radio, spectrum-analyzer, sdr"