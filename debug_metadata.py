#!/usr/bin/env python3
"""
Debug script to analyze the metadata structure in PBIXRay.
"""

import os
import sys
import json
from pbixray import PBIXRay


def main():
    """
    Load the sample PBIX file and print metadata details
    """
    sample_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo", "AdventureWorks Sales.pbix")

    if not os.path.exists(sample_file):
        print(f"Error: Sample file not found at {sample_file}")
        return

    print(f"Loading PBIX file: {sample_file}")
    model = PBIXRay(sample_file)

    print("\nMetadata type:", type(model.metadata))

    try:
        # Try pandas to_json
        metadata_json = model.metadata.to_json(orient="records")
        print("\nSuccessfully converted to JSON using pandas to_json")
        print(f"JSON snippet: {metadata_json[:200]}...")
    except Exception as e:
        print(f"\nError converting with pandas to_json: {e}")

    try:
        # Try python's json module
        metadata_dict = model.metadata.to_dict()
        print("\nSuccessfully converted to dict using pandas to_dict")
        json_str = json.dumps(metadata_dict)
        print(f"JSON snippet: {json_str[:200]}...")
    except Exception as e:
        print(f"\nError converting with json.dumps: {e}")

    # Handle as pandas dataframe
    print("\nDataFrame columns:", model.metadata.columns.tolist())
    print("DataFrame shape:", model.metadata.shape)
    print("DataFrame first row:", model.metadata.iloc[0].tolist())


if __name__ == "__main__":
    main()
