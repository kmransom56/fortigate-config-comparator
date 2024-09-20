import pandas as pd
import re

# Define the file path
file_path = 'data.txt'
temp_file_path = 'cleaned_data.txt'

# Preprocess the file to remove extra spaces
with open(file_path, 'r') as infile, open(temp_file_path, 'w') as outfile:
    for line in infile:
        # Replace multiple spaces with a single space
        cleaned_line = re.sub(r'\s+', ' ', line).strip()
        # Write the cleaned line to the temporary file
        outfile.write(cleaned_line + '\n')

# Read the cleaned data using whitespace as the delimiter
try:
    df = pd.read_csv(temp_file_path, sep=' ', skiprows=2, header=None)
except pd.errors.ParserError as e:
    print("ParserError:", e)
    df = pd.DataFrame()  # Create an empty DataFrame to avoid further errors

# Check if the DataFrame is empty
if df.empty:
    print("The DataFrame is empty. Please check the input file for inconsistencies.")
else:
    # Define the correct column names
    column_names = ["seq-num", "q_origin_key", "status", "dst", "src", "gateway", "distance", "weight", "priority", "device"]

    # Assign the correct column names to the DataFrame
    df.columns = column_names + [f"extra_col_{i}" for i in range(len(df.columns) - len(column_names))]

    # Drop any extra columns that are not needed
    df = df[column_names]

    # Display the DataFrame to verify the data
    print("Initial DataFrame:")
    print(df.head())

    # Convert relevant columns to numeric, forcing errors to NaN
    df['seq-num'] = pd.to_numeric(df['seq-num'], errors='coerce')
    df['distance'] = pd.to_numeric(df['distance'], errors='coerce')
    df['weight'] = pd.to_numeric(df['weight'], errors='coerce')
    df['priority'] = pd.to_numeric(df['priority'], errors='coerce')

    # Drop rows with NaN values in critical columns (if any)
    df = df.dropna(subset=['seq-num', 'distance', 'weight', 'priority'])

    # Display the DataFrame after dropping NaN values
    print("DataFrame after dropping NaN values:")
    print(df)

    # Example of consolidating data into a single row format
    consolidated_df = df.groupby('device').agg({
        'seq-num': 'count',  # Example: count of seq-num per device
        'distance': 'mean',  # Example: average distance per device
    }).reset_index()

    # Display the consolidated DataFrame
    print("Consolidated DataFrame:")
    print(consolidated_df)