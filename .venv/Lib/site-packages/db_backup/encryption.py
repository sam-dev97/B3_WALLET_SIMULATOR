from db_backup.processes import feed_process, check_and_start_process, until, stdout_chunks, print_process
from db_backup.errors import GPGFailedToStart

class Encryptor(object):
    """Used to encrypt and decrypt with gpg"""

    def encrypt(self, input_iterator, recipients, destination, gpg_home=None):
        """Encrypt chunks from the provided iterator"""
        desc = "Encrypting something"
        options = [
            "--trust-model", "always"
          , "-r", " -r ".join(recipients)
          , "--output", destination
          , "-e"
          ]
        if gpg_home: options.extend(["--homedir", gpg_home])

        process = check_and_start_process("gpg", ' '.join(options), desc, capture_stdin=True)

        # See if it fails to start (i.e. bad recipients)
        for _ in until(timeout=0.5):
            print_process(process, desc)
            if process.poll() not in (None, 0):
                raise GPGFailedToStart("GPG didn't even start")

        feed_process(process, desc, input_iterator)

    def decrypt(self, location, gpg_home=None, password=None):
        """Decrypt provided location and yield chunks of decrypted data"""
        options = ["--trust-model", "always", "-d", "--no-tty"]
        if gpg_home: options.extend(["--homedir", gpg_home])
        if password: options.extend(["--passphrase-file", "/dev/stdin"])
        options.append(location)
        return stdout_chunks("gpg", ' '.join(options), "Decrypting something", interaction=password)
