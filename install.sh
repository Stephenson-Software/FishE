#!/bin/sh
# Usage: sudo sh install.sh
# Safe to run again: an existing install is updated rather than cloned over.
set -e

INSTALL_DIR=/usr/games/FishE

mkdir -p /usr/games

apt-get update
apt-get install -y git

if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Existing install found in $INSTALL_DIR - updating it."
    git -C "$INSTALL_DIR" pull
else
    git clone https://github.com/Stephenson-Software/FishE "$INSTALL_DIR"
fi

echo "cd $INSTALL_DIR && ./run.sh" > /bin/fishe
chmod +x "$INSTALL_DIR/run.sh"
chmod +x /bin/fishe

echo "Installation complete. Type 'fishe' to play."
