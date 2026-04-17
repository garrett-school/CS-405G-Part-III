import json
import sys
from pathlib import Path

import mysql.connector
from mysql.connector import Error

CONFIG_PATH = Path(__file__).resolve().parents[1] / 'config' / 'config.json'


def load_config():
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f'Configuration file not found: {CONFIG_PATH}')
        sys.exit(1)
    except json.JSONDecodeError as err:
        print(f'Configuration file is invalid: {err}')
        sys.exit(1)


def connect_db():
    try:
        config = load_config()
        return mysql.connector.connect(**config)
    except Error as err:
        print('Failed to connect to database:', err)
        sys.exit(1)
