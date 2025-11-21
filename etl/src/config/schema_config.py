
# Load schema config from YAML
import os
import yaml

def load_config(config_path=None):
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), 'schema_config.yml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    # Convert type strings to actual Python types
    type_map = {'int': int, 'str': str, 'float': float}
    for col, rules in config['schema'].items():
        rules['type'] = type_map.get(rules['type'], str)
    return config

_CONFIG = load_config()
SCHEMA = _CONFIG['schema']
UNIQUE_FIELDS = _CONFIG['unique_fields']
TABLE_NAME = _CONFIG['table_name']
DB_CONFIG = _CONFIG['db_config']
