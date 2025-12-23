# Connect to EC2 PostgreSQL using pgAdmin with SSH Tunnel

## Overview

pgAdmin 4 has **built-in SSH tunnel support** - no need for separate terminal commands! This is the easiest way to connect to your EC2 PostgreSQL database.

---

## Step 1: Install pgAdmin

### macOS Installation

```bash
# Option A: Using Homebrew (Recommended)
brew install --cask pgadmin4

# Option B: Download from website
# Visit: https://www.pgadmin.org/download/pgadmin-4-macos/
```

### Launch pgAdmin

```bash
# Open pgAdmin
open -a pgAdmin\ 4

# Or find it in Applications folder
```

---

## Step 2: Create New Server Connection

### 2.1 Open Connection Dialog

1. **Open pgAdmin 4**
2. Right-click on **"Servers"** in the left panel
3. Select **"Register" → "Server..."**

### 2.2 General Tab

Fill in these details:

| Field | Value |
|-------|-------|
| **Name** | `Trading Platform EC2` |
| **Server group** | `Servers` (default) |
| **Comments** | `PostgreSQL on EC2 with TimescaleDB` |

### 2.3 Connection Tab

Fill in these details:

| Field | Value |
|-------|-------|
| **Host name/address** | `localhost` |
| **Port** | `5432` |
| **Maintenance database** | `trading_db` |
| **Username** | `trading_user` |
| **Password** | `YourSecurePassword123!` |
| **Save password?** | ✅ Check this |

### 2.4 SSH Tunnel Tab ⭐ (Most Important!)

Click on the **"SSH Tunnel"** tab and fill in:

| Field | Value |
|-------|-------|
| **Use SSH tunneling** | ✅ Check this |
| **Tunnel host** | `65.2.153.114` |
| **Tunnel port** | `22` |
| **Username** | `ubuntu` |
| **Authentication** | Select **"Identity file"** |
| **Identity file** | Click **Browse** → Select `/Users/faizanuddinmorkas/.ssh/trading-platform-key.pem` |
| **Password** | Leave empty (using key file) |

### 2.5 Advanced Tab (Optional)

| Field | Value |
|-------|-------|
| **DB restriction** | `trading_db` |

### 2.6 Save Connection

Click **"Save"** button at the bottom.

---

## Step 3: Connect to Database

1. In the left panel, expand **"Servers"**
2. Click on **"Trading Platform EC2"**
3. It will automatically:
   - ✅ Create SSH tunnel using your key
   - ✅ Connect to PostgreSQL
   - ✅ Show all databases and tables

---

## Step 4: Verify Connection

### Check TimescaleDB Extension

1. Expand: **Trading Platform EC2** → **Databases** → **trading_db** → **Extensions**
2. You should see **timescaledb** listed

### View Tables

1. Expand: **Schemas** → **public** → **Tables**
2. You should see:
   - `ohlcv`
   - `signals`
   - `trades`
   - `positions`

### Run Test Query

1. Right-click on **trading_db**
2. Select **"Query Tool"**
3. Run this query:

```sql
-- Test connection
SELECT version();

-- Check TimescaleDB
SELECT extversion FROM pg_extension WHERE extname='timescaledb';

-- List all tables
SELECT tablename FROM pg_tables WHERE schemaname='public';

-- Check OHLCV table structure
\d ohlcv
```

---

## Visual Guide (Screenshots Reference)

### Connection Dialog - General Tab
```
┌─────────────────────────────────────────┐
│ General                                 │
├─────────────────────────────────────────┤
│ Name: Trading Platform EC2              │
│ Server group: Servers                   │
│ Comments: PostgreSQL on EC2             │
└─────────────────────────────────────────┘
```

### Connection Dialog - Connection Tab
```
┌─────────────────────────────────────────┐
│ Connection                              │
├─────────────────────────────────────────┤
│ Host: localhost                         │
│ Port: 5432                              │
│ Maintenance database: trading_db        │
│ Username: trading_user                  │
│ Password: ••••••••••••                  │
│ ☑ Save password?                        │
└─────────────────────────────────────────┘
```

### Connection Dialog - SSH Tunnel Tab ⭐
```
┌─────────────────────────────────────────┐
│ SSH Tunnel                              │
├─────────────────────────────────────────┤
│ ☑ Use SSH tunneling                     │
│ Tunnel host: 65.2.153.114             │
│ Tunnel port: 22                         │
│ Username: ubuntu                        │
│ Authentication: Identity file           │
│ Identity file: [Browse...]              │
│   ~/.ssh/trading-platform-key.pem       │
└─────────────────────────────────────────┘
```

---

## Common Issues & Solutions

### Issue 1: "Identity file not found"

**Solution:**
```bash
# Verify key exists
ls -la ~/.ssh/trading-platform-key.pem

# Check permissions
chmod 400 ~/.ssh/trading-platform-key.pem
```

### Issue 2: "Connection refused"

**Solution:**
1. Check PostgreSQL is running on EC2:
   ```bash
   ssh -i ~/.ssh/trading-platform-key.pem ubuntu@65.2.153.114 "sudo systemctl status postgresql"
   ```

2. Verify PostgreSQL is listening:
   ```bash
   ssh -i ~/.ssh/trading-platform-key.pem ubuntu@65.2.153.114 "sudo netstat -plnt | grep 5432"
   ```

### Issue 3: "Authentication failed"

**Solution:**
- Double-check username: `trading_user`
- Double-check password
- Verify user exists on EC2:
  ```bash
  ssh -i ~/.ssh/trading-platform-key.pem ubuntu@65.2.153.114
  sudo -u postgres psql -c "\du"
  ```

### Issue 4: "SSH tunnel failed"

**Solution:**
- Verify EC2 IP: `65.2.153.114`
- Check security group allows SSH (port 22)
- Test SSH connection manually:
  ```bash
  ssh -i ~/.ssh/trading-platform-key.pem ubuntu@65.2.153.114
  ```

---

## Alternative: DBeaver (Another Great Option)

If you prefer DBeaver over pgAdmin:

### Install DBeaver
```bash
brew install --cask dbeaver-community
```

### Configure SSH Tunnel in DBeaver

1. **Create New Connection** → Select **PostgreSQL**
2. **Main Tab:**
   - Host: `localhost`
   - Port: `5432`
   - Database: `trading_db`
   - Username: `trading_user`
   - Password: `YourSecurePassword123!`

3. **SSH Tab:**
   - ✅ Use SSH Tunnel
   - Host/IP: `65.2.153.114`
   - Port: `22`
   - User Name: `ubuntu`
   - Authentication Method: **Public Key**
   - Private Key: Browse to `~/.ssh/trading-platform-key.pem`

4. **Test Connection** → **Finish**

---

## Advantages of pgAdmin/DBeaver

✅ **No command-line needed** - GUI-based  
✅ **Built-in SSH tunnel** - automatic connection  
✅ **Visual query builder** - easier than writing SQL  
✅ **Table browser** - see data in grid format  
✅ **Query history** - save and reuse queries  
✅ **Export data** - CSV, JSON, Excel formats  
✅ **ERD diagrams** - visualize table relationships  
✅ **Backup/Restore** - GUI-based tools  

---

## Useful pgAdmin Features

### 1. Query Tool
- Right-click database → **Query Tool**
- Write and execute SQL queries
- View results in grid format
- Export results to CSV/JSON

### 2. View/Edit Data
- Right-click table → **View/Edit Data** → **All Rows**
- See data in spreadsheet format
- Edit data directly (be careful!)
- Filter and sort columns

### 3. Backup Database
- Right-click database → **Backup...**
- Choose format (Custom, Tar, Plain)
- Select backup location
- Click **Backup**

### 4. Restore Database
- Right-click database → **Restore...**
- Select backup file
- Click **Restore**

### 5. Import/Export Data
- Right-click table → **Import/Export Data...**
- Import from CSV
- Export to CSV/JSON

### 6. Monitor Queries
- **Tools** → **Server Activity**
- See active queries
- Kill long-running queries

---

## Quick Reference

### Connection Details Summary

| Setting | Value |
|---------|-------|
| **pgAdmin Name** | Trading Platform EC2 |
| **Database Host** | localhost (via tunnel) |
| **Database Port** | 5432 |
| **Database Name** | trading_db |
| **Database User** | trading_user |
| **Database Password** | YourSecurePassword123! |
| **SSH Tunnel Host** | 65.2.153.114 |
| **SSH Port** | 22 |
| **SSH User** | ubuntu |
| **SSH Key** | ~/.ssh/trading-platform-key.pem |

---

## Next Steps

After connecting with pgAdmin:

1. ✅ Browse your tables (ohlcv, signals, trades, positions)
2. ✅ Run test queries
3. ✅ Insert sample data
4. ✅ Create visualizations
5. ✅ Set up scheduled backups
6. ✅ Start building your Python trading application

---

## Summary

**pgAdmin is the easiest way to connect!**

- ✅ No terminal commands needed
- ✅ Built-in SSH tunnel support
- ✅ Uses your SSH key automatically
- ✅ Visual interface for everything
- ✅ Perfect for development and testing

Just install pgAdmin, configure the connection with your SSH key, and you're ready to go! 🚀
