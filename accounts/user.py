import uuid
from datetime import datetime
class User:

    def __init__(self, username, email, password):
        self.__user_id = uuid.uuid4()
        self.__username = username
        self.__email = email
        self.__password = password
        self.page_views = 0
        self.created_at = datetime.now()

    def get_user_id(self):
        return self.__user_id

    def get_username(self):
        return self.__username

    def get_password(self):
        return self.__password
    
    def get_email(self):
        return self.__email

    def set_username(self, username):
        self.__username = username

    def set_password(self, password):
        self.__password = password

    def set_email(self, email):
        self.__email = email

    def log_page_view(self):
        self.page_views += 1

    def get_page_views(self):
        return self.page_views
      
    def get_creation_date(self):
        return self.created_at