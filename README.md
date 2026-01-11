# 🔒 SaveLinks

![Python](https://img.shields.io/badge/Python-3.9-blue?style=for-the-badge&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey?style=for-the-badge)

**SaveLinks** is a secure, CLI-based password manager and topic saver. It encrypts your sensitive links and notes locally using AES-256 encryption, ensuring your data remains private and hidden.

---

## ✨ Features

* **🔐 Strong Encryption:** Uses `Fernet` (AES-256) implementation from the `cryptography` library.
* **💾 Local Storage:** Data is stored in a hidden directory (`~/.hidden_topics`), keeping your folder clean.
* **🐳 Dockerized:** Run securely in a container without installing Python.
* **⚡ Fast Operations:** Add, Search, and Delete topics instantly via CLI.
* **📦 Portable:** Available as a standalone `.exe` for Windows users.

---

## 🚀 Getting Started

You can run SaveLinks in three ways. Choose the one that fits you best!

## Option 1: Standalone Application (Easiest)
No installation required. Perfect for Windows users.
1. Go to the [Releases Page](../../releases).
2. Download **`SaveLinks.exe`**.
3. Double-click to run!

## Option 2: Run with Docker (Recommended for Security)
Keep your host system clean by running the app in a container.

**1. Build the Image**
```bash
docker build -t savelinks .
```
**2. Run the Container (This command mounts a volume so your data persists even after closing Docker)**



### Windows (PowerShell)
```Bash
docker run -it -v ${PWD}/data:/root/.hidden_topics savelinks
```

### Linux / Mac
```Bash
docker run -it -v $(pwd)/data:/root/.hidden_topics savelinks
```
## Option 3: Run from Source (Python)
If you want to modify the code or run it natively.

**1. Clone the repo:**

```Bash

git clone [https://github.com/ahvcxa/SaveLinks.git](https://github.com/ahvcxa/SaveLinks.git)
cd SaveLinks
```
**2. Install dependencies:**

```Bash

pip install -r requirements.txt
```
**3. Run the app:**
python main.py

## 🛠️ Project Structure


```Bash

SaveLinks/
├── main.py            # Main application logic
├── requirements.txt   # Python dependencies
├── Dockerfile         # Docker configuration
├── app.ico            # Application icon
└── README.md          # Project documentation
```
## 🛡️ Security Note
Warning: Your master password is used to generate the encryption key. Do not lose your password. Without it, the encrypted file cannot be recovered.

## 🤝 Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

*Developed by Batuhan İNAN*
