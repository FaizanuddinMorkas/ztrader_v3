#!/bin/bash
# Setup Telegram bot as systemd service on EC2

set -e

echo "🤖 Setting up Telegram Bot as systemd service..."

# Create logs directory
echo "Creating logs directory..."
mkdir -p ~/ztrader/logs

# Copy service file to systemd
echo "Installing service file..."
sudo cp ~/ztrader/scripts/deployment/trading-bot.service /etc/systemd/system/

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Enable service (start on boot)
echo "Enabling service..."
sudo systemctl enable trading-bot

# Start service
echo "Starting service..."
sudo systemctl start trading-bot

# Show status
echo ""
echo "✅ Service installed successfully!"
echo ""
echo "Service status:"
sudo systemctl status trading-bot --no-pager

echo ""
echo "📋 Useful commands:"
echo "  sudo systemctl status trading-bot    # Check status"
echo "  sudo systemctl restart trading-bot   # Restart bot"
echo "  sudo systemctl stop trading-bot      # Stop bot"
echo "  sudo systemctl start trading-bot     # Start bot"
echo "  sudo journalctl -u trading-bot -f    # View live logs"
echo "  tail -f ~/ztrader/logs/bot.log       # View bot output"
