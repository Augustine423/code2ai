#!/bin/bash

# Exit on error
set -e

# Define project directory and virtual environment
PROJECT_DIR="/home/ubuntu/code2ai/13ai"
VENV_DIR="$PROJECT_DIR/myenv"
LOG_DIR="$PROJECT_DIR/logs"
MODEL_FILE="$PROJECT_DIR/aimodel/modelv0.3.5.pt"
PYTHON_VERSION="3.12"

# Create project and log directories
echo "Setting up project directory: $PROJECT_DIR"
mkdir -p "$PROJECT_DIR" "$LOG_DIR" "$PROJECT_DIR/aimodel"

# Update system and install dependencies
echo "Updating system and installing dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-venv \
    python${PYTHON_VERSION}-dev \
    libgl1 \
    libgl1-mesa-dri \
    libglib2.0-0 \
    npm

# Create and activate virtual environment
echo "Creating virtual environment in $VENV_DIR..."
python${PYTHON_VERSION} -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# Upgrade pip and install Python packages
echo "Installing Python packages..."
pip install --upgrade pip
pip install \
    numpy==1.26.4 \
    opencv-python-headless==4.10.0.84 \
    Pillow==10.4.0 \
    ultralytics==8.3.4 \
    websockets==13.0.1 \
    python-socketio==5.11.4 \
    eventlet==0.36.0

# Install wscat for WebSocket testing
echo "Installing wscat for WebSocket testing..."
npm install -g wscat

# Verify project files
echo "Checking for required project files..."
for file in server.py server_websocket.py qeue.py detection.py; do
    if [ ! -f "$PROJECT_DIR/$file" ]; then
        echo "Error: $file not found in $PROJECT_DIR"
        exit 1
    fi
done

# Verify YOLO model file
if [ ! -f "$MODEL_FILE" ]; then
    echo "Warning: YOLO model file ($MODEL_FILE) not found. Ensure it is uploaded."
fi

# Create systemd service for Socket.IO server
echo "Creating systemd service for Socket.IO server..."
sudo bash -c "cat > /etc/systemd/system/socketio.service << EOF
[Unit]
Description=Socket.IO Server for 13ai
After=network.target

[Service]
User=ubuntu
WorkingDirectory=$PROJECT_DIR
Environment=\"PATH=$VENV_DIR/bin\"
ExecStart=$VENV_DIR/bin/python $PROJECT_DIR/server.py
Restart=always
StandardOutput=append:$LOG_DIR/socketio.log
StandardError=append:$LOG_DIR/socketio.log

[Install]
WantedBy=multi-user.target
EOF"

# Create systemd service for WebSocket server
echo "Creating systemd service for WebSocket server..."
sudo bash -c "cat > /etc/systemd/system/websocket.service << EOF
[Unit]
Description=WebSocket Server for 13ai
After=network.target

[Service]
User=ubuntu
WorkingDirectory=$PROJECT_DIR
Environment=\"PATH=$VENV_DIR/bin\"
ExecStart=$VENV_DIR/bin/python $PROJECT_DIR/server_websocket.py
Restart=always
StandardOutput=append:$LOG_DIR/websocket.log
StandardError=append:$LOG_DIR/websocket.log

[Install]
WantedBy=multi-user.target
EOF"

# Reload systemd and enable services
echo "Enabling and starting systemd services..."
sudo systemctl daemon-reload
sudo systemctl enable socketio.service
sudo systemctl enable websocket.service
sudo systemctl start socketio.service
sudo systemctl start websocket.service

# Verify services are running
echo "Checking systemd service status..."
sudo systemctl status socketio.service --no-pager
sudo systemctl status websocket.service --no-pager

# Deactivate virtual environment
deactivate

# Instructions for monitoring and testing
echo "Deployment complete!"
echo "To monitor logs:"
echo "  Socket.IO: journalctl -u socketio.service -f"
echo "  WebSocket: journalctl -u websocket.service -f"
echo "To test servers:"
echo "  Socket.IO: curl http://<ec2-public-ip>:5000"
echo "  WebSocket: wscat -c ws://<ec2-public-ip>:5001"
echo "To stop/restart services:"
echo "  sudo systemctl stop socketio.service"
echo "  sudo systemctl stop websocket.service"
echo "  sudo systemctl restart socketio.service"
echo "  sudo systemctl restart websocket.service"
echo "Ensure ports 5000 and 5001 are open in your EC2 security group."