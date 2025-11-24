

import os
import sys
import csv
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.config.schema_config import load_config



class ETLProcess:
    def __init__(self, csv_file, config):
        self.csv_file = csv_file
        self.config = config
        self.db_config = config['db_config']
        self.valid_rows = []
        self.error_rows = []

    def validate(self):
        from src.validator.csv_validator import validate_csv
        self.valid_rows, self.error_rows = validate_csv(
            self.csv_file,
            schema=self.config['schema'],
            unique_fields=self.config['unique_fields']
        )

    def write_errors(self):
        if not self.error_rows:
            return
        error_file = self.csv_file.replace('.csv', '_errors.csv')
        with open(self.csv_file, newline='', encoding='utf-8') as infile, \
             open(error_file, 'w', newline='', encoding='utf-8') as errfile:
            reader = list(csv.DictReader(infile))
            fieldnames = reader[0].keys() if reader else []
            writer = csv.DictWriter(errfile, fieldnames=fieldnames)
            writer.writeheader()
            for row_num, errors in self.error_rows:
                writer.writerow(reader[row_num-2])
        print(f'Invalid rows written to {error_file}')
        # Remove invalid rows from the original file
        valid_indices = set(range(len(reader))) - set([row_num-2 for row_num, _ in self.error_rows])
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            for idx in valid_indices:
                writer.writerow(reader[idx])

        # Send error file by email if configured
        email_cfg = self.config.get('email')
        if email_cfg and email_cfg.get('enabled'):
            try:
                from src.utils.email_utils import send_email
                smtp_cfg = email_cfg.get('smtp', {})
                from_addr = email_cfg.get('from')
                to_addrs = email_cfg.get('to') or []
                subject = email_cfg.get('subject') or f"ETL error report: {os.path.basename(error_file)}"
                body = email_cfg.get('body') or f"Attached are the invalid rows extracted from {os.path.basename(self.csv_file)}."
                send_email(smtp_cfg, from_addr, to_addrs, subject, body, attachments=[error_file])
                print('Error file emailed to:', to_addrs)
            except Exception as e:
                print('Failed to send error email:', e)

    def load(self):
        from src.loader.postgres_loader import load_to_postgres
        table = self.config.get('table_name') or self.config.get('table')
        if self.valid_rows:
            load_to_postgres(self.valid_rows, self.db_config, table)
            print('Data loaded to PostgreSQL.')
        else:
            print('No valid rows to load.')

    def run(self):
        self.validate()
        if self.error_rows:
            print('Validation errors:')
            self.write_errors()
        print(f'Valid rows: {len(self.valid_rows)}')
        self.load()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='ETL CSV to PostgreSQL')
    parser.add_argument('--csv', dest='csv_file', required=False, help='Path to CSV file')
    parser.add_argument('--config', dest='config_file', required=False, help='Path to YAML config file')
    args = parser.parse_args()

    # Allow config file from env var or CLI
    config_path = args.config_file or os.environ.get('ETL_CONFIG')
    if config_path:
        config = load_config(config_path)
    else:
        config = load_config()

    # Allow CSV file from CLI or default
    if args.csv_file:
        csv_file = args.csv_file
    else:
        csv_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'enterprise-survey-2024.csv')
    if not os.path.isfile(csv_file):
        print(f'CSV file not found: {csv_file}')
        sys.exit(1)
    etl = ETLProcess(csv_file, config)
    etl.run()

if __name__ == '__main__':
    main()
