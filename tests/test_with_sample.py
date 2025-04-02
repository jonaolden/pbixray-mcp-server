#!/usr/bin/env python3
"""
Test the PBIXRay MCP server with a sample PBIX file
"""

import os
import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters


async def main():
    """Test the PBIXRay MCP server with a sample file"""
    server_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "pbixray_server.py")
    sample_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo", "AdventureWorks Sales.pbix"
    )

    # Make sure the sample file exists
    if not os.path.exists(sample_file_path):
        print(f"Error: Sample file not found at {sample_file_path}")
        return

    # Start the server process
    server_params = StdioServerParameters(command="python", args=[server_path], env=None)

    print(f"Connecting to PBIXRay server and testing with file: {os.path.basename(sample_file_path)}")

    async with stdio_client(server_params) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            # Initialize the session
            await session.initialize()

            # Load the sample PBIX file
            print("\n1. Loading PBIX file...")
            load_result = await session.call_tool("load_pbix_file", {"file_path": sample_file_path})
            print_result(load_result)

            # Get model summary
            print("\n2. Getting model summary...")
            summary_result = await session.call_tool("get_model_summary", {})
            print_result(summary_result)

            # List tables
            print("\n3. Listing tables...")
            tables_result = await session.call_tool("get_tables", {})
            print_result(tables_result)

            # Get DAX measures
            print("\n4. Getting DAX measures...")
            measures_result = await session.call_tool("get_dax_measures", {})
            print_result(measures_result)

            # Get relationships
            print("\n5. Getting relationships...")
            rel_result = await session.call_tool("get_relationships", {})
            print_result(rel_result)

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
