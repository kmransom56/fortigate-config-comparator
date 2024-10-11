import paramiko

def ssh_connect(host, username, password):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=username, password=password)
        return client
    except Exception as e:
        print(f"Failed to connect to {host}: {str(e)}")
        return None

def check_firewall_rules(ssh_client, device_ip, destination_ip):
    try:
        command = f"diagnose firewall proute list | grep {device_ip}"
        stdin, stdout, stderr = ssh_client.exec_command(command)
        rules_output = stdout.read().decode('utf-8')

        if destination_ip in rules_output:
            return f"Traffic from {device_ip} to {destination_ip} is being blocked by a firewall rule."
        else:
            return f"No blocking rules found for traffic from {device_ip} to {destination_ip}."
    except Exception as e:
        return f"Failed to execute the command: {str(e)}"

def main():
    # Firewall login details
    fortigate_ip = input("Enter FortiGate IP address: ")
    username = input("Enter SSH username: ")
    password = input("Enter SSH password: ")

    # Device details
    device_ip = input("Enter the device IP address: ")
    destination_ip = input("Enter the destination IP address: ")

    if not (fortigate_ip and username and password and device_ip and destination_ip):
        print("All inputs are required. Please try again.")
        return

    # Connect to FortiGate
    ssh_client = ssh_connect(fortigate_ip, username, password)
    if not ssh_client:
        print("Failed to connect to FortiGate.")
        return

    # Check firewall rules
    result = check_firewall_rules(ssh_client, device_ip, destination_ip)
    print(result)

    # Close SSH connection
    ssh_client.close()

if __name__ == "__main__":
    main()

