# 🔐 Passman - Secure Password Manager

A local, encrypted password manager with anti-brute force protection.

## Features

- 🔒 **AES-256 Encryption** with PBKDF2 (100,000 iterations)
- 🛡️ **Anti-Brute Force** - 5 attempts, 5 minute lockout
- 🎨 **Modern Dark UI** - Easy on the eyes
- 🔑 **Password Generator** - Secure random passwords
- 📋 **Copy to Clipboard** - Double-click or button
- 🔍 **Real-time Search** - Find passwords instantly
- 💾 **Local Storage** - Your data never leaves your computer

## Installation

```bash
git clone https://github.com/yourusername/passman
cd passman
pip install -r requirements.txt
python passman.py
```
Usage

    First run - Set your master password

    Add passwords - Click "Add" button

    Search - Type in search box

    Copy - Double-click any entry

    View/Hide - Toggle password visibility

Security

    Master password never stored

    AES-256 encryption (military grade)

    PBKDF2 key derivation (100,000 iterations)

    Rate limiting: 5 attempts, 5 min lockout

    Local storage only - no cloud, no telemetry

Requirements

    Python 3.7+

    cryptography

    pyperclip
