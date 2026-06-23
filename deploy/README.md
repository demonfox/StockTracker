# StockTracker Production Deployment Guide

## systemd Service Setup

This guide helps you run StockTracker as a system service that:
- ✅ Survives SSH disconnection
- ✅ Auto-restarts on crash
- ✅ Auto-starts on server reboot
- ✅ Proper log management via `journalctl`

### Prerequisites

- Linux server with systemd (Ubuntu 18+, CentOS 7+, Debian 9+, etc.)
- Python 3.11+
- Node.js 18+
- A dedicated non-root user (e.g., `deploy`)

### Step 1: Prepare the Application

```bash
# Create a deploy user (if not exists)
sudo useradd -r -m -s /bin/bash deploy

# Copy/clone the project to /opt/stocktracker
sudo mkdir -p /opt/stocktracker
sudo cp -r /path/to/StockTracker/* /opt/stocktracker/
sudo chown -R deploy:deploy /opt/stocktracker

# Make run_prod.sh executable
sudo chmod +x /opt/stocktracker/run_prod.sh
```

### Step 2: Install the Service

```bash
# Copy the service file
sudo cp /opt/stocktracker/deploy/stocktracker.service /etc/systemd/system/

# Reload systemd to pick up the new service
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable stocktracker

# Start the service now
sudo systemctl start stocktracker
```

### Step 3: Verify

```bash
# Check status
sudo systemctl status stocktracker

# View live logs
journalctl -u stocktracker -f

# View last 100 lines of logs
journalctl -u stocktracker -n 100
```

### Common Operations

```bash
# Stop the service
sudo systemctl stop stocktracker

# Restart (e.g., after code update)
sudo systemctl restart stocktracker

# Reload systemd after editing the .service file
sudo systemctl daemon-reload

# Disable auto-start on boot
sudo systemctl disable stocktracker
```

### Configuration

Edit the service file to customize:

| Setting | Default | Description |
|---------|---------|-------------|
| `User` | `deploy` | System user to run as |
| `WorkingDirectory` | `/opt/stocktracker` | Project root path |
| `--port` | `8000` | Server listening port |
| `--workers` | `2` | Number of uvicorn workers |

After editing:
```bash
sudo systemctl daemon-reload
sudo systemctl restart stocktracker
```

### Troubleshooting

```bash
# Check if the service is running
systemctl is-active stocktracker

# See why it failed
journalctl -u stocktracker --since "5 minutes ago"

# Check for permission issues
journalctl -u stocktracker | grep -i "permission"
```

### Using a Reverse Proxy (Recommended)

For production, put Nginx in front:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Then add HTTPS with Let's Encrypt:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```
