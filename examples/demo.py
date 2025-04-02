#!/usr/bin/env python3
"""
Demo script for the PBIXRay MCP Server

This script demonstrates how to use the MCP client to interact with the PBIXRay server.
"""

import os
import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters


async def main():
    """Run the demo with the PBIXRay MCP server"""
    # Replace this with the path to your PBIX file or use the provided sample
    sample_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo", "AdventureWorks Sales.pbix"
    )

    # Make sure the file exists
    if not os.path.exists(sample_file_path):
        print(f"Sample file not found at {sample_file_path}")
        print("Please specify a valid PBIX file path or download a sample file to the demo directory.")
        return

    # Make sure the server script exists
    server_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "pbixray_server.py")
    if not os.path.exists(server_path):
        print(f"Error: Server script not found at {server_path}")
        return

    # Start the server process
    server_params = StdioServerParameters(command="python", args=[server_path], env=None)

    print(f"=== PBIXRay MCP Server Demo ===")
    print(f"Connecting to server and analyzing: {os.path.basename(sample_file_path)}")

    async with stdio_client(server_params) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()

            # List the available tools
            tools_response = await session.list_tools()
            print("\n=== Available Tools ===")
            for tool in tools_response.tools:
                print(f"- {tool.name}")

            # Load a PBIX file
            print(f"\n=== Loading PBIX File ===")
            load_result = await session.call_tool("load_pbix_file", {"file_path": sample_file_path})
            print_result(load_result)

            # Get model summary
            print("\n=== Model Summary ===")
            summary_result = await session.call_tool("get_model_summary", {})
            print_result(summary_result)

            # Menu for more detailed analysis
            while True:
                print("\n=== Analysis Options ===")
                print("1. Show tables")
                print("2. Show metadata")
                print("3. Show Power Query (M) code")
                print("4. Show DAX measures")
                print("5. Show relationships")
                print("6. Show schema")
                print("7. Show model statistics")
                print("8. Exit demo")

                choice = input("\nSelect an option (1-8): ")

                if choice == "1":
                    # Show tables
                    print("\n=== Tables ===")
                    tables_result = await session.call_tool("get_tables", {})
                    print_result(tables_result)

                    # Ask if user wants to see contents of a specific table
                    see_contents = input("\nWould you like to see the contents of a specific table? (y/n): ")
                    if see_contents.lower() == "y":
                        table_name = input("Enter the table name: ")
                        print(f"\n=== Contents of {table_name} ===")
                        contents_result = await session.call_tool("get_table_contents", {"table_name": table_name})
                        print_result(contents_result)

                elif choice == "2":
                    # Show metadata
                    print("\n=== Metadata ===")
                    metadata_result = await session.call_tool("get_metadata", {})
                    print_result(metadata_result)

                elif choice == "3":
                    # Show Power Query code
                    print("\n=== Power Query Code ===")
                    pq_result = await session.call_tool("get_power_query", {})
                    print_result(pq_result)

                elif choice == "4":
                    # Show DAX measures
                    print("\n=== DAX Measures ===")
                    measures_result = await session.call_tool("get_dax_measures", {})
                    print_result(measures_result)

                elif choice == "5":
                    # Show relationships
                    print("\n=== Relationships ===")
                    rel_result = await session.call_tool("get_relationships", {})
                    print_result(rel_result)

                elif choice == "6":
                    # Show schema
                    print("\n=== Schema ===")
                    schema_result = await session.call_tool("get_schema", {})
                    print_result(schema_result)

                elif choice == "7":
                    # Show model statistics
                    print("\n=== Model Statistics ===")
                    stats_result = await session.call_tool("get_statistics", {})
                    print_result(stats_result)

                elif choice == "8":
                    print("\nExiting demo...")
                    break

                else:
                    print("\nInvalid choice. Please try again.")


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
