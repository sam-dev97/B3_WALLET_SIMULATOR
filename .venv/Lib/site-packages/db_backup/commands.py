from db_backup.errors import BadBackupFile, NonEmptyDatabase
from db_backup.databases import DatabaseHandler
from db_backup.encryption import Encryptor

import urlparse
import time
import os

def make_backup_filename():
    """Return a string for the filename of a backup"""
    return "db_backup_{0}.gpg".format(time.time())

def backup(database_settings, recipients, backup_dir, filename_maker=None, gpg_home=None):
    """Backup the database into the specified backup_dir for our recipients"""
    if filename_maker is None:
        filename_maker = make_backup_filename

    filename = filename_maker()
    destination = os.path.join(backup_dir, filename)

    database_handler = DatabaseHandler(database_settings)
    Encryptor().encrypt(database_handler.dump(), recipients, destination, gpg_home=gpg_home)
    return destination

def restore(database_settings, restore_from, gpg_home=None):
    """Restore to the database from the specified restoration point"""
    location = sanitise_path(restore_from)

    if not os.path.exists(location):
        raise BadBackupFile("The backup file at '{0}' doesn't exist".format(location))

    database_handler = DatabaseHandler(database_settings)
    if not database_handler.is_empty():
        raise NonEmptyDatabase("Sorry, won't restore to a database that isn't empty")

    database_handler.restore(Encryptor().decrypt(location, gpg_home=gpg_home))

def sanitise_path(path):
    """Remove file:// scheme from a path if it has one"""
    info = urlparse.urlparse(path)
    if info.scheme == "file":
        parts = [info.netloc]
        if info.path:
            parts.append(info.path)
        return ''.join(parts)
    return path

