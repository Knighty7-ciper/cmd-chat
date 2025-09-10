# CMD CHAT

**CMD CHAT** is a new milestone in console communication.  
A fully anonymous chat between two clients, impossible to intercept or hand over.  
All data exists only in RAM and is wiped after the session ends.  
No logs, no traces, no compromise.  

---

## 🔒 Key Features

- Full anonymity  
- End-to-End encryption (RSA + symmetric key)  
- Data stored only in memory (RAM), deleted on exit  
- No logging, no persistence on disk  
- Easy to run via Python or CLI  

---

## ⚙️ How It Works

1. The client generates an RSA key pair.  
2. The server creates a symmetric key.  
3. The client sends its public key to the server.  
4. The server encrypts the symmetric key and sends it back.  
5. The client decrypts and confirms the key.  
6. From that point, all communication is done via symmetric encryption.  

Everything happens in memory only. Nothing is written to disk.  

---

## 🚀 Installation & Run

### Option 1: Python  

Install with pip:  
```bash
pip install secured_console_chat
````

Run directly from Python:

```python
import asyncio 
import cmd_chat

if __name__ == '__main__':
    asyncio.run(cmd_chat.run())
```

### Option 2: CLI

Start the server:

```bash
cmd_chat serve localhost 5000
```

Connect to the server:

```bash
cmd_chat connect localhost 5000 tyler
```

---

## 🎥 Example

Here’s how it looks in action:

![Example](example.gif)

