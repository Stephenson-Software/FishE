mkdir /usr/games

apt-get update
apt-get install git
cd /usr/games && git clone https://github.com/Stephenson-Software/FishE

echo "cd /usr/games/FishE && ./run.sh" > /bin/fishe
chmod +x /usr/games/FishE/run.sh
chmod +x /bin/fishe

echo "Installation complete. Type 'fishe' to play."

