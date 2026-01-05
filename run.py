#!/usr/bin/env python3
"""
Run script for Trading Journal
"""

from app import app

if __name__ == '__main__':
    print("Starting Trading Journal...")
    print("Open http://127.0.0.1:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)
