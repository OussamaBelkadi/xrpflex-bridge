import paramiko
import os
from dotenv import load_dotenv

SFTP_HOST= os.getenv('SFTP_HOST')
SFTP_USER= os.getenv('SFTP_USER')
SFTP_PASS= os.getenv('SFTP_PASS')

def main():
    load_dotenv()
    ssh = paramiko.SSHClient();
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy());
    ssh.connect(SFTP_HOST, username=SFTP_USER, password=SFTP_PASS);

    if ssh.get_transport().is_active():
        print("Connected to SFTP server")
    else:
        print("Failed to connect to SFTP server")
        return

    sftp = ssh.open_sftp();
    files = sftp.listdir();

    for file in files:
        print(f"File: {file}");
        try:
            with sftp.open(file, 'r') as f:
                file_content = f.read().decode('utf-8');
                print(file_content);
        except Exception as e:
            print(f"Error reafing file: {e}");

    sftp.close();
    ssh.close();

if __name__ == '__main__':
    main()
