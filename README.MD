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

### Python

1. Clone the repository:
   `git clone https://github.com/emilycodestar/cmd-chat.git`
   `cd cmd-chat`

2. Create a virtual environment and install dependencies:

   Linux / macOS:
   `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt`

   Windows (PowerShell):
   `python -m venv venv ; .\venv\Scripts\activate ; pip install -r requirements.txt`

3. Start the server (set a password for client connections):
   `python cmd_chat.py serve 0.0.0.0 1000 --password YOUR_PASSWORD`

4. Connect a client:
   `python cmd_chat.py connect SERVER_IP 1000 USERNAME YOUR_PASSWORD`

   Example (local run):
   `python cmd_chat.py connect localhost 1000 tyler YOUR_PASSWORD`

---

## 🎥 Example

Here’s how it looks in action:

![Example](example.gif)
