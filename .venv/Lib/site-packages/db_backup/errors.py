class FailedBackup(Exception):
    """Base Exception for backup/restore related exceptions"""

class NoCommand(FailedBackup):
    """Called when the necessary command for dumping doesn't exist"""

class FailedToRun(FailedBackup):
    """Exception that is raised when we can't dump the database"""
    def __init__(self, message, exit_code):
        super(FailedToRun, self).__init__(message)
        self.exit_code = exit_code

class FailedEncryption(FailedBackup):
    """Exception for when we can't encrypt"""

class GPGFailedToStart(FailedBackup):
    """Exception for when gpg doesn't start"""

class BadBackupFile(FailedBackup):
    """Exception for something wrong with the backup file"""

class NonEmptyDatabase(FailedBackup):
    """Exception for when we restore to a non empty database"""

class NoDBDriver(FailedBackup):
    """Exception for when we don't have a DatabaseDriver object for some engine"""

class NoDatabase(FailedBackup):
    """Exception for when we don't have a Database to work with"""

