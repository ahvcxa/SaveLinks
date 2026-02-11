# SaveLinks - Secure Private Link Saver

Refactored professional version of SaveLinks with layered architecture and enhanced security.

## Features
- **Secure**: Uses PBKDF2HMAC for key derivation and Fernet (AES-128 in CBC mode) for encryption.
- **Private**: Zero-Knowledge architecture. Your password never leaves memory and is not stored directly.
- **Database**: efficient SQLite storage.
- **Structured**: Clean code architecture (UI, Service, Repository, Core).

## Installation

1.  Clone or download the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the application:
```bash
python run.py
```

### Menu Options
1.  **Login**: Access your existing links.
2.  **Register**: Create a new account (local).
3.  **Exit**: Close the application.

Once logged in:
-   **Add Link**: Store a new topic and link.
-   **Search**: Find links by topic name.
-   **Delete**: Remove a link by ID.
