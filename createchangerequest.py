import pandas as pd
import openpyxl

# Load the Excel template again
template_path = "/mnt/data/Change_Request_Template.xlsx"
template_df = pd.read_excel(template_path, sheet_name=None)  # Load all sheets

# Extracted data from the image
extracted_data = {
    "Licensing": [
        {"Use": "On-Premises License Server", "Port": 7070, "Transport Protocol": "TCP", "Application Protocol": "HTTP",
         "Source": "Tosca Server, Tosca Commander, DEX Agent", "Destination": "Tosca Application Server", "Configurable": "Yes"},
        {"Use": "Cloud License Server", "Port": 443, "Transport Protocol": "TCP", "Application Protocol": "HTTPS",
         "Source": "Tosca Server, Tosca Commander, DEX Agent", "Destination": "Cloud License Server", "Configurable": "No"},
    ],
    "Tosca Server": [
        {"Use": "Tosca Server", "Port": 443, "Transport Protocol": "TCP", "Application Protocol": "HTTPS",
         "Source": "Tosca Server, Tosca Commander, DEX Agent", "Destination": "Tosca Server", "Configurable": "No"},
    ],
    "Database": [
        {"Use": "MSSQL Server/Azure SQL", "Port": 1433, "Transport Protocol": "TCP", "Application Protocol": "TCP",
         "Source": "Tosca Server, Tosca Commander", "Destination": "MSSQL", "Configurable": "Yes"},
        {"Use": "Oracle DB", "Port": 1521, "Transport Protocol": "TCP", "Application Protocol": "TCP",
         "Source": "Tosca Server, Tosca Commander", "Destination": "Oracle", "Configurable": "Yes"},
        {"Use": "IBM DB2", "Port": 50000, "Transport Protocol": "TCP", "Application Protocol": "TCP",
         "Source": "Tosca Server, Tosca Commander", "Destination": "IBM DB2", "Configurable": "Yes"},
    ]
}

# Adjusted mapping for the template

# Sample mapping logic based on assumed relevance
# Note: This logic is speculative due to lack of exact matching sheet names
mapping = {
    "Policy Changes": extracted_data["Licensing"] + extracted_data["Tosca Server"],
    "Vlan": extracted_data.get("VLANs", []),  # Assuming VLANs were part of the data
    "Service Objects": extracted_data["Database"]  # Database info could fit here
}

# Function to populate the template with the adjusted mapping
def populate_template_adjusted(template_df, mapping):
    for sheet_name, data in mapping.items():
        if sheet_name in template_df and data:
            df = pd.DataFrame(data)
            template_df[sheet_name] = df
    
    # Save the populated template
    output_path = "/mnt/data/Populated_Change_Request_Template_Adjusted.xlsx"
    with pd.ExcelWriter(output_path) as writer:
        for sheet_name, df in template_df.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    return output_path

# Populate the template with the adjusted data
populated_template_path_adjusted = populate_template_adjusted(template_df, mapping)

populated_template_path_adjusted
