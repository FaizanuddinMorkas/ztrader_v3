# RDS Local Access Guide

Two ways to connect to RDS from your local machine:

## Option 1: SSH Tunnel via EC2 (Recommended ⭐)

**Pros:**
- ✅ More secure (RDS doesn't need to be publicly accessible)
- ✅ Uses existing EC2 instance
- ✅ No need to whitelist your home IP

**Cons:**
- ❌ Requires EC2 instance running
- ❌ Slightly more complex setup

### Setup Steps

#### 1. Configure RDS Security Group
Allow EC2 to access RDS:
- Go to **AWS Console → RDS → Your Database → Connectivity & security**
- Click the **VPC security group** link
- **Edit inbound rules** → **Add rule**:
  - Type: PostgreSQL
  - Port: 5432
  - Source: Your **EC2 security group ID** (e.g., `sg-xxxxx`)
- Save rules

#### 2. Update Connection Script
Edit `scripts/connect-rds.sh` with your RDS details:

```bash
RDS_ENDPOINT="your-db.xxxx.region.rds.amazonaws.com"
RDS_PORT=5432
DB_NAME="your_database"
DB_USER="your_user"
```

#### 3. Start the Tunnel
```bash
./scripts/connect-rds.sh
```

Keep this terminal open!

#### 4. Connect from Local Machine
In a **new terminal**:

```bash
# Using psql
psql -h localhost -p 5433 -U your_user -d your_database

# Using Python
python3 << EOF
import psycopg2
conn = psycopg2.connect(
    host='localhost',
    port=5433,
    database='your_database',
    user='your_user',
    password='your_password'
)
print('✅ Connected to RDS!')
conn.close()
EOF
```

---

## Option 2: Direct Connection (Simpler but Less Secure)

**Pros:**
- ✅ Simpler - no tunnel needed
- ✅ Direct connection
- ✅ No EC2 required

**Cons:**
- ❌ RDS exposed to internet
- ❌ Need to whitelist your IP
- ❌ IP changes require security group updates
- ❌ Less secure

### Setup Steps

#### 1. Enable Public Access
- Go to **AWS Console → RDS → Your Database**
- Click **Modify**
- Under **Connectivity**, set **Public access** to **Yes**
- Click **Continue** → **Apply immediately** → **Modify DB instance**
- Wait for modification to complete (~5 minutes)

#### 2. Get Your Public IP
```bash
curl ifconfig.me
```

#### 3. Configure RDS Security Group
Allow your local machine to access RDS:
- Go to **RDS → Your Database → Connectivity & security**
- Click the **VPC security group** link
- **Edit inbound rules** → **Add rule**:
  - Type: PostgreSQL
  - Port: 5432
  - Source: **My IP** (or paste your IP from step 2 with `/32`)
  - Description: "My local machine"
- Save rules

#### 4. Connect Directly
```bash
# Get RDS endpoint from AWS Console
RDS_ENDPOINT="your-db.xxxx.region.rds.amazonaws.com"

# Connect with psql
psql -h $RDS_ENDPOINT -p 5432 -U your_user -d your_database

# Or with Python
python3 << EOF
import psycopg2
conn = psycopg2.connect(
    host='$RDS_ENDPOINT',
    port=5432,
    database='your_database',
    user='your_user',
    password='your_password'
)
print('✅ Connected to RDS!')
conn.close()
EOF
```

---

## Troubleshooting

### Connection Timeout
- **Check security group** - Most common issue
- **Verify RDS is publicly accessible** (for direct connection)
- **Check your IP hasn't changed** (for direct connection)
- See `rds_troubleshooting.md` for detailed steps

### Port Already in Use (Tunnel)
```bash
# Kill existing tunnel
lsof -ti:5433 | xargs kill -9
```

### Test Connectivity
```bash
# From EC2 (for tunnel method)
ssh -i ~/.ssh/trading-platform-key.pem ubuntu@65.2.153.114
nc -zv your-rds-endpoint.rds.amazonaws.com 5432

# From local machine (for direct method)
nc -zv your-rds-endpoint.rds.amazonaws.com 5432
```

---

## Recommendation

**Use Option 1 (SSH Tunnel)** because:
1. More secure - RDS not exposed to internet
2. No IP whitelisting needed
3. Better for production use

**Use Option 2 (Direct)** only if:
1. You need quick testing
2. EC2 instance is not available
3. You understand the security implications

---

## Quick Reference

### SSH Tunnel Method
```bash
# Terminal 1: Start tunnel
./scripts/connect-rds.sh

# Terminal 2: Connect
psql -h localhost -p 5433 -U user -d database
```

### Direct Method
```bash
psql -h your-rds-endpoint.rds.amazonaws.com -p 5432 -U user -d database
```
