#!/usr/bin/env python3
"""
Unified Integration Test Runner

This script runs all integration tests in the integration folder, providing
a single entry point to validate the entire system functionality.

Usage:
    python integration/run_all_integration_tests.py
    
    OR
    
    ./integration/run_all_integration_tests.py

This will run:
- MCP Server Integration Tests
- arXiv Connection Tests  
- SSRN Connection Tests
- Unified Search Integration Tests

Exit codes:
- 0: All tests passed
- 1: Some tests failed
- 130: Tests interrupted by user
"""

import asyncio
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import all integration test modules
try:
    from integration.mcp_server_test import run_all_tests as run_mcp_server_tests
    from integration.arxiv_connection_test import run_all_tests as run_arxiv_tests
    from integration.ssrn_connection_test import run_all_tests as run_ssrn_tests
    from integration.unified_search_integration_test import run_integration_tests as run_unified_search_tests
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

# Setup logging
try:
    from src.util.logging import setup_logging
    setup_logging(logToStdout=True)
except ImportError:
    # Fallback if logging utility not available
    import logging
    logging.basicConfig(level=logging.INFO)

console = Console()

class IntegrationTestResult:
    """Container for integration test results"""
    def __init__(self, name: str, passed: bool, duration: float, error: str = ""):
        self.name = name
        self.passed = passed
        self.duration = duration
        self.error = error if error else ""

async def run_test_suite(name: str, test_func, *args) -> IntegrationTestResult:
    """Run a single test suite and capture results"""
    console.print(f"\n{'='*80}")
    console.print(f"🧪 [bold blue]Running {name}[/bold blue]")
    console.print(f"{'='*80}")
    
    start_time = datetime.now()
    
    try:
        # Run the test function
        if args:
            result = await test_func(*args)
        else:
            result = await test_func()
            
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Check if result indicates success (some tests return boolean, others return None)
        if result is False:
            return IntegrationTestResult(name, False, duration, "Test suite reported failure")
        else:
            return IntegrationTestResult(name, True, duration)
            
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        error_msg = f"{type(e).__name__}: {str(e)}"
        console.print(f"💥 [red]Test suite crashed: {error_msg}[/red]")
        return IntegrationTestResult(name, False, duration, error_msg)

async def run_all_integration_tests() -> List[IntegrationTestResult]:
    """Run all integration test suites"""
    
    console.print(Panel.fit(
        "[bold blue]🚀 Research Aggregator MCP - Full Integration Test Suite[/bold blue]\n"
        "Running comprehensive tests across all components...",
        border_style="blue"
    ))
    
    # Define all test suites to run
    test_suites = [
        ("MCP Server Integration", run_mcp_server_tests),
        ("arXiv Connection", run_arxiv_tests),
        ("SSRN Connection", run_ssrn_tests),
        ("Unified Search Integration", run_unified_search_tests),
    ]
    
    results = []
    
    for suite_name, test_func in test_suites:
        try:
            # Special handling for SSRN tests which expect arguments
            if "SSRN" in suite_name:
                # SSRN test expects a list of test tuples
                from integration.ssrn_connection_test import recent_papers_test
                result = await run_test_suite(suite_name, test_func, [("Recent Papers", recent_papers_test)])
            else:
                result = await run_test_suite(suite_name, test_func)
                
            results.append(result)
            
        except Exception as e:
            console.print(f"💥 [red]Failed to run {suite_name}: {e}[/red]")
            results.append(IntegrationTestResult(suite_name, False, 0.0, str(e)))
    
    return results

def display_results_summary(results: List[IntegrationTestResult]):
    """Display a comprehensive summary of all test results"""
    
    console.print(f"\n{'='*80}")
    console.print("📊 [bold]Integration Test Results Summary[/bold]")
    console.print(f"{'='*80}")
    
    # Create results table
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Test Suite", style="cyan", width=30)
    table.add_column("Status", justify="center", width=10)
    table.add_column("Duration", justify="right", width=10)
    table.add_column("Error", style="red", width=50)
    
    passed_count = 0
    total_duration = 0.0
    
    for result in results:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        duration_str = f"{result.duration:.2f}s"
        error_str = result.error[:47] + "..." if result.error and len(result.error) > 50 else (result.error or "")
        
        table.add_row(
            result.name,
            status,
            duration_str,
            error_str
        )
        
        if result.passed:
            passed_count += 1
        total_duration += result.duration
    
    console.print(table)
    
    # Overall summary
    total_tests = len(results)
    success_rate = (passed_count / total_tests) * 100 if total_tests > 0 else 0
    
    console.print(f"\n🎯 [bold]Overall Results:[/bold]")
    console.print(f"   Passed: {passed_count}/{total_tests} ({success_rate:.1f}%)")
    console.print(f"   Total Duration: {total_duration:.2f} seconds")
    
    if passed_count == total_tests:
        console.print("\n🎉 [bold green]All integration tests passed! System is ready.[/bold green]")
        return True
    else:
        console.print(f"\n⚠️ [bold yellow]{total_tests - passed_count} test suite(s) failed. Check errors above.[/bold yellow]")
        return False

async def main():
    """Main entry point for integration test runner"""
    start_time = datetime.now()
    
    try:
        console.print(f"🕐 Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all integration tests
        results = await run_all_integration_tests()
        
        # Display comprehensive summary
        all_passed = display_results_summary(results)
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        console.print(f"\n🕐 Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        console.print(f"⏱️ Total execution time: {total_time:.2f} seconds")
        
        # Exit with appropriate code
        sys.exit(0 if all_passed else 1)
        
    except KeyboardInterrupt:
        console.print("\n🛑 [yellow]Tests interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n💥 [red bold]Integration test runner failed: {e}[/red bold]")
        console.print(f"[red]Traceback:[/red]\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())