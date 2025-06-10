# test_mcp_server.py
"""
Test script for the MCP server - simulates what Claude would do
"""
import asyncio
import json

from rich.console import Console
from rich.table import Table
from rich.json import JSON

# Import our MCP server functions
import sys
from pathlib import Path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from server.shared import (
    handle_search_trading_papers,
    handle_search_quant_finance_papers, 
    handle_get_recent_papers
)

console = Console()

async def test_search_trading_papers():
    """Test the search_trading_papers tool"""
    console.print("\n🔍 [bold blue]Testing search_trading_papers[/bold blue]")
    
    # Test with default parameters
    arguments = {"max_results": 5}  # Small number for testing
    
    try:
        result = await handle_search_trading_papers(arguments)
        data = json.loads(result)
        
        console.print(f"✅ Found {data['total_found']} papers")
        console.print(f"📅 Date range: {data['date_range']['start']} to {data['date_range']['end']}")
        
        if data['papers']:
            # Show first paper
            paper = data['papers'][0]
            console.print(f"\n📄 [bold]Sample Paper:[/bold]")
            console.print(f"Title: {paper['title']}")
            console.print(f"Authors: {', '.join(paper['authors'][:3])}")
            console.print(f"Categories: {', '.join(paper['categories'])}")
            console.print(f"Submitted: {paper['submitted_date'][:10]}")
        
        return True
        
    except Exception as e:
        console.print(f"❌ Error: {e}")
        return False

async def test_search_quant_finance_papers():
    """Test the search_quant_finance_papers tool"""
    console.print("\n🔍 [bold blue]Testing search_quant_finance_papers[/bold blue]")
    
    arguments = {"max_results": 5}  # Small number for testing
    
    try:
        result = await handle_search_quant_finance_papers(arguments)
        data = json.loads(result)
        
        console.print(f"✅ Found {data['total_found']} papers")
        console.print(f"📊 Category breakdown:")
        
        for category, count in list(data['category_breakdown'].items())[:5]:
            console.print(f"  {category}: {count}")
        
        return True
        
    except Exception as e:
        console.print(f"❌ Error: {e}")
        return False

async def test_get_recent_papers():
    """Test the get_recent_papers tool"""
    console.print("\n🔍 [bold blue]Testing get_recent_papers[/bold blue]")
    
    arguments = {
        "months_back": 3,
        "category": "q-fin.TR",
        "max_results": 5
    }
    
    try:
        result = await handle_get_recent_papers(arguments)
        data = json.loads(result)
        
        console.print(f"✅ Found {data['total_found']} papers in {data['category']}")
        console.print(f"📅 Looking back {data['months_back']} months")
        
        return True
        
    except Exception as e:
        console.print(f"❌ Error: {e}")
        return False

async def test_error_handling():
    """Test error handling"""
    console.print("\n🔍 [bold blue]Testing error handling[/bold blue]")
    
    # Test with invalid parameters
    arguments = {"months_back": None}  # Should fail
    
    try:
        result = await handle_get_recent_papers(arguments)
        if "Error" in result:
            console.print("✅ Error handling works correctly")
            return True
        else:
            console.print("❌ Error handling failed")
            return False
            
    except Exception as e:
        console.print(f"✅ Caught expected error: {type(e).__name__}")
        return True

async def test_json_format():
    """Test that the JSON output is properly formatted"""
    console.print("\n🔍 [bold blue]Testing JSON format[/bold blue]")
    
    arguments = {"max_results": 2}
    
    try:
        result = await handle_search_trading_papers(arguments)
        data = json.loads(result)  # This will fail if JSON is invalid
        
        # Check required fields
        required_fields = ["search_query", "date_range", "total_found", "papers"]
        for field in required_fields:
            if field not in data:
                console.print(f"❌ Missing required field: {field}")
                return False
        
        console.print("✅ JSON format is valid and complete")
        
        # Pretty print a sample
        if data['papers']:
            console.print("\n📄 [bold]Sample JSON output:[/bold]")
            sample_paper = data['papers'][0]
            console.print(JSON(json.dumps(sample_paper, indent=2)))
        
        return True
        
    except json.JSONDecodeError as e:
        console.print(f"❌ Invalid JSON: {e}")
        return False
    except Exception as e:
        console.print(f"❌ Error: {e}")
        return False

async def run_all_tests():
    """Run all MCP server tests"""
    console.print("🧪 [bold magenta]MCP Server Test Suite[/bold magenta]")
    
    tests = [
        ("Trading Papers Search", test_search_trading_papers),
        ("Quant Finance Search", test_search_quant_finance_papers),
        ("Recent Papers Search", test_get_recent_papers),
        ("Error Handling", test_error_handling),
        ("JSON Format", test_json_format)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        console.print(f"\n{'='*60}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            console.print(f"💥 Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    console.print(f"\n{'='*60}")
    console.print("📊 [bold]Test Results Summary[/bold]")
    
    table = Table()
    table.add_column("Test", style="cyan")
    table.add_column("Result", style="white")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        table.add_row(test_name, status)
        if result:
            passed += 1
    
    console.print(table)
    console.print(f"\n🎯 [bold]Passed: {passed}/{len(results)} tests[/bold]")
    
    if passed == len(results):
        console.print("🎉 [bold green]All tests passed! MCP server is ready.[/bold green]")
    else:
        console.print("⚠️ [bold yellow]Some tests failed. Check the errors above.[/bold yellow]")

if __name__ == "__main__":
    asyncio.run(run_all_tests())