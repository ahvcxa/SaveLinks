import os
import getpass
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64

# Function to clear the console
def clear_console():
    os.system("cls" if os.name == "nt" else "clear")

# Derive a key from the user's password
def derive_key(password, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

# Encrypt a file
def encrypt_file(file_name, key):
    fernet = Fernet(key)
    with open(file_name, "rb") as file:
        original_data = file.read()
    encrypted_data = fernet.encrypt(original_data)
    with open(file_name, "wb") as file:
        file.write(encrypted_data)

# Decrypt a file
def decrypt_file(file_name, key):
    fernet = Fernet(key)
    with open(file_name, "rb") as file:
        encrypted_data = file.read()
    decrypted_data = fernet.decrypt(encrypted_data)
    with open(file_name, "wb") as file:
        file.write(decrypted_data)

# Add a topic to the file
def add_topic_to_file(file_name, key):
    while True:
        clear_console()
        print("Add a new topic and link (type 'q' to quit):")
        topic = input("Topic: ")
        if topic.lower() == 'q':
            print("Exiting...")
            break

        link = input("Link: ")

        # Decrypt the file before appending data
        if os.path.exists(file_name):
            decrypt_file(file_name, key)

        # Append the new topic and link
        with open(file_name, "a", encoding="utf-8") as file:
            file.write(f"{topic}|{link}\n")

        # Encrypt the file after appending data
        encrypt_file(file_name, key)

        print("Topic and link successfully added!\n")
        input("Press Enter to continue...")

# Search for a topic in the file
def search_topic_in_file(file_name, key):
    clear_console()
    print("Search for a topic (partial names allowed):")
    search_query = input("Enter a keyword: ").lower()

    try:
        # Decrypt the file before reading
        if os.path.exists(file_name):
            decrypt_file(file_name, key)

        with open(file_name, "r", encoding="utf-8") as file:
            found = False
            print("\nSearch Results:")
            print("-" * 30)
            for line in file:
                if "|" in line:
                    topic, link = line.strip().split("|")
                    if search_query in topic.lower():
                        print(f"Topic: {topic}\nLink: {link}\n")
                        found = True

            if not found:
                print("No matching topics found.\n")
            print("-" * 30)

        # Encrypt the file after reading
        encrypt_file(file_name, key)

    except FileNotFoundError:
        print("File not found. Please add a topic and link first.\n")
    except InvalidToken:
        print("Invalid password! Cannot decrypt the file.\n")

    input("Press Enter to return to the menu...")

# Delete a topic from the file
def delete_topic_from_file(file_name, key):
    clear_console()
    print("Delete a topic:")
    topic_to_delete = input("Enter the exact topic name to delete: ").lower()

    try:
        # Decrypt the file before editing
        if os.path.exists(file_name):
            decrypt_file(file_name, key)

        with open(file_name, "r", encoding="utf-8") as file:
            lines = file.readlines()

        # Check if the file is empty
        if not lines:
            print("The file is empty. No topics to delete.")
            input("Press Enter to return to the menu...")
            return

        with open(file_name, "w", encoding="utf-8") as file:
            found = False
            for line in lines:
                if "|" in line:
                    topic, link = line.strip().split("|")
                    if topic.lower() == topic_to_delete:
                        found = True
                        print(f"Deleted: {topic} | {link}")
                        continue
                    file.write(line)

            if not found:
                print("No matching topic found to delete.")

        # Encrypt the file after editing
        encrypt_file(file_name, key)

    except FileNotFoundError:
        print("File not found. Please add a topic and link first.")
    except InvalidToken:
        print("Invalid password! Cannot decrypt the file.")
    except Exception as e:
        print(f"An error occurred: {e}")

    input("Press Enter to return to the menu...")

# Main function
def main():
    # Gizli bir dizin oluştur
    hidden_dir = os.path.expanduser("~/.hidden_topics")
    if not os.path.exists(hidden_dir):
        os.makedirs(hidden_dir)

    file_name = os.path.join(hidden_dir, ".topics.txt")
    salt = b"salt_value"  # Sabit bir salt değeri (gerçek uygulamada rastgele olmalı)

    # Ask the user for a password (hidden input)
    while True:
        password = getpass.getpass("Enter your password: ")  # Şifreyi gizli bir şekilde al
        key = derive_key(password, salt)  # Şifreden anahtar türet

        # Test if the password is correct by trying to decrypt the file
        if os.path.exists(file_name):
            try:
                with open(file_name, "rb") as file:
                    encrypted_data = file.read()
                Fernet(key).decrypt(encrypted_data)  # Şifre çözme testi
                break  # Şifre doğru, döngüden çık
            except InvalidToken:
                print("Invalid password! Please try again.\n")
        else:
            break  # Dosya yok, şifre doğrulama atlanır

    while True:
        clear_console()
        print("Menu:")
        print("1. Add a topic and link")
        print("2. Search for a topic")
        print("3. Delete a topic")
        print("4. Exit")
        choice = input("Enter your choice (1/2/3/4): ")

        if choice == "1":
            add_topic_to_file(file_name, key)
        elif choice == "2":
            search_topic_in_file(file_name, key)
        elif choice == "3":
            delete_topic_from_file(file_name, key)
        elif choice == "4":
            print("Exiting program...")
            break
        else:
            print("Invalid choice! Please try again.\n")
            input("Press Enter to continue...")

# Run the program
if __name__ == "__main__":
    main()