# Secure Startup Vault

Secure Startup Vault is a modern, secure document management platform built for startups and growing teams. It combines strong encryption, role-based access, personal and company vaults, and a polished user experience to help organizations protect sensitive files without sacrificing usability.

## 🌟 Why this project matters

Startups often deal with contracts, financial records, product plans, and intellectual property that must stay private and controlled. Secure Startup Vault provides a simple and secure way to store, manage, and share sensitive documents while keeping access under clear permissions.

## ✨ Key Features

- End-to-end encryption for uploaded files
- Personal vaults for individual document storage
- Company vaults with role-based access control
- Activity logging and audit-friendly file tracking
- Clean dashboard experience for daily usage
- Support for secure upload and download workflows

## 🛠️ Tech Stack

- Python 3.10+
- Flask
- SQLAlchemy
- PostgreSQL / SQLite support
- Bootstrap-based UI
- Flask-WTF for forms

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or newer
- pip
- A virtual environment tool such as venv

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/kpharenraj/secure_startup_vault_web.git
   cd secure_startup_vault
   ```

2. Create and activate a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
   On Windows:
   ```bash
   venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application
   ```bash
   python run.py
   ```

5. Open your browser and visit:
   ```text
   http://127.0.0.1:5000
   ```

## 📁 Project Structure

- `vault/` – Main Flask application package
- `vault/templates/` – HTML templates for the web interface
- `vault/static/` – CSS, JavaScript, and image assets
- `migrations/` – Database migration files
- `tests/` – Automated test coverage for key functionality

## 🔐 Security Notes

This project is designed with security in mind, but it should still be reviewed and hardened before production use. Always keep secrets, keys, and environment settings protected and use strong deployment practices.

## 🧪 Testing

Run the test suite with:

```bash
python -m unittest discover -s tests
```

## 🤝 Contributing

Contributions are welcome. If you would like to improve the project, please open an issue or submit a pull request with a clear description of your changes.

## 📄 License

This project is protected by a proprietary license. Reuse, copying, modification, merging, publishing, distribution, sublicensing, or selling of this software is allowed only with explicit written permission from the copyright owner.

## 👨‍💻 Created By

- K P Haren Raj