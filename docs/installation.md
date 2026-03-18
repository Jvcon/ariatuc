# Installation Guide

Detailed installation instructions for ariatuc.

## System Requirements

- **Python**: 3.11 or higher
- **aria2c**: Latest version
- **OS**: macOS, Linux, or Windows (with WSL)

## Install aria2c

### macOS

```bash
brew install aria2
```

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install aria2
```

### Arch Linux

```bash
sudo pacman -S aria2
```

### Windows

Use [Chocolatey](https://chocolatey.org/):

```powershell
choco install aria2
```

Or download from [aria2 releases](https://github.com/aria2/aria2/releases).

## Install ariatuc

### From Source (Recommended)

```bash
# Clone repository
git clone https://github.com/Jvcon/ariatuc.git
cd ariatuc

# Install dependencies
poetry install

# Run application
poetry run ariatuc
```

### Development Installation

```bash
# Install with development dependencies
poetry install --with dev

# Verify installation
poetry run pytest
```

## Configure aria2c

### Start RPC Server

```bash
# Basic configuration
aria2c --enable-rpc --rpc-listen-all

# With authentication
aria2c --enable-rpc \
  --rpc-secret=your-secret-token \
  --rpc-listen-port=6800

# Run as daemon
aria2c --enable-rpc --daemon=true
```

### Configuration File

Create `~/.aria2/aria2.conf`:

```ini
# RPC Settings
enable-rpc=true
rpc-listen-all=true
rpc-allow-origin-all=true
rpc-listen-port=6800
rpc-secret=your-secret-token

# Download Settings
dir=/path/to/downloads
max-concurrent-downloads=5
max-connection-per-server=4
split=4

# Session
save-session=/path/to/session.txt
input-file=/path/to/session.txt
```

Start with:
```bash
aria2c --conf-path=~/.aria2/aria2.conf
```

## Configure ariatuc

Configuration is stored in `~/.config/ariatuc/config.json`:

```json
{
  "servers": [
    {
      "name": "Local",
      "url": "http://localhost:6800/jsonrpc",
      "secret": "your-secret-token"
    }
  ],
  "current_server": "Local",
  "theme": "dark",
  "auto_refresh": true,
  "refresh_interval": 1000
}
```

## Verify Installation

```bash
# Check aria2c
aria2c --version

# Check Python
python --version

# Run ariatuc tests
mise run test:unit
```

## Troubleshooting

### aria2c not found

Ensure aria2c is in your PATH:

```bash
which aria2c
```

### Connection refused

Check if aria2c RPC is running:

```bash
curl http://localhost:6800/jsonrpc
```

### Permission denied

On Linux, you may need to adjust firewall rules:

```bash
sudo ufw allow 6800/tcp
```

## Next Steps

- See [Quick Start](quick-start.md) for basic usage
- Read [Development Guide](development/) to contribute
- Check [Testing Guide](development/testing.md) for running tests
