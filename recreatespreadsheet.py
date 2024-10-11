import pandas as pd

# Recreating the structure of the original spreadsheet based on the extracted columns and the sheets

# Create empty dataframes with the correct structure
sheets = {
    "Policy Changes": pd.DataFrame(columns=[
        "Firewall", "Policy ID", "Name", "From", "To", "Source", "Destination", 
        "Schedule", "Service", "Action", "NAT", "Security Profiles", "Log", "Notes"
    ]),
    "Vlan": pd.DataFrame(columns=[
        "Firewall", "Name", "Vlan ID", "Subnet", "Interface", "DHCP"
    ]),
    "Address Objects": pd.DataFrame(columns=[
        "Firewall", "Name", "Details", "Address Group"
    ]),
    "Service Objects": pd.DataFrame(columns=[
        "Firewall", "Name", "Details", "Service Group"
    ]),
    "WebFilter": pd.DataFrame(columns=[
        "Firewall", "Requested URLs", "WebFilter Name", "Type", "Action", "Status"
    ]),
    "Meraki Switch": pd.DataFrame(columns=[
        "Template", "Port", "Vlan", "Notes"
    ]),
    "Static Routes": pd.DataFrame(columns=[
        "Firewall", "Destination", "Device", "Distance", "Gateway", "Priority", "Description"
    ])
}

# Save the recreated spreadsheet to a file
recreated_spreadsheet_path = "/mnt/data/Recreated_Change_Request_Template.xlsx"
with pd.ExcelWriter(recreated_spreadsheet_path) as writer:
    for sheet_name, df in sheets.items():
        df.to_excel(writer, sheet_name=sheet_name, index=False)

recreated_spreadsheet_path
import pandas as pd

# Recreating the structure of the original spreadsheet based on the extracted columns and the sheets

# Create empty dataframes with the correct structure
sheets = {
    "Policy Changes": pd.DataFrame(columns=[
        "Firewall", "Policy ID", "Name", "From", "To", "Source", "Destination", 
        "Schedule", "Service", "Action", "NAT", "Security Profiles", "Log", "Notes"
    ]),
    "Vlan": pd.DataFrame(columns=[
        "Firewall", "Name", "Vlan ID", "Subnet", "Interface", "DHCP"
    ]),
    "Address Objects": pd.DataFrame(columns=[
        "Firewall", "Name", "Details", "Address Group"
    ]),
    "Service Objects": pd.DataFrame(columns=[
        "Firewall", "Name", "Details", "Service Group"
    ]),
    "WebFilter": pd.DataFrame(columns=[
        "Firewall", "Requested URLs", "WebFilter Name", "Type", "Action", "Status"
    ]),
    "Meraki Switch": pd.DataFrame(columns=[
        "Template", "Port", "Vlan", "Notes"
    ]),
    "Static Routes": pd.DataFrame(columns=[
        "Firewall", "Destination", "Device", "Distance", "Gateway", "Priority", "Description"
    ])
}

# Save the recreated spreadsheet to a file
recreated_spreadsheet_path = "/mnt/data/Recreated_Change_Request_Template.xlsx"
with pd.ExcelWriter(recreated_spreadsheet_path) as writer:
    for sheet_name, df in sheets.items():
        df.to_excel(writer, sheet_name=sheet_name, index=False)

recreated_spreadsheet_path
