# Quick Start: Access RDS from Local Machine

## Choose Your Method

### Method 1: SSH Tunnel (Recommended) 🔒
**More secure** - RDS stays private, accessed through EC2

1. **Get your public IP** (for whitelisting):
   ```bash
   ./scripts/get-my-ip.sh
   ```

2. **Configure AWS Security Groups**:
   - Go to **AWS Console → RDS → Your Database**
   - Click **VPC security group** → **Edit inbound rules** → **Add rule**:
     - Type: PostgreSQL
     - Port: 5432
     - Source: Your **EC2 security group ID** (e.g., `sg-xxxxx`)

3. **Update connection script**:
   Edit `scripts/connect-rds.sh` with your RDS details:
   ```bash
   RDS_ENDPOINT="your-db.xxxxx.region.rds.amazonaws.com"
   DB_NAME="your_database"
   DB_USER="your_user"
   ```

4. **Start tunnel**:
   ```bash
   ./scripts/connect-rds.sh
   ```
   Keep this terminal open!

5. **Connect** (in new terminal):
   ```bash
   psql -h localhost -p 5433 -U your_user -d your_database
   ```

---

### Method 2: Direct Connection 🌐
**Simpler** - Direct connection to RDS over internet

1. **Get your public IP**:
   ```bash
   ./scripts/get-my-ip.sh
   ```

2. **Enable RDS Public Access**:
   - AWS Console → RDS → Your Database → **Modify**
   - Set **Public access** to **Yes**
   - Apply immediately

3. **Configure Security Group**:
   - Click **VPC security group** → **Edit inbound rules** → **Add rule**:
     - Type: PostgreSQL
     - Port: 5432
     - Source: **My IP** (or paste IP from step 1)

4. **Update connection script**:
   Edit `scripts/connect-rds-direct.sh` with your RDS details

5. **Connect**:
   ```bash
   ./scripts/connect-rds-direct.sh
   ```

---

## Available Scripts

| Script | Purpose |
|--------|---------|
| `connect-postgres.sh` | Connect to PostgreSQL on EC2 |
| `connect-rds.sh` | Connect to RDS via SSH tunnel |
| `connect-rds-direct.sh` | Connect directly to RDS |
| `get-my-ip.sh` | Get your public IP for whitelisting |

---

## Troubleshooting

**Connection timeout?**
- Check security group configuration
- Verify RDS is publicly accessible (for direct method)
- See `rds_troubleshooting.md` for detailed help

**Port already in use?**
```bash
lsof -ti:5433 | xargs kill -9
```

---

## Full Documentation

- **Setup Guide**: `docs/RDS_LOCAL_ACCESS.md`
- **Troubleshooting**: `rds_troubleshooting.md` (in artifacts)
- **SSH Tunnel Details**: `docs/RDS_SSH_TUNNEL.md`
