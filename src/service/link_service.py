from src.core.security import SecurityManager
from src.database.repository import LinkRepository
from src.core.exceptions import ValidationError, SaveLinksError
from src.core.logger import logger

class LinkService:
    """Business logic for handling users and links."""

    def __init__(self, repository: LinkRepository):
        self.repository = repository

    def register_user(self, username, password):
        """Registers a new user."""
        if not username or not password:
            raise ValidationError("Username and password cannot be empty.")
        
        salt = SecurityManager.generate_salt()
        key = SecurityManager.derive_key(password, salt)
        verifier = SecurityManager.hash_key(key)
        
        try:
            self.repository.add_user(username, salt, verifier)
            logger.info(f"User '{username}' registered successfully.")
            return True
        except Exception as e:
            logger.error(f"Registration failed for user '{username}': {e}")
            raise SaveLinksError("Registration failed. Username might be taken.")

    def login_user(self, username, password):
        """Authenticates a user and returns (user_id, key)."""
        if not username or not password:
            raise ValidationError("Username and password cannot be empty.")

        try:
            user_data = self.repository.get_user_credentials(username)
            if not user_data:
                raise ValidationError("User not found.")
            
            user_id, salt, stored_verifier = user_data
            key = SecurityManager.derive_key(password, salt)
            computed_verifier = SecurityManager.hash_key(key)
            
            if computed_verifier != stored_verifier:
                logger.warning(f"Failed login attempt for user '{username}'")
                raise ValidationError("Invalid password.")
            
            logger.info(f"User '{username}' logged in successfully.")
            return user_id, key
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Login error for '{username}': {e}")
            raise SaveLinksError("Login failed due to system error.")

    def add_link(self, user_id, key, topic, link):
        """Encrypts and adds a link."""
        if not topic or not link:
            raise ValidationError("Topic and link cannot be empty.")
        
        try:
            # Format: topic|link
            data = f"{topic}|{link}".encode('utf-8')
            encrypted_data = SecurityManager.encrypt(data, key)
            self.repository.add_link(user_id, encrypted_data)
            logger.info(f"Link added for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to add link: {e}")
            raise SaveLinksError("Could not save link.")

    def search_links(self, user_id, key, query):
        """Searches for links matching the query (decrypts in memory)."""
        query = query.lower()
        results = []
        
        try:
            encrypted_links = self.repository.get_links(user_id)
            for link_id, encrypted_blob in encrypted_links:
                try:
                    decrypted_bytes = SecurityManager.decrypt(encrypted_blob, key)
                    decrypted_text = decrypted_bytes.decode('utf-8')
                    if "|" in decrypted_text:
                        topic, link = decrypted_text.split("|", 1)
                        if query in topic.lower():
                            results.append({"id": link_id, "topic": topic, "link": link})
                except Exception as e:
                    logger.warning(f"Failed to decrypt link {link_id}: {e}")
                    continue
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise SaveLinksError("Search operation failed.")

    def delete_link(self, user_id, link_id):
        """Deletes a link by ID."""
        try:
            self.repository.delete_link(link_id, user_id)
            logger.info(f"Link {link_id} deleted for user {user_id}")
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise SaveLinksError("Could not delete link.")
