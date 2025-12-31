# GitHub Upload Instructions for SpectrumSnek 🐍📻

## Step 1: Install Git (if not already installed)

### On Ubuntu/Debian Linux:
```bash
sudo apt update
sudo apt install git
```

### On CentOS/RHEL/Fedora:
```bash
sudo yum install git  # CentOS/RHEL
sudo dnf install git  # Fedora
```

### On macOS (with Homebrew):
```bash
brew install git
```

### On Windows:
Download and install from: https://git-scm.com/downloads

## Step 2: Configure Git

Set up your Git identity (replace with your actual information):

```bash
git config --global user.name "Your Full Name"
git config --global user.email "your.email@example.com"
```

Verify configuration:
```bash
git config --global --list
```

## Step 3: Create GitHub Account & Repository

1. Go to https://github.com and create an account (if you don't have one)
2. Click the "+" icon in the top right → "New repository"
3. Repository name: `spectrumsnek`
4. Description: `🐍📻 A Python-powered radio spectrum analysis toolkit using RTL-SDR`
5. Make it **Public** (recommended for open source)
6. **DO NOT** initialize with README, .gitignore, or license (we already have these)
7. Click "Create repository"

## Step 4: Initialize Local Repository & Push

Navigate to your project directory and run these commands:

```bash
cd /home/nomore/radiotools

# Initialize Git repository
git init

# Add all files to staging
git add .

# Create initial commit
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

# Connect to your GitHub repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/spectrumsnek.git

# Push to GitHub
git push -u origin main
```

## Step 5: Verify Upload

1. Go to https://github.com/YOUR_USERNAME/spectrumsnek
2. You should see all your files uploaded
3. The README should display properly with the SpectrumSnek branding

## Troubleshooting

### If you get authentication errors:
```bash
# Generate a Personal Access Token on GitHub:
# Go to GitHub → Settings → Developer settings → Personal access tokens → Generate new token
# Give it repo permissions

# Then use the token as your password when prompted
git push -u origin main
# Username: YOUR_USERNAME
# Password: YOUR_PERSONAL_ACCESS_TOKEN
```

### If the push fails:
```bash
# Check remote URL
git remote -v

# Remove and re-add remote if needed
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/spectrumsnek.git

# Try pushing again
git push -u origin main
```

### If you want to rename the local directory to match GitHub:
```bash
cd /home/nomore
mv radiotools spectrumsnek
cd spectrumsnek
# Then repeat the git commands above
```

## Step 6: Add Repository Metadata

After successful upload, enhance your GitHub repository:

1. **Topics**: Click "Add topics" and add:
   - `python`
   - `rtl-sdr`
   - `radio`
   - `spectrum-analyzer`
   - `sdr`
   - `ads-b`
   - `radio-scanner`
   - `hacktoberfest`

2. **About Section**: The description should auto-populate from your README

3. **License**: Should show as MIT

4. **README**: Should render beautifully with emojis and formatting

## Step 7: Optional Enhancements

### GitHub Pages (for documentation)
1. Go to repository Settings → Pages
2. Source: "main" branch, "/docs" folder
3. Create a `/docs` folder and add documentation

### GitHub Actions (CI/CD)
Create `.github/workflows/ci.yml` for automated testing:

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    - name: Run tests
      run: |
        python -m pytest
```

Your SpectrumSnek 🐍📻 project is now ready to meet the world! 🎉