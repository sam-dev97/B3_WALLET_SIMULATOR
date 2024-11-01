from db_backup.processes import stdout_chunks, check_and_start_process, feed_process
from db_backup.errors import NoDBDriver, NoDatabase

from contextlib import contextmanager
import tempfile
import logging
import os

log = logging.getLogger("db_backup")

class DatabaseInfo(object):
    ATTRS = ("engine", "name", "user", "password", "port", "host")

    def __init__(self, engine, name, user=None, password=None, port=None, host=None):
        self.name = name
        self.user = user or ""
        self.port = port or ""
        self.host = host or ""
        self.engine = engine
        self.password = password or ""

    def as_dict(self):
        """Return database info attributes as a dictionary"""
        return dict((key, getattr(self, key, None)) for key in DatabaseInfo.ATTRS)

    @classmethod
    def from_dict(self, options):
        """Return us an instance of DatabaseInfo from a dictionary"""
        lowered = dict((key.lower(), val) for key, val in options.items())
        have = dict((key, lowered[key]) for key in DatabaseInfo.ATTRS if key in lowered)
        return DatabaseInfo(**have)

class DatabaseDriver(object):
    """
    Base class for the database drivers
    These are used by DatabaseHandler so it doesn't care what engine is being used

    Password_option if specified is a 4 item tuple of (env, option, file_contents, stdin)
    Where env and option are (flag, val) pairs where the val is formatted with values from the database info.
    Also provided is a PASSWORD_FILE value which holds a temporary file with the file_contents string
    file_contents is also formatted with database values.
    Stdin if specified (also formatted with database values) is fed into the stdin of the process
    """

    aliases = ()
    password_option = None

    dump_template = ("", "")
    restore_template = ("", "")
    is_empty_template = ("", "")

    def __init__(self, database_info):
        self.database_info = database_info

    @contextmanager
    def a_temp_file(self, content):
        """Yield a temporary file and ensure it gets deleted"""
        filename = None
        try:
            if content:
                filename = tempfile.NamedTemporaryFile(delete=False).name
                with open(filename, "w") as fle:
                    fle.write(content)

            yield filename
        finally:
            if filename and os.path.exists(filename):
                os.remove(filename)

    @contextmanager
    def fill_out(self, template):
        """
        Fill out a template with the database_info
        Assume the template is [<command>, <options>]

        Where command is a string
        and options is [(<flag>, <val>), ...]

        If val formatted with the database_info is empty then that flag is ignored.
        """
        opts = []
        stdin = None
        environment = {}
        file_contents = None

        values = self.database_info.as_dict()
        command, argv = template

        if isinstance(argv, basestring):
            argv = [("", argv)]

        if self.database_info.password and self.password_option:
            env, option, file_contents, stdin = self.password_option
            if env:
                environment.update(env)

            if option:
                argv.insert(0, option)

        if file_contents:
            file_contents = file_contents.format(**values)

        if stdin:
            stdin = stdin.format(**values)

        with self.a_temp_file(file_contents) as password_file:
            values["PASSWORD_FILE"] = password_file

            for flag, val in argv:
                filled = val.format(**values)
                if filled:
                    opts.append("{0} {1}".format(flag, filled))

            for name, val in environment.items():
                filled = val.format(**values)
                if filled:
                    environment[name] = filled

            yield (command, " ".join(opts), environment, stdin)

    @contextmanager
    def dump_command(self):
        """Return us the command for dumping as (program, options)"""
        with self.fill_out(self.dump_template) as info:
            yield info

    @contextmanager
    def restore_command(self):
        """
        Return us the command for restoring from a backup as (program, options)
        This command should accept the output of the dump_command as input
        (The encrypted output of the dump_command output is decrypted when the restore command is run)
        """
        with self.fill_out(self.restore_template) as info:
            yield info

    def is_empty(self):
        """See that there are no tables under this database"""
        result = self.run_template(self.is_empty_template, "Find number of tables")
        log.info("The database has %s tables", result)
        return result == "0"

    def run_template(self, template, desc):
        """Run a template and return it's stdout"""
        with self.fill_out(template) as (command, options, env, stdin):
            return '\n'.join(stdout_chunks(command, options, desc, env=env, stdin=stdin)).strip()

class PsqlDriver(DatabaseDriver):
    aliases = ('psql', 'django.db.backends.postgresql_psycopg2', )
    dump_template = ('pg_dump', [("-U", "{user}"), ("--host", "{host}"), ("--port", "{port}"), ("", "{name}")])
    restore_template = ('psql', [("-U", "{user}"), ("--host", "{host}"), ("--port", "{port}"), ("-d", "{name}")])
    is_empty_template = ('psql', [
          ("-U", "{user}"), ("--host", "{host}"), ("--port", "{port}"), ("", "{name}")
        , ("", "-c \"select count(*) from information_schema.tables where table_schema = 'public'\" -t -A")
        ])
    password_option = ({"PGPASSFILE": "{PASSWORD_FILE}"}, None, "localhost:*:*:{user}:{password}", None)

class MysqlDriver(DatabaseDriver):
    aliases = ('mysql', 'django.db.backends.mysql', )
    dump_template = ('mysqldump', [("--user", "{user}"), ("--host", "{host}"), ("--port", "{port}"), ("", "{name}")])
    restore_template = ('mysql', [("--user", "{user}"), ("--host", "{host}"), ("--port", "{port}"), ("-D", "{name}")])
    is_empty_template = ('mysql', [
          ("--user", "{user}"), ("--host", "{host}"), ("--port", "{port}"), ("-D", "{name}")
        , ("", "-e \"select count(*) from information_schema.tables where table_schema = '{name}'\" --batch -s")
        ])
    password_option = (None, ("", "--defaults-extra-file={PASSWORD_FILE}"), "[client]\nuser={user}\npassword={password}", None)

class SqliteDriver(DatabaseDriver):
    aliases = ('sqlite3', 'django.db.backends.sqlite3', )
    dump_template = ('sqlite3', "{name} .dump")
    restore_template = ('sqlite3', "{name}")
    is_empty_template = ('sqlite3', "{name} \"select count(*) from sqlite_master where type='table'\"")

    def is_empty(self):
        """Complain if the database doesn't exist to be consistent with other drivers"""
        if not os.path.exists(self.database_info.name):
            raise NoDatabase("There was no sqlite database at {0}".format(self.database_info.name))
        return super(SqliteDriver, self).is_empty()

class DatabaseHandler(object):
    def __init__(self, database_info, database_driver=None):
        self.drivers = {}
        self.database_info = database_info
        self.given_database_driver = database_driver

        if isinstance(self.database_info, dict):
            self.database_info = DatabaseInfo.from_dict(self.database_info)

    @property
    def db_driver(self):
        if not hasattr(self, '_db_driver'):
            if self.given_database_driver is None:
                self._db_driver = self.driver_for(self.database_info)
            else:
                self._db_driver = self.given_database_driver
        return self._db_driver

    def dump(self):
        """Dump the contents of the database and yield a chunk at a time without hitting the disk"""
        with self.db_driver.dump_command() as (command, options, env, stdin):
            for chunk in stdout_chunks(command, options, "Dump command", env=env, stdin=stdin):
                yield chunk

    def restore(self, food):
        """Restore from the provided chunks"""
        with self.db_driver.restore_command() as (command, options, env, stdin):
            restorer = check_and_start_process(command, options, "Restore command", env=env, capture_stdin=True, stdin=stdin)
            feed_process(restorer, "Restoring database", food)

    def is_empty(self):
        """Work out if the database is empty"""
        return self.db_driver.is_empty()

    def driver_for(self, database_info):
        """
        Find us a DBDriver object for this database.
        If we can't find it, load the default drivers
        If we still can't find it, raise a NoDBDriver

        If we can find it, instantiate it with the database_info object
        """
        engine = database_info.engine
        if engine not in self.drivers:
            self.load_default_drivers()

        if engine not in self.drivers:
            raise NoDBDriver("Couldn't find driver for engine {0}".format(engine))

        return self.drivers[engine](database_info)

    def add_db_driver(self, driver_kls):
        """Register a database driver"""
        for alias in driver_kls.aliases:
            if alias not in self.drivers:
                self.drivers[alias] = driver_kls

    def load_default_drivers(self):
        """Add the default database drivers we know about"""
        for driver in (PsqlDriver, MysqlDriver, SqliteDriver):
            self.add_db_driver(driver)

