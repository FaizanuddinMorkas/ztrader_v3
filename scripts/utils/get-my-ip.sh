#!/bin/bash
# Get your current public IP address
# Useful for whitelisting in RDS security groups

echo "Your current public IP address:"
curl -s ifconfig.me
echo ""
echo ""
echo "To allow RDS access from this IP:"
echo "1. Go to AWS Console → RDS → Your Database"
echo "2. Click the VPC security group link"
echo "3. Edit inbound rules → Add rule"
echo "4. Type: PostgreSQL, Port: 5432, Source: My IP"
echo "   (or manually enter: $(curl -s ifconfig.me)/32)"
echo "5. Save rules"
