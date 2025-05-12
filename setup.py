#!/usr/bin/env python
"""
Setup script for the coffee shop data analysis system.
This script creates the necessary directory structure and installs required packages.
"""

import os
import subprocess
import sys

def create_directory_structure():
    """Create the necessary directory structure for the project."""
    print("Creating directory structure...")
    
    # Main data directories
    dirs = [
        "data/raw",
        "data/processed",
        "reports",
        "notebooks"
    ]
    
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    
    print("Directory structure created successfully.")

def install_dependencies():
    """Install the required packages from requirements.txt."""
    print("Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {str(e)}")
        return False
    
    return True

def setup():
    """Run the complete setup process."""
    print("Setting up the Coffee Shop Data Analysis System...")
    
    # Create directory structure
    create_directory_structure()
    
    # Install dependencies
    if install_dependencies():
        print("\nSetup completed successfully!")
        print("\nYou can now run the system using:")
        print("python src/main.py full")
        print("\nOr explore the demo notebook:")
        print("jupyter notebook notebooks/coffee_shop_analysis_demo.ipynb")
    else:
        print("\nSetup completed with errors.")

if __name__ == "__main__":
    setup()
