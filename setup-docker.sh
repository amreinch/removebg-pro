#!/bin/bash
# Fix Docker permissions and deploy QuickTools

echo "🔧 Setting up Docker permissions..."
echo ""

# Check if user is in docker group
if groups | grep -q docker; then
    echo "✅ Already in docker group"
else
    echo "Adding user to docker group (requires sudo)..."
    sudo usermod -aG docker $USER
    echo "✅ Added to docker group"
    echo ""
    echo "⚠️  You need to log out and log back in for this to take effect!"
    echo "   OR run: newgrp docker"
    echo ""
    read -p "Apply changes now with 'newgrp docker'? (y/n): " APPLY
    if [ "$APPLY" = "y" ]; then
        echo "Applying changes..."
        newgrp docker <<EOF
cd ~/projects/quicktools
./deploy-local.sh
EOF
        exit 0
    else
        echo ""
        echo "Please run these commands manually:"
        echo "  newgrp docker"
        echo "  cd ~/projects/quicktools"
        echo "  ./deploy-local.sh"
        exit 0
    fi
fi

# If already in group, just deploy
cd ~/projects/quicktools
./deploy-local.sh
