"""
Pytest configuration for the pbixray-mcp tests.
"""

import os
import pytest
import pathlib


def pytest_addoption(parser):
    """Add command-line options for testing"""
    parser.addoption("--pbix-file", action="store", default=None, help="Path to a custom PBIX file to use for testing")


@pytest.fixture
def pbix_file_path(request):
    """
    Returns the path to the PBIX file to use for testing.

    If --pbix-file command-line option is provided and exists, it will be used.
    Otherwise, defaults to the demo file included in the repo.
    """
    # Check if a custom path was provided
    custom_path = request.config.getoption("--pbix-file")

    if custom_path and os.path.exists(custom_path):
        print(f"Using custom PBIX file: {custom_path}")
        return pathlib.Path(custom_path)

    # Default to the demo file in the repo
    repo_root = pathlib.Path(__file__).parent.parent
    demo_file_path = repo_root / "demo" / "AdventureWorks Sales.pbix"

    print(f"Using default PBIX file: {demo_file_path}")
    return demo_file_path
