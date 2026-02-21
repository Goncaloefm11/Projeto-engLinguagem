"""
Grammar Playground - Web Module
Flask application for grammar analysis
"""

from .app import app

def main():
    """Entry point for the application"""
    app.run(debug=True, host='0.0.0.0', port=5000)

__all__ = ['app', 'main']
