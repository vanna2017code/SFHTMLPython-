import os
import paramiko
from contextlib import contextmanager

class SFTPConfig:
    def __init__(self, host, port=22, username=None, password=None, key_filename=None, remote_dir="/"):
        self.host = host
        self.port = int(port)
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.remote_dir = remote_dir

@contextmanager
def sftp_connection(config: SFTPConfig):
    transport = None
    sftp = None
    try:
        transport = paramiko.Transport((config.host, config.port))
        if config.key_filename:
            private_key = paramiko.RSAKey.from_private_key_file(config.key_filename)
            transport.connect(username=config.username, pkey=private_key)
        else:
            transport.connect(username=config.username, password=config.password)

        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.chdir(config.remote_dir)
        yield sftp
    finally:
        if sftp:
            sftp.close()
        if transport:
            transport.close()

def list_files(config: SFTPConfig):
    with sftp_connection(config) as sftp:
        return sftp.listdir(config.remote_dir)

def upload_file(config: SFTPConfig, local_path: str, remote_filename: str = None):
    if not remote_filename:
        remote_filename = os.path.basename(local_path)
    remote_path = os.path.join(config.remote_dir, remote_filename).replace("\\", "/")
    with sftp_connection(config) as sftp:
        sftp.put(local_path, remote_path)
    return remote_filename

def download_file(config: SFTPConfig, remote_filename: str, local_path: str):
    remote_path = os.path.join(config.remote_dir, remote_filename).replace("\\", "/")
    with sftp_connection(config) as sftp:
        sftp.get(remote_path, local_path)
    return local_path
