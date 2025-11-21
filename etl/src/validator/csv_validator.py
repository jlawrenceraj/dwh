
import csv
from src.config.schema_config import SCHEMA, UNIQUE_FIELDS

def validate_row(row, schema):
    errors = []
    validated = {}
    for col, rules in schema.items():
        col_type = rules['type']
        required = rules['required']
        max_length = rules.get('max_length')
        value = row.get(col, '').strip()
        if required and not value:
            errors.append(f"Missing required field: {col}")
            continue
        if value:
            # Length validation
            if max_length and isinstance(value, str) and len(value) > max_length:
                errors.append(f"Field {col} exceeds max length {max_length}")
            # Type validation
            try:
                validated[col] = col_type(value)
            except Exception:
                errors.append(f"Invalid type for {col}: expected {col_type.__name__}")
        else:
            validated[col] = None
    return validated, errors


def validate_csv(file_path, schema=SCHEMA, unique_fields=UNIQUE_FIELDS):
    valid_rows = []
    error_rows = []
    seen_uniques = set()
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for i, row in enumerate(reader, 2):  # start at 2 for header
            validated, errors = validate_row(row, schema)
            # Duplicate check
            if not errors and unique_fields:
                unique_key = tuple(validated.get(f) for f in unique_fields)
                if unique_key in seen_uniques:
                    errors.append(f"Duplicate row on fields {unique_fields}: {unique_key}")
                else:
                    seen_uniques.add(unique_key)
            if errors:
                error_rows.append((i, errors))
            else:
                valid_rows.append(validated)
    return valid_rows, error_rows
