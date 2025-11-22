from .user import User

class Admin(User):
    DEFAULT_PROFILE_PIC = 'uploads/default pfp.jpg'

    def __init__(self, username, email, password, job):
        super().__init__(username, email, password)
        self.__job = job
        self.profile_picture = Admin.DEFAULT_PROFILE_PIC

    def get_job(self):
        return self.__job

    def set_job(self, job):
        self.__job = job

    def get_user_type(self):
        return 'Admin'