"""
This is the file you run to start the simulation.

Run: python main.py
"""

import sys


def check_dependencies():
    """
    Verify that all dependencies are installed.

    Returns:

    --------
    bool: True if everything is installed, False if something is missing
    """
    required = {
        'simpy': 'SimPy (discrete event simulation)',
        'pandas': 'Pandas (data management)',
        'numpy': 'NumPy (mathematical calculations)'
    }
    
    missing = []
    
    for package, description in required.items():
        try:
            __import__(package)
        except ImportError:
            missing.append(f"  - {package}: {description}")
    
    if missing:
        print("=" * 70)
        print("❌ ERROR: Necessary dependencies are missing")
        print("=" * 70)
        print("\nThe following packages could not be imported:")
        for item in missing:
            print(item)
        print("\n💡 Solution:")
        print("   Run the following command to install all dependencies:")
        print("   pip install -r requirements.txt")
        print("\n   or install manually:")
        print("   pip install simpy pandas numpy matplotlib")
        print("=" * 70)
        return False
    
    return True


def main():
    
    # Check dependencies first
    if not check_dependencies():
        sys.exit(1)
    
    # Import after verification 
    import config
    from simulation import GreenGridSimulation
    
    # Create simulation
    sim = GreenGridSimulation()
    
    # Execute
    sim.run()
    
    print("\n✨ Done! Check the simulation_results.csv file to see the data.")
    print("   You can open this file in Excel or use pandas to analyze it.")


if __name__ == "__main__":
    main()