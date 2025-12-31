#!/bin/bash
# Fix SpectrumSnek .bashrc syntax errors

echo "Fixing .bashrc syntax errors..."
echo "Current .bashrc line count: $(wc -l ~/.bashrc)"

# Backup current .bashrc
cp ~/.bashrc ~/.bashrc.backup.$(date +%Y%m%d_%H%M%S)
echo "✓ Backed up .bashrc to ~/.bashrc.backup.$(date +%Y%m%d_%H%M%S)"

# Remove all SpectrumSnek-related lines (they might be corrupted)
sed -i '/# SpectrumSnek/,/fi/d' ~/.bashrc
sed -i '/# SpectrumSnek/,/EOF/d' ~/.bashrc

# Check for basic syntax errors
if bash -n ~/.bashrc 2>/dev/null; then
    echo "✓ .bashrc syntax is now valid"
else
    echo "⚠ .bashrc still has syntax errors, recreating clean version..."
    # Create a minimal working .bashrc
    cat > ~/.bashrc << 'EOF'
# ~/.bashrc: executed by bash(1) for non-login shells.

# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac

# History settings
HISTCONTROL=ignoredups:ignorespace
HISTSIZE=1000
HISTFILESIZE=2000

# Check window size after each command
shopt -s checkwinsize

# Enable color support
if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    alias ls='ls --color=auto'
    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

# Basic aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'

# Enable programmable completion features
if ! shopt -oq posix; then
  if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
  fi
fi
EOF
    echo "✓ Created clean .bashrc"
fi

# Add SpectrumSnek console configuration
cat >> ~/.bashrc << 'EOF'

# SpectrumSnek console autologin
if [[ -z "$TMUX" && "$(tty)" == "/dev/tty1" ]]; then
    if command -v tmux &> /dev/null; then
        tmux has-session -t spectrum 2>/dev/null || tmux new-session -s spectrum -d ~/start_spectrum.sh
        exec tmux attach-session -t spectrum
    else
        ~/start_spectrum.sh
    fi
fi
EOF

# Test the syntax
if bash -n ~/.bashrc; then
    echo "✓ .bashrc syntax is valid"
    echo "✓ SpectrumSnek console configuration added"
    echo ""
    echo "To apply changes: source ~/.bashrc"
    echo "Or log out and back in"
else
    echo "✗ .bashrc still has syntax errors"
    echo "Check: bash -n ~/.bashrc"
fi