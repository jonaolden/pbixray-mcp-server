#!/usr/bin/env python3
"""
Test script for the enhanced pagination and filtering capabilities of the PBIXRay MCP server.
With stricter output limits to test performance with large models.
"""

import os
import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters


async def main():
    """Test the PBIXRay MCP server with a sample file, focusing on pagination and filtering"""
    # Use stricter output limits to simulate large model behavior
    server_params = StdioServerParameters(
        command="python", args=["src/pbixray_server.py", "--page-size", "3", "--max-rows", "5"], env=None
    )

    # Path to the sample file
    sample_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo", "AdventureWorks Sales.pbix")

    # Make sure the sample file exists
    if not os.path.exists(sample_file_path):
        print(f"Error: Sample file not found at {sample_file_path}")
        return

    print(f"Testing PBIXRay server with new pagination and filtering capabilities...")
    print(f"Sample file: {os.path.basename(sample_file_path)}")

    async with stdio_client(server_params) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            # Initialize the session
            await session.initialize()

            # Load the sample PBIX file
            print("\n1. Loading PBIX file...")
            load_result = await session.call_tool("load_pbix_file", {"file_path": sample_file_path})
            print_result(load_result)

            # Test pagination for table contents with smaller page size (3 rows)
            print("\n2. Testing pagination - Page 1 of table contents (3 rows)...")
            table_result = await session.call_tool("get_table_contents", {"table_name": "Sales", "page": 1, "page_size": 3})
            print_result(table_result)

            print("\n3. Testing pagination - Page 2 of table contents (3 rows)...")
            table_result_p2 = await session.call_tool("get_table_contents", {"table_name": "Sales", "page": 2, "page_size": 3})
            print_result(table_result_p2)

            print("\n4. Testing pagination - Page 3 of table contents (3 rows)...")
            table_result_p3 = await session.call_tool("get_table_contents", {"table_name": "Sales", "page": 3, "page_size": 3})
            print_result(table_result_p3)

            # Test with very small page size (1 row)
            print("\n5. Testing with minimal page size (1 row) - Page 1...")
            table_result_single = await session.call_tool(
                "get_table_contents", {"table_name": "Sales", "page": 1, "page_size": 1}
            )
            print_result(table_result_single)

            # Test filtering of DAX measures
            print("\n6. Testing measure filtering by table...")
            sales_measures = await session.call_tool("get_dax_measures", {"table_name": "Sales"})
            print_result(sales_measures)

            # Test filtering of relationships
            print("\n7. Testing relationship filtering by from_table...")
            sales_relations = await session.call_tool("get_relationships", {"from_table": "Sales"})
            print_result(sales_relations)

            # Test filtering of schema by table
            print("\n8. Testing schema filtering by table...")
            customer_schema = await session.call_tool("get_schema", {"table_name": "Customer"})
            print_result(customer_schema)

            # Test performance logging with large page number (should trigger elapsed time logging)
            print("\n9. Testing performance monitoring for large page access...")
            # This should trigger the performance logging for large tables
            large_result = await session.call_tool("get_table_contents", {"table_name": "Sales", "page": 100, "page_size": 2})
            print_result(large_result)

            print("\nAll tests completed successfully!")


def print_result(result):
    """Print tool call results in a readable format"""
    for content in result.content:
        if hasattr(content, "text") and content.text:
            try:
                # Try to parse and pretty print JSON
                data = json.loads(content.text)
                print(json.dumps(data, indent=2))
            except json.JSONDecodeError:
                # Regular text output
                print(content.text)


if __name__ == "__main__":
    asyncio.run(main())
