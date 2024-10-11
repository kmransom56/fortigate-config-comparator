import pandas as pd
import textfsm
import sys
import argparse
import logging
import json
from datetime import datetime

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_arguments():
    parser = argparse.ArgumentParser(description="Process routing table data.")
    parser.add_argument('--data', default='data.txt', help='Path to the data file')
    parser.add_argument('--template', default='routing_table.template', help='Path to the TextFSM template file')
    parser.add_argument('--output', help='Path to save the output CSV file')
    return parser.parse_args()

def concatenate_routes(group):
    routes = []
    for _, row in group.iterrows():
        route = {
            'seq_num': row['SEQ_NUM'],
            'q_origin_key': row['Q_ORIGIN_KEY'],
            'status': row['STATUS'],
            'dst': row['DST'],
            'netmask': row['NETMASK'],
            'src': row['SRC'],
            'gateway1': row['GATEWAY1'],
            'gateway2': row['GATEWAY2'],
            'distance': row['DISTANCE'],
            'weight': row['WEIGHT'],
            'priority': row['PRIORITY']
        }
        routes.append(route)
    return json.dumps(routes)

def main():
    setup_logging()
    args = parse_arguments()

    # Read the raw data from the file
    try:
        with open(args.data, 'r') as f:
            raw_data = f.read()
        logging.info("Raw data loaded successfully")
    except IOError as e:
        logging.error(f"Error reading data file: {e}")
        sys.exit(1)

    # Load the TextFSM template
    try:
        with open(args.template, 'r') as template_file:
            fsm = textfsm.TextFSM(template_file)
        logging.info("Template loaded successfully")
    except IOError as e:
        logging.error(f"Error loading template: {e}")
        sys.exit(1)

    # Parse the raw data using the template
    try:
        parsed_data = fsm.ParseText(raw_data)
        logging.info("Data parsed successfully")
    except textfsm.TextFSMError as e:
        logging.error(f"Error parsing data: {e}")
        sys.exit(1)

    # Convert parsed data to DataFrame
    df = pd.DataFrame(parsed_data, columns=fsm.header)
    logging.info("DataFrame created")

    # Convert numeric columns to appropriate types
    numeric_columns = ['SEQ_NUM', 'Q_ORIGIN_KEY', 'DISTANCE', 'WEIGHT', 'PRIORITY']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Group by DEVICE and concatenate all routes
    result_df = df.groupby('DEVICE').apply(concatenate_routes).reset_index()
    result_df.columns = ['DEVICE', 'ROUTES']

    # Add a count of routes for each device
    result_df['ROUTE_COUNT'] = df.groupby('DEVICE').size().values

    print("\nResult DataFrame:")
    print(result_df)

    # Save output
    if args.output:
        output_file = args.output
    else:
        # Generate a default filename if not provided
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"routing_table_output_{timestamp}.csv"

    result_df.to_csv(output_file, index=False)
    logging.info(f"Output saved to {output_file}")

    logging.info("Processing completed successfully")

if __name__ == "__main__":
    main()