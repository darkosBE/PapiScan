# 🌑 PAPISCAN Minecraft Server Scanner

The Offensive Global Minecraft® Server Scanner


> ⚠️ Please: Do not repeat the actions of The Fifth Column. If too many people start doing this, who knows what playing minecraft will be like then.
---

## ✨ Features

- **Scans /21 subnets** (~2,046 IPs) per resolved target — ideal for finding hidden or misconfigured servers  
- **Case-insensitive MOTD filtering** — skip fake, protected, or irrelevant servers using a keyword blacklist  
- **Resolves domains** via `mcsrvstat.us` + DNS fallback  
- **Atomic file locking** — safely removes processed targets from `ips.txt` even with multiple workers  
- **MongoDB integration** — stores server info (IP, version, players, MOTD, timestamp)  
- **Multiprocessing + threading** — leverages all CPU cores and handles I/O efficiently  
- **Fake server detection** — skips servers with malformed JSON or suspicious MOTDs  
- **IPv4-only** — avoids IPv6 complexity and incompatibility  

---

## 🛠️ Requirements

- Python 3.8+
- Packages:
  ```bash
  pip install pymongo requests colorama
  ```

> 💡 No external binaries needed — pure Python + standard library (`socket`, `ipaddress`, `multiprocessing`).

---

## ⚙️ Configuration

Edit these values at the top of `scanner.py`:

| Setting | Description |
|--------|-------------|
| `MONGO_URI` | Your MongoDB Atlas (or local) connection string |
| `FORBIDDEN_KEYWORDS` | List of **lowercase** words to skip in MOTD (e.g., `"protect"`, `"invalid"`) |
| `PING_TIMEOUT` | Seconds to wait per server (default: `1.6`) |
| `IPS_FILE` | Input file (default: `ips.txt`) |

---

## 📁 Input Format (`ips.txt`)

One target per line. Supports:
```
192.168.1.10
104.236.123.45:25565
play.hypixel.net
mc.example.com:25566
```

The scanner will:
1. Resolve domains to IPv4
2. Extract port (default: `25565`)
3. Scan the **/21 subnet** of the resolved IP
4. Remove the line from `ips.txt` **atomically**

---

## ▶️ Usage

1. Create `ips.txt` with your seed targets
2. Run the scanner:
   ```bash
   python3 scanner.py
   ```
3. Results are:
   - Printed to console (`[ONLINE] ...`)
   - Saved to MongoDB (`mcscanner.servers` collection)
   - Skipped servers logged as `[SKIP]`

> ⚠️ **Warning**: Scanning large IP ranges may trigger network abuse alerts. Use responsibly and comply with local laws.

---

## 🧠 How It Works

1. **Read & shuffle** targets from `ips.txt`
2. **Resolve** each to an IPv4 + port
3. **Generate /21 subnet** (e.g., `192.168.0.0/21` → `192.168.0.1` to `192.168.7.254`)
4. **Ping all IPs in parallel** using threaded socket handshakes
5. **Parse valid server responses**, skip fakes
6. **Save clean servers** to MongoDB
7. **Remove processed target** from file (with cross-platform file locking)

---

## 🚫 Blacklisted MOTDs (Case-Insensitive)

Servers with **any** of these words in their MOTD are skipped:
```python
["protect", "docs", "refer", "invalid", "be"]
```

> Example: `"§cServer is protected!"` → contains `"protect"` → **skipped**

Add more words to `FORBIDDEN_KEYWORDS` as needed.

---

## 📦 Output Schema (MongoDB)

Each document in `mcscanner.servers`:
```json
{
  "_id": "192.168.1.100:25565",
  "ip": "192.168.1.100",
  "port": 25565,
  "description": "Welcome to my server!",
  "version": "Paper 1.20.1",
  "players": "12/100",
  "protocol": 763,
  "timestamp": "2025-10-23T12:34:56.789Z"
}
```

---

## 🛡️ Safety & Ethics

- This tool is for **educational and research purposes only**
⚠️ Please: Do not repeat the actions of The Fifth Column. If too many people start doing this, who knows what playing minecraft will be like then.

---

## 🙌 Credits

- Inspired by open-source Minecraft scanners
- Uses `mcsrvstat.us` for domain resolution (fallback: system DNS)
- Built with ❤️ By Syzdark

---

> 🌐 **Use wisely. Scan ethically. Share responsibly.**
