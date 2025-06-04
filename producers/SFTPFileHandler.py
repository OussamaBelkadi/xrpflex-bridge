# import paramiko
# import time
# from confluent_kafka import Producer
# import os
# from dotenv import load_dotenv
#
# def main():
#     try:
#         load_dotenv()
#
#         SFTP_HOST = os.getenv('SFTP_HOST')
#         SFTP_USERNAME = os.getenv('SFTP_USER')
#         SFTP_PASSWORD = os.getenv('SFTP_PASS')
#         SFTP_DIR = os.getenv('SFTP_DIR')
#         KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"  # Use Docker service name
#
#         KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "default_topic")
#
#         ssh = paramiko.SSHClient()
#         ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#         ssh.connect(SFTP_HOST, username=SFTP_USERNAME, password=SFTP_PASSWORD)
#
#         sftp = ssh.open_sftp()
#
#         producer = Producer({
#             'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
#             'client.id': 'sftp_producer'
#         })
#
#         known_files = {}
#
#         while True:
#             try:
#                 files = sftp.listdir(SFTP_DIR)
#                 for file in files:
#                     file_path = f"{SFTP_DIR}/{file}"
#                     file_stat = sftp.stat(file_path)
#
#                     if file not in known_files:
#                         # New file detected
#                         known_files[file] = file_stat.st_mtime
#                         event = f"New file uploaded: {file_path}"
#                         producer.produce(KAFKA_TOPIC, value=event.encode('utf-8'))
#                         producer.flush()
#                         print(f"Produced event for new file: {file_path}")
#                     elif file_stat.st_mtime > known_files[file]:
#                         # File updated
#                         known_files[file] = file_stat.st_mtime
#                         event = f"File updated: {file_path}"
#                         producer.produce(KAFKA_TOPIC, value=event.encode('utf-8'))
#                         producer.flush()
#                         print(f"Produced event for updated file: {file_path}")
#
#             except Exception as e:
#                 print(f"Error: {e}")
#
#             time.sleep(60)  # Poll every 1 minute
#
#     except Exception as e:
#         print(f"Error: {e}")
#
# if __name__ == '__main__':
#     main()
import os
import socket
from dotenv import load_dotenv
from confluent_kafka import Producer

# Load environment variables
load_dotenv()

def is_running_in_docker():
    """Check if we're running inside a Docker container"""
    try:
        with open('/proc/1/cgroup', 'rt') as f:
            return 'docker' in f.read()
    except FileNotFoundError:
        return False

def get_kafka_config():
    """Determine Kafka configuration based on environment"""
    # Check both the environment variable and actual Docker status
    in_docker = os.getenv('IN_DOCKER', 'false').lower() == 'true' or is_running_in_docker()

    if in_docker:
        return {
            'bootstrap.servers': 'kafka:9092',
            'client.id': 'sftp-producer-docker'
        }
    else:
        return {
            'bootstrap.servers': 'localhost:9092',
            'client.id': 'sftp-producer-local'
        }

def validate_config():
    """Validate all required environment variables"""
    required_vars = {
        'KAFKA_TOPIC': os.getenv('KAFKA_TOPIC'),
        'SFTP_HOST': os.getenv('SFTP_HOST'),
        'SFTP_USER': os.getenv('SFTP_USER'),
        'SFTP_PASSWORD': os.getenv('SFTP_PASSWORD')
    }

    missing_vars = [var for var, val in required_vars.items() if not val]
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

def test_kafka_connection(producer):
    """Test Kafka connection with more detailed error handling"""
    try:
        metadata = producer.list_topics(timeout=10)
        print(f"Connected to Kafka. Available topics: {list(metadata.topics.keys())}")
        return True
    except Exception as e:
        print(f"Failed to connect to Kafka: {str(e)}")
        return False

def main():
    try:
        # Validate configuration
        validate_config()

        # Get Kafka configuration
        kafka_config = get_kafka_config()
        print(f"Using Kafka configuration: {kafka_config}")

        # Create producer with additional configuration
        producer = Producer({
            **kafka_config,
            'request.timeout.ms': 30000,
            'metadata.max.age.ms': 30000,
            'socket.keepalive.enable': True
        })

        # Test connection
        if not test_kafka_connection(producer):
            print("Failed to establish Kafka connection. Check if Kafka is running and accessible.")
            return

        # Your SFTP processing logic here
        topic = os.getenv('KAFKA_TOPIC')
        producer.produce(topic, value="Test message")
        producer.flush()
        print("Message sent successfully!")

    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
