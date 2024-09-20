import pandas as pd
import re
import PyPDF2
from docx import Document

# Function to read text file
def read_text_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

# Function to read PDF file
def read_pdf_file(file_path):
    text = ""
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfFileReader(file)
        for page_num in range(reader.numPages):
            text += reader.getPage(page_num).extract_text()
    return text

# Function to read Word file
def read_word_file(file_path):
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

# Function to parse the provided text data
def parse_network_requirements(text):
    policies = []
    vlans = []
    address_objects = []
    service_objects = []
    web_filters = []
    meraki_switches = []
    meraki_stack_routes = []
    current_section = None

    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        print(f"Processing line: {line}")  # Debugging statement
        if "Firewall rule/proxy" in line:
            current_section = 'policy'
            parts = line.split()
            if len(parts) >= 7:
                firewall, policy_id, name, from_zone, to_zone, source, destination = parts[:7]
                schedule = "always"
                service = "HTTP"
                action = "accept"
                nat = "enable"
                sec_profiles = "default"
                log = "all"
                notes = " ".join(parts[7:]) if len(parts) > 7 else ""
                policies.append((firewall, policy_id, name, from_zone, to_zone, source, destination, schedule, service, action, nat, sec_profiles, log, notes))
        elif "Necessary Ports" in line:
            current_section = 'ports'
        elif current_section == 'ports' and re.search(r'\d+ - \w+', line):
            parts = re.split(r' - ', line, maxsplit=2)
            if len(parts) == 3:
                port_number, port_name, description = parts
                service = port_name.strip()
                policies[-1] = policies[-1][:8] + (service,) + policies[-1][9:]
                firewall = "ExampleFirewall"
                name = port_name.strip()
                details = f"TCP/{port_number.strip()}"
                service_group = "ExampleServiceGroup"
                service_objects.append((firewall, name, details, service_group))
        elif "VLAN" in line and re.search(r'VLAN \d+:', line):
            current_section = 'vlan'
            parts = re.split(r':', line, maxsplit=1)
            if len(parts) == 2:
                vlan_id, subnet = parts[0].strip().split()[1], parts[1].strip()
                firewall = "ExampleFirewall"
                name = f"VLAN_{vlan_id}"
                interface = "port1"
                dhcp = "enable"
                vlans.append((firewall, name, vlan_id, subnet, interface, dhcp))
        elif "Fixed IPs" in line:
            current_section = 'address_objects'
        elif current_section == 'address_objects' and re.search(r'\d+\.\d+\.\d+\.\d+', line):
            parts = line.split()
            if len(parts) >= 2:
                details = parts[0]
                name = f"Object_{details.replace('.', '_')}"
                firewall = "ExampleFirewall"
                address_group = "ExampleGroup"
                address_objects.append((firewall, name, details, address_group))
        elif "URLs Allowed" in line:
            current_section = 'web_filters'
        elif current_section == 'web_filters' and re.search(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', line):
            url = line.strip()
            firewall = "ExampleFirewall"
            webfilter_name = "ExampleWebFilter"
            filter_type = "URL"
            action = "allow"
            status = "enable"
            web_filters.append((firewall, url, webfilter_name, filter_type, action, status))
        elif "Meraki Switch" in line:
            current_section = 'meraki_switch'
        elif current_section == 'meraki_switch' and re.search(r'^\w+', line):
            parts = line.split()
            if len(parts) >= 3:
                template, port, vlan = parts[:3]
                notes = " ".join(parts[3:]) if len(parts) > 3 else ""
                meraki_switches.append((template, port, vlan, notes))
        elif "Meraki Stack Routes" in line:
            current_section = 'meraki_stack_routes'
        elif current_section == 'meraki_stack_routes' and re.search(r'^\w+', line):
            parts = line.split()
            if len(parts) >= 3:
                template, port, vlan = parts[:3]
                notes = " ".join(parts[3:]) if len(parts) > 3 else ""
                meraki_stack_routes.append((template, port, vlan, notes))

    # Debugging statements
    print("Policies:", policies)
    print("VLANs:", vlans)
    print("Address Objects:", address_objects)
    print("Service Objects:", service_objects)
    print("Web Filters:", web_filters)
    print("Meraki Switches:", meraki_switches)
    print("Meraki Stack Routes:", meraki_stack_routes)

    return policies, vlans, address_objects, service_objects, web_filters, meraki_switches, meraki_stack_routes

# Function to write data to Excel
def write_to_excel(details, output_file):
    policies, vlans, address_objects, service_objects, web_filters, meraki_switches, meraki_stack_routes = details

    # Create DataFrames for each worksheet
    df_policies = pd.DataFrame(policies, columns=['Firewall', 'Policy ID', 'Name', 'From', 'To', 'Source', 'Destination', 'Schedule', 'Service', 'Action', 'NAT', 'Security Profiles', 'Log', 'Notes'])
    df_vlans = pd.DataFrame(vlans, columns=['Firewall', 'Name', 'Vlan ID', 'Subnet', 'Interface', 'DHCP'])
    df_address_objects = pd.DataFrame(address_objects, columns=['Firewall', 'Name', 'Details', 'Address Group'])
    df_service_objects = pd.DataFrame(service_objects, columns=['Firewall', 'Name', 'Details', 'Service Group'])
    df_web_filters = pd.DataFrame(web_filters, columns=['Firewall', 'Requested URLs', 'WebFilter Name', 'Type', 'Action', 'Status'])
    df_meraki_switches = pd.DataFrame(meraki_switches, columns=['Template', 'Port', 'Vlan', 'Notes'])
    df_meraki_stack_routes = pd.DataFrame(meraki_stack_routes, columns=['Template', 'Port', 'Vlan', 'Notes'])

    # Write DataFrames to Excel
    with pd.ExcelWriter(output_file) as writer:
        df_policies.to_excel(writer, sheet_name='Policy Changes', index=False)
        df_vlans.to_excel(writer, sheet_name='VLan', index=False)
        df_address_objects.to_excel(writer, sheet_name='Address Objects', index=False)
        df_service_objects.to_excel(writer, sheet_name='Service Objects', index=False)
        df_web_filters.to_excel(writer, sheet_name='WebFilter', index=False)
        df_meraki_switches.to_excel(writer, sheet_name='Meraki Switch', index=False)
        df_meraki_stack_routes.to_excel(writer, sheet_name='Meraki Stack Routes', index=False)

# Main function to load the document and process it
def main():
    file_path = input("Enter the file path: ")
    file_type = input("Enter the file type (text, pdf, word): ")
    output_file = 'network_requirements.xlsx'

    if file_type == 'text':
        text_data = read_text_file(file_path)
    elif file_type == 'pdf':
        text_data = read_pdf_file(file_path)
    elif file_type == 'word':
        text_data = read_word_file(file_path)
    else:
        raise ValueError("Unsupported file type")

    parsed_details = parse_network_requirements(text_data)
    write_to_excel(parsed_details, output_file)
    print(f"Data has been written to {output_file}")

if __name__ == "__main__":
    main()
