#!/bin/bash

# CycleMACD Python Requirements Installation Script
# This script attempts multiple methods to install required Python packages

echo "=== CycleMACD Python Requirements Installation ==="
echo "Required packages from requirements.txt:"
cat requirements.txt
echo ""

# Method 1: Try standard pip3 installation
echo "Method 1: Attempting pip3 installation..."
if command -v pip3 &> /dev/null; then
    echo "pip3 found, installing packages..."
    pip3 install -r requirements.txt --break-system-packages
    if [ $? -eq 0 ]; then
        echo "✅ Successfully installed packages with pip3"
        exit 0
    fi
else
    echo "❌ pip3 not found"
fi

# Method 2: Try python3 -m pip
echo ""
echo "Method 2: Attempting python3 -m pip installation..."
python3 -m pip install -r requirements.txt --break-system-packages 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Successfully installed packages with python3 -m pip"
    exit 0
fi

# Method 3: Install pip first, then packages
echo ""
echo "Method 3: Installing pip first, then packages..."

# Try to install pip using ensurepip
python3 -c "import ensurepip; ensurepip.bootstrap()" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "pip installed via ensurepip"
    python3 -m pip install -r requirements.txt --break-system-packages
    if [ $? -eq 0 ]; then
        echo "✅ Successfully installed packages after installing pip"
        exit 0
    fi
fi

# Method 4: Try downloading get-pip.py (if network allows)
echo ""
echo "Method 4: Downloading and installing pip..."
curl -s https://bootstrap.pypa.io/get-pip.py -o get-pip.py --connect-timeout 10
if [ $? -eq 0 ] && [ -f get-pip.py ]; then
    python3 get-pip.py --break-system-packages
    if [ $? -eq 0 ]; then
        echo "pip installed successfully"
        python3 -m pip install -r requirements.txt --break-system-packages
        if [ $? -eq 0 ]; then
            echo "✅ Successfully installed packages after downloading pip"
            rm -f get-pip.py
            exit 0
        fi
    fi
    rm -f get-pip.py
fi

# Method 5: Try apt-get if available
echo ""
echo "Method 5: Attempting system package manager installation..."
if command -v apt-get &> /dev/null; then
    echo "Attempting to install python3-pip via apt-get..."
    sudo apt-get update && sudo apt-get install -y python3-pip python3-dev
    if [ $? -eq 0 ]; then
        pip3 install -r requirements.txt --break-system-packages
        if [ $? -eq 0 ]; then
            echo "✅ Successfully installed packages via system package manager"
            exit 0
        fi
    fi
fi

# Final attempt: Try individual package installation
echo ""
echo "Method 6: Individual package installation attempt..."
packages=("flask>=3.0.0" "yfinance>=0.2.0" "pandas>=2.0.0" "numpy>=1.20.0" "matplotlib>=3.5.0" "seaborn>=0.11.0" "japanize-matplotlib")

for package in "${packages[@]}"; do
    echo "Attempting to install: $package"
    python3 -m pip install "$package" --break-system-packages 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ $package installed successfully"
    else
        echo "❌ Failed to install $package"
    fi
done

# Verify installation
echo ""
echo "=== Verification ==="
echo "Checking installed packages:"

python3 -c "
import sys
required_packages = ['flask', 'yfinance', 'pandas', 'numpy', 'matplotlib', 'seaborn']
installed = []
missing = []

for package in required_packages:
    try:
        __import__(package)
        installed.append(package)
        print(f'✅ {package}: Available')
    except ImportError:
        missing.append(package)
        print(f'❌ {package}: Missing')

print(f'\\nSummary: {len(installed)}/{len(required_packages)} packages available')

if missing:
    print('\\n⚠️  Missing packages may cause application errors.')
    print('Please ensure network connectivity and try again.')
else:
    print('\\n🎉 All required packages are installed!')
"

echo ""
echo "=== Installation Complete ==="
echo "Run 'python3 simple_test.py' to verify basic functionality"
echo "Run 'python3 run_webapp.py' to start the web application"