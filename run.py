#!/usr/bin/env python
"""
Grammar Playground - Main Entry Point
Run this file to start the Flask web application
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import app

if __name__ == '__main__':
    print("=" * 50)
    print("  Grammar Playground - LL(1) Grammar Analyzer")
    print("=" * 50)
    print("\nStarting server...")
    print("Open http://localhost:5000 in your browser\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
