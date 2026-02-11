import getpass
import os
import sys
from src.service.link_service import LinkService
from src.core.exceptions import SaveLinksError, ValidationError

class CLI:
    """Command Line Interface for SaveLinks."""

    def __init__(self, service: LinkService):
        self.service = service
        self.user_id = None
        self.key = None

    def clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def print_header(self):
        print("========================================")
        print("          SAVE LINKS - SECURE           ")
        print("========================================")

    def start(self):
        """Main entry point for the CLI."""
        while True:
            self.clear_screen()
            self.print_header()
            print("1. Login")
            print("2. Register")
            print("3. Exit")
            
            choice = input("\nSelect an option: ")

            if choice == "1":
                self.login_flow()
            elif choice == "2":
                self.register_flow()
            elif choice == "3":
                print("Goodbye!")
                sys.exit(0)
            else:
                input("Invalid option. Press Enter to try again...")

    def login_flow(self):
        print("\n--- LOGIN ---")
        username = input("Username: ")
        password = getpass.getpass("Password: ")

        try:
            self.user_id, self.key = self.service.login_user(username, password)
            self.main_menu()
        except SaveLinksError as e:
            print(f"\nError: {e}")
            input("Press Enter to continue...")
        except ValidationError as e:
            print(f"\nValidation Error: {e}")
            input("Press Enter to continue...")

    def register_flow(self):
        print("\n--- REGISTER ---")
        username = input("Choose a Username: ")
        password = getpass.getpass("Choose a Password: ")
        confirm_password = getpass.getpass("Confirm Password: ")

        if password != confirm_password:
            print("\nError: Passwords do not match.")
            input("Press Enter to continue...")
            return

        try:
            self.service.register_user(username, password)
            print("\nRegistration successful! You can now login.")
            input("Press Enter to continue...")
        except SaveLinksError as e:
            print(f"\nError: {e}")
            input("Press Enter to continue...")

    def main_menu(self):
        while True:
            self.clear_screen()
            self.print_header()
            print(f"Logged in as User #{self.user_id}")
            print("----------------------------------------")
            print("1. Add New Link")
            print("2. Search Links")
            print("3. Delete Link")
            print("4. Logout")

            choice = input("\nSelect an option: ")

            if choice == "1":
                self.add_link_flow()
            elif choice == "2":
                self.search_link_flow()
            elif choice == "3":
                self.delete_link_flow()
            elif choice == "4":
                self.user_id = None
                self.key = None
                return
            else:
                input("Invalid option. Press Enter to try again...")

    def add_link_flow(self):
        print("\n--- ADD LINK ---")
        topic = input("Topic: ")
        link = input("Link: ")

        try:
            self.service.add_link(self.user_id, self.key, topic, link)
            print("\nLink added successfully!")
        except Exception as e:
            print(f"\nError: {e}")
        
        input("Press Enter to continue...")

    def search_link_flow(self):
        print("\n--- SEARCH LINKS ---")
        query = input("Search query: ")

        try:
            results = self.service.search_links(self.user_id, self.key, query)
            if not results:
                print("\nNo links found.")
            else:
                print(f"\nFound {len(results)} results:")
                print("-" * 40)
                for res in results:
                    print(f"ID: {res['id']}")
                    print(f"Topic: {res['topic']}")
                    print(f"Link: {res['link']}")
                    print("-" * 40)
        except Exception as e:
            print(f"\nError: {e}")

        input("Press Enter to continue...")

    def delete_link_flow(self):
        print("\n--- DELETE LINK ---")
        try:
            link_id = int(input("Enter Link ID to delete: "))
            self.service.delete_link(self.user_id, link_id)
            print("\nLink deleted successfully (if it existed).")
        except ValueError:
            print("\nError: Invalid ID format.")
        except Exception as e:
            print(f"\nError: {e}")

        input("Press Enter to continue...")
