# RDS Connection via EC2 SSH Tunnel

This guide explains how to connect to your AWS RDS database from your local machine using your EC2 instance as a bastion/jump host.

## Architecture

```
[Local Machine] --SSH--> [EC2 Instance] ---> [RDS Database]
     :5433                 65.2.153.114         RDS Endpoint
```

## Prerequisites

1. **EC2 Instance** with network access to RDS (same VPC or proper security group rules)
2. **SSH Key** for EC2 access: `~/.ssh/trading-platform-key.pem`
3. **RDS Security Group** must allow connections from EC2's security group
4. **RDS Endpoint** information

## Setup Steps

### 1. Update RDS Configuration

Edit `scripts/connect-rds.sh` and update these variables:

```bash
RDS_ENDPOINT="your-rds-endpoint.xxxxxxxxxxxx.region.rds.amazonaws.com"
RDS_PORT=5432
DB_NAME="your_database_name"
DB_USER="your_db_user"
```

**To find your RDS endpoint:**
- Go to AWS Console → RDS → Databases
- Click on your database instance
- Copy the "Endpoint" value (e.g., `mydb.c1234567890.us-east-1.rds.amazonaws.com`)

### 2. Verify EC2 Can Reach RDS

SSH into your EC2 instance and test connectivity:

```bash
# SSH into EC2
ssh -i ~/.ssh/trading-platform-key.pem ubuntu@65.2.153.114

# Test RDS connectivity (replace with your RDS endpoint)
nc -zv your-rds-endpoint.rds.amazonaws.com 5432

# Or try with psql
psql -h your-rds-endpoint.rds.amazonaws.com -U your_db_user -d your_database_name
```

If this fails, check:
- RDS security group allows inbound connections from EC2's security group
- EC2 and RDS are in the same VPC or have proper networking setup

### 3. Start the Tunnel

```bash
./scripts/connect-rds.sh
```

The tunnel will run in the foreground. Keep this terminal open.

### 4. Connect from Your Local Machine

In a **new terminal**, connect to the database:

```bash
# Using psql
psql -h localhost -p 5433 -U your_db_user -d your_database_name

# Using Python
python3 -c "
import psycopg2
conn = psycopg2.connect(
    host='localhost',
    port=5433,
    database='your_database_name',
    user='your_db_user',
    password='your_password'
)
print('Connected successfully!')
conn.close()
"
```

### 5. Update Your Application Connection String

Update your application's database connection to use:

```
Host: localhost
Port: 5433
Database: your_database_name
User: your_db_user
Password: your_password
```

Or as a connection string:
```
postgresql://your_db_user:your_password@localhost:5433/your_database_name
```

## Port Usage

- **5432** - EC2 PostgreSQL (via `connect-postgres.sh`)
- **5433** - RDS via EC2 tunnel (via `connect-rds.sh`)

Both tunnels can run simultaneously!

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
lsof -i :5433

# Kill the process
lsof -ti:5433 | xargs kill -9
```

### Connection Refused

1. **Check EC2 to RDS connectivity** - SSH into EC2 and try connecting to RDS directly
2. **Verify RDS security group** - Must allow connections from EC2's security group
3. **Check RDS is publicly accessible** - If not, EC2 must be in same VPC

### SSH Key Permission Issues

```bash
chmod 400 ~/.ssh/trading-platform-key.pem
```

## AWS Security Group Configuration

### RDS Security Group

Add an inbound rule:
- **Type**: PostgreSQL (or MySQL/etc.)
- **Port**: 5432 (or your RDS port)
- **Source**: EC2 instance's security group ID (e.g., `sg-xxxxxxxxx`)

### EC2 Security Group

Should already allow SSH (port 22) from your IP.

## Alternative: Background Tunnel

To run the tunnel in the background:

```bash
# Start in background
ssh -i ~/.ssh/trading-platform-key.pem \
    -L 5433:your-rds-endpoint.rds.amazonaws.com:5432 \
    -N -f \
    ubuntu@65.2.153.114

# Find and kill later
ps aux | grep ssh
kill <pid>
```

## Notes

- The tunnel must remain active while you're connected to RDS
- If the tunnel disconnects, your database connection will fail
- Consider using `autossh` for automatic reconnection in production
