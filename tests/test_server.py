#!/usr/bin/env python3
"""
Unit tests for the PBIXRay MCP server

Usage:
    pytest -xvs tests/test_server.py                         # Use the default demo PBIX file
    pytest -xvs tests/test_server.py --pbix-file=/path/to/custom.pbix  # Use a custom PBIX file
"""

import os
import pytest
import sys
import json
import asyncio
import pathlib
from unittest.mock import patch, MagicMock

# Add the src directory to the path so we can import the server module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# Mock the parse_args function before importing the module
with patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
    # Create a mock args object with the expected attributes
    mock_args = MagicMock()
    mock_args.disallow = []
    mock_args.max_rows = 100
    mock_args.page_size = 20
    mock_parse_args.return_value = mock_args

    # Now import the server module
    import pbixray_server


# Mock PBIXRay class to avoid needing actual PBIX files during tests
class MockPBIXRay:
    def __init__(self, file_path):
        self.file_path = file_path
        self.tables = ["Table1", "Table2"]

        # Create metadata as a DataFrame with Name and Value columns (matching real structure)
        import pandas as pd

        self.metadata = pd.DataFrame(
            {"Name": ["version", "creator", "timestamp"], "Value": ["1.0", "Test User", "2023-01-01"]}
        )

        self.size = 1024

        # Add additional properties for comprehensive testing
        self.dax_measures = pd.DataFrame(
            {
                "TableName": ["Table1", "Table1", "Table2"],
                "Name": ["Measure1", "Measure2", "Measure3"],
                "Expression": ["SUM(Column1)", "AVG(Column1)", "COUNT(Column2)"],
            }
        )

        self.dax_columns = pd.DataFrame(
            {
                "TableName": ["Table1", "Table2"],
                "ColumnName": ["CalcColumn1", "CalcColumn2"],
                "Expression": ["Column1 + 10", "UPPER(Column2)"],
            }
        )

        self.relationships = pd.DataFrame(
            {
                "FromTableName": ["Table1", "Table2"],
                "FromColumnName": ["ID", "FK"],
                "ToTableName": ["Table2", "Table1"],
                "ToColumnName": ["FK", "ID"],
                "IsActive": [True, False],
            }
        )

        self.power_query = pd.DataFrame(
            {"TableName": ["Table1", "Table2"], "Expression": ["let Source = #table(...", "let Source = #table(...)"]}
        )

        self.schema = pd.DataFrame(
            {
                "TableName": ["Table1", "Table1", "Table2"],
                "ColumnName": ["Column1", "Column2", "Column1"],
                "DataType": ["Integer", "String", "Integer"],
            }
        )

        self.statistics = pd.DataFrame(
            {
                "TableName": ["Table1", "Table2"],
                "ColumnName": ["Column1", "Column1"],
                "Cardinality": [3, 3],
                "SizeInBytes": [12, 12],
            }
        )

    def get_table(self, table_name):
        # Return a mock pandas DataFrame
        import pandas as pd

        return pd.DataFrame({"Column1": [1, 2, 3], "Column2": ["A", "B", "C"]})


# Helper function to run async tests
def run_async(coro):
    """Run an async function synchronously in tests"""
    return asyncio.run(coro)


# Tests for the server functions
@pytest.mark.asyncio
async def test_load_pbix_file(pbix_file_path):
    """Test the load_pbix_file function"""
    # Create a mock Context with async methods
    mock_context = MagicMock()
    mock_context.info = MagicMock(return_value=asyncio.Future())
    mock_context.info.return_value.set_result(None)
    mock_context.report_progress = MagicMock(return_value=asyncio.Future())
    mock_context.report_progress.return_value.set_result(None)

    if pbix_file_path.exists():
        # Test with the actual PBIX file
        print(f"Testing with PBIX file: {pbix_file_path}")
        result = await pbixray_server.load_pbix_file(str(pbix_file_path), mock_context)
        assert "Successfully loaded" in result

        # Test that the model was loaded correctly
        assert pbixray_server.current_model is not None
        assert pbixray_server.current_model_path == str(pbix_file_path)

        # Clean up
        pbixray_server.current_model = None
        pbixray_server.current_model_path = None
    else:
        # Fall back to the mock approach if file is not found
        print(f"PBIX file not found: {pbix_file_path}, using mock approach")
        with patch("os.path.getsize", return_value=1024):  # Small file to avoid thread pooling
            # Mock the PBIXRay class
            with patch("pbixray_server.PBIXRay", MockPBIXRay):
                with patch("os.path.exists", return_value=True):
                    result = await pbixray_server.load_pbix_file("/path/to/test.pbix", mock_context)
                    assert "Successfully loaded" in result


def test_get_tables(pbix_file_path):
    """Test the get_tables function"""
    # Create a mock Context
    mock_context = MagicMock()

    if pbix_file_path.exists() and pbixray_server.current_model is None:
        # Use actual PBIX file (load it synchronously for this test)
        try:
            from pbixray import PBIXRay

            pbixray_server.current_model = PBIXRay(str(pbix_file_path))
            using_real_file = True
            print(f"Using PBIX file for tables test: {pbix_file_path}")
        except Exception as e:
            print(f"Could not load PBIX file, using mock: {e}")
            pbixray_server.current_model = MockPBIXRay("/path/to/test.pbix")
            using_real_file = False
    else:
        # Use mock
        pbixray_server.current_model = MockPBIXRay("/path/to/test.pbix")
        using_real_file = False

    # Run the test
    result = pbixray_server.get_tables(mock_context)

    # Check appropriate assertions based on whether we're using a real file or mock
    if using_real_file:
        assert len(result) > 0, "Expected real tables from PBIX file"
        assert isinstance(result, str), "Expected JSON string response"
        # Parse JSON to make sure it's valid
        parsed = json.loads(result)
        assert isinstance(parsed, list), "Expected list of tables"
    else:
        assert "Table1" in result
        assert "Table2" in result

    # Clean up
    pbixray_server.current_model = None


def test_get_metadata(pbix_file_path):
    """Test the get_metadata function"""
    # Create a mock Context
    mock_context = MagicMock()

    if pbix_file_path.exists() and pbixray_server.current_model is None:
        # Use actual PBIX file
        try:
            from pbixray import PBIXRay

            pbixray_server.current_model = PBIXRay(str(pbix_file_path))
            using_real_file = True
        except Exception:
            pbixray_server.current_model = MockPBIXRay("/path/to/test.pbix")
            using_real_file = False
    else:
        # Use mock
        pbixray_server.current_model = MockPBIXRay("/path/to/test.pbix")
        using_real_file = False

    # This method wasn't modified to be async
    result = pbixray_server.get_metadata(mock_context)

    if using_real_file:
        assert result, "Expected metadata from PBIX file"
        assert isinstance(result, str), "Expected JSON string"
    else:
        assert "version" in result

    # Clean up
    pbixray_server.current_model = None


def test_get_model_size(pbix_file_path):
    """Test the get_model_size function"""
    # Create a mock Context
    mock_context = MagicMock()

    if pbix_file_path.exists() and pbixray_server.current_model is None:
        # Use actual PBIX file
        try:
            from pbixray import PBIXRay

            pbixray_server.current_model = PBIXRay(str(pbix_file_path))
            using_real_file = True
        except Exception:
            pbixray_server.current_model = MockPBIXRay("/path/to/test.pbix")
            using_real_file = False
    else:
        # Use mock
        pbixray_server.current_model = MockPBIXRay("/path/to/test.pbix")
        using_real_file = False

    # This method wasn't modified to be async
    result = pbixray_server.get_model_size(mock_context)

    if using_real_file:
        assert "bytes" in result
        assert "MB" in result
    else:
        assert "1024 bytes" in result

    # Clean up
    pbixray_server.current_model = None


@pytest.mark.asyncio
async def test_get_table_contents(pbix_file_path):
    """Test the get_table_contents function with actual PBIX file"""
    # Create a mock Context with async methods
    mock_context = MagicMock()
    mock_context.info = MagicMock(return_value=asyncio.Future())
    mock_context.info.return_value.set_result(None)
    mock_context.report_progress = MagicMock(return_value=asyncio.Future())
    mock_context.report_progress.return_value.set_result(None)

    if not pbix_file_path.exists():
        pytest.skip(f"PBIX file not found: {pbix_file_path}, skipping table contents test")

    # Load the PBIX file
    await pbixray_server.load_pbix_file(str(pbix_file_path), mock_context)

    # Get the list of tables
    tables_json = pbixray_server.get_tables(mock_context)
    tables = json.loads(tables_json)

    if not tables:
        pytest.skip("No tables found in PBIX file")

    # Test the get_table_contents function with the first table
    first_table = tables[0]
    result = await pbixray_server.get_table_contents(mock_context, first_table, page=1, page_size=5)

    # Verify the result
    assert result, "Expected table contents"
    assert isinstance(result, str), "Expected JSON string"

    # Parse JSON to make sure it's valid
    parsed = json.loads(result)
    assert "pagination" in parsed, "Expected pagination info"
    assert "data" in parsed, "Expected data in response"

    # Verify progress reporting
    assert mock_context.report_progress.call_count >= 2, "Progress should be reported multiple times"

    # Clean up
    pbixray_server.current_model = None
    pbixray_server.current_model_path = None


@pytest.mark.asyncio
async def test_get_model_summary(pbix_file_path):
    """Test the get_model_summary function"""
    # Create a mock Context with async methods
    mock_context = MagicMock()
    mock_context.info = MagicMock(return_value=asyncio.Future())
    mock_context.info.return_value.set_result(None)
    mock_context.report_progress = MagicMock(return_value=asyncio.Future())
    mock_context.report_progress.return_value.set_result(None)

    if pbix_file_path.exists() and pbixray_server.current_model is None:
        # Load the actual PBIX file first
        await pbixray_server.load_pbix_file(str(pbix_file_path), mock_context)
    else:
        # Fall back to mock if PBIX file is not available
        pbixray_server.current_model = MockPBIXRay("/path/to/test.pbix")
        pbixray_server.current_model_path = "/path/to/test.pbix"

    result = await pbixray_server.get_model_summary(mock_context)
    assert "file_path" in result
    assert "tables_count" in result
    assert "size_mb" in result

    # Clean up
    pbixray_server.current_model = None
    pbixray_server.current_model_path = None


@pytest.mark.asyncio
async def test_large_file_handling(pbix_file_path):
    """Test the large file handling specifically"""
    # Create a mock Context with async methods
    mock_context = MagicMock()
    mock_context.info = MagicMock(return_value=asyncio.Future())
    mock_context.info.return_value.set_result(None)
    mock_context.report_progress = MagicMock(return_value=asyncio.Future())
    mock_context.report_progress.return_value.set_result(None)

    if not pbix_file_path.exists():
        pytest.skip(f"PBIX file not found: {pbix_file_path}, skipping large file test")

    # Force the large file path by patching the file size detection
    # This will force the code to use the large file processing path
    with patch("os.path.getsize", return_value=60 * 1024 * 1024):  # Mock as 60MB to trigger large file handling
        result = await pbixray_server.load_pbix_file(str(pbix_file_path), mock_context)
        assert "Successfully loaded" in result

        # Verify that progress was reported multiple times
        progress_call_count = mock_context.report_progress.call_count
        assert progress_call_count >= 2, f"Progress reported only {progress_call_count} times"

        # Verify the model was loaded correctly
        assert pbixray_server.current_model is not None

        # Clean up
        pbixray_server.current_model = None
        pbixray_server.current_model_path = None
