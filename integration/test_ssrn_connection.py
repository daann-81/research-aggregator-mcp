"""
SSRN API Integration Test

Test the complete SSRN client + parser integration to verify API connectivity,
response format, and filtering capabilities.
"""

import asyncio
from datetime import datetime, timedelta
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import json

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from src.ssrn.client import AsyncSSRNClient, SSRNAPIError
from src.ssrn.parser import SSRNJSONParser, SSRNPaper
from src.util.logging import setup_logging

logger = logging.getLogger(__name__)
console = Console()


async def test_ssrn_api_connectivity():
    """Test basic SSRN API connectivity and response format"""
    console.print("🔌 [bold green]Testing SSRN API Connectivity[/bold green]")

    async with AsyncSSRNClient(delay_seconds=3.0) as client:
        try:
            # Test basic API call with minimal parameters
            params = {"index": 0, "count": 5, "sort": 0}
            response = await client._make_request(params)

            console.print(f"✅ [green]API Response Status: Success[/green]")
            console.print(f"📊 Response keys: {list(response.keys())}")

            papers = response.get("papers", [])
            if papers:
                console.print(f"📄 Found {len(papers)} papers")
                console.print(f"🔍 First paper keys: {list(papers[0].keys())}")

                # Show sample paper structure
                sample_paper = papers[0]
                console.print(
                    Panel(
                        json.dumps(sample_paper, indent=2, default=str)[:500] + "...",
                        title="Sample Paper Structure",
                        border_style="blue",
                    )
                )
            else:
                console.print("⚠️ [yellow]No papers in response[/yellow]")

            return True

        except SSRNAPIError as e:
            console.print(f"❌ [red]SSRN API Error: {e}[/red]")
            return False
        except Exception as e:
            console.print(f"💥 [red]Unexpected Error: {e}[/red]")
            return False


async def test_ssrn_parser():
    """Test SSRN JSON parser functionality"""
    console.print("🔧 [bold green]Testing SSRN JSON Parser[/bold green]")

    parser = SSRNJSONParser()

    async with AsyncSSRNClient(delay_seconds=3.0) as client:
        try:
            # Get sample data from API
            params = {"index": 0, "count": 10, "sort": 0}
            response_data = await client._make_request(params)

            # Parse response
            papers = parser.parse_response(response_data)

            if papers:
                console.print(
                    f"✅ [green]Successfully parsed {len(papers)} papers[/green]"
                )

                # Show details of first paper
                first_paper = papers[0]
                await display_paper_details(first_paper)

                return papers
            else:
                console.print("⚠️ [yellow]No papers parsed[/yellow]")
                return []

        except Exception as e:
            console.print(f"❌ [red]Parser Error: {e}[/red]")
            return []


async def test_text_search():
    """Test text search functionality"""
    console.print("🔍 [bold green]Testing Text Search[/bold green]")

    async with AsyncSSRNClient(delay_seconds=3.0) as client:
        try:
            # Test with finance-related keywords
            query = "finance"
            console.print(f"🔍 Searching for papers containing: '{query}'")

            papers = await client.search_papers(query, max_results=10)

            if papers:
                console.print(
                    f"✅ [green]Found {len(papers)} papers containing '{query}'[/green]"
                )

                # Show sample titles
                for i, paper in enumerate(papers[:3]):
                    title = paper.get("title", "")[:100] + "..."
                    console.print(f"   Paper {i+1}: {title}")

                return True
            else:
                console.print(
                    f"⚠️ [yellow]No papers found containing '{query}'[/yellow]"
                )
                return False

        except Exception as e:
            console.print(f"❌ [red]Text Search Error: {e}[/red]")
            return False


async def test_author_search():
    """Test author search functionality"""
    console.print("👤 [bold green]Testing Author Search[/bold green]")

    async with AsyncSSRNClient(delay_seconds=3.0) as client:
        try:
            # Test with an actual author name from the data (seen in API response)
            author_name = "Kodongo"
            console.print(f"🔍 Searching for papers by author: '{author_name}'")

            papers = await client.search_by_author(author_name, max_results=10)

            if papers:
                console.print(
                    f"✅ [green]Found {len(papers)} papers by authors matching '{author_name}'[/green]"
                )

                # Show author examples
                for i, paper in enumerate(papers[:3]):
                    authors = paper.get("authors", [])
                    console.print(f"   Paper {i+1}: {authors}")

                return True
            else:
                console.print(
                    f"⚠️ [yellow]No papers found for author '{author_name}'[/yellow]"
                )
                return False

        except Exception as e:
            console.print(f"❌ [red]Author Search Error: {e}[/red]")
            return False


async def test_recent_papers():
    """Test recent papers functionality"""
    console.print("📅 [bold green]Testing Recent Papers Retrieval[/bold green]")

    async with AsyncSSRNClient(delay_seconds=3.0) as client:
        try:
            months_back = 1
            console.print(f"🔍 Searching for papers from last {months_back} months")

            papers = await client.get_recent_papers(
                months_back=months_back, max_results=1500
            )

            if papers:
                console.print(f"✅ [green]Found {len(papers)} recent papers[/green]")

                # Show date distribution
                date_counts = {}
                for paper in papers:
                    pub_date = paper.get("approved_date", "")
                    if pub_date:
                        year_month = pub_date[:7]  # YYYY-MM
                        date_counts[year_month] = date_counts.get(year_month, 0) + 1

                if date_counts:
                    console.print("📊 Date Distribution:")
                    for date, count in sorted(date_counts.items(), reverse=True):
                        console.print(f"   {date}: {count} papers")

                return True
            else:
                console.print(f"⚠️ [yellow]No recent papers found[/yellow]")
                return False

        except Exception as e:
            console.print(f"❌ [red]Recent Papers Error: {e}[/red]")
            return False


async def test_finance_papers_search():
    """Test finance-specific papers search"""
    console.print("💰 [bold green]Testing Finance Papers Search[/bold green]")

    async with AsyncSSRNClient(delay_seconds=3.0) as client:
        try:
            console.print("🔍 Searching for finance papers using multiple JEL codes")

            papers = await client.search_finance_papers(max_results=15)

            if papers:
                console.print(f"✅ [green]Found {len(papers)} finance papers[/green]")

                # Show title keyword distribution
                keyword_counts = {}
                finance_keywords = [
                    "finance",
                    "financial",
                    "investment",
                    "trading",
                    "market",
                ]
                for paper in papers:
                    title = paper.get("title", "").lower()
                    for keyword in finance_keywords:
                        if keyword in title:
                            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

                if keyword_counts:
                    console.print("📊 Finance Keyword Distribution:")
                    for keyword, count in sorted(
                        keyword_counts.items(), key=lambda x: x[1], reverse=True):
                        console.print(f"   {keyword}: {count} papers")

                return True
            else:
                console.print("⚠️ [yellow]No finance papers found[/yellow]")
                return False

        except Exception as e:
            console.print(f"❌ [red]Finance Papers Error: {e}[/red]")
            return False


async def display_paper_details(paper: SSRNPaper):
    """Display detailed information about a paper"""
    table = Table(
        title="Sample SSRN Paper Details", show_header=True, header_style="bold magenta"
    )
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    table.add_row("SSRN ID", paper.ssrn_id)
    table.add_row(
        "Title", paper.title[:100] + "..." if len(paper.title) > 100 else paper.title
    )
    table.add_row(
        "Authors",
        ", ".join(paper.authors[:3]) + ("..." if len(paper.authors) > 3 else ""),
    )
    table.add_row("Approved Date", paper.approved_date.strftime("%Y-%m-%d"))
    table.add_row("Download Count", str(paper.download_count))
    table.add_row(
        "Affiliations",
        ", ".join(paper.university_affiliations[:2])
        + ("..." if len(paper.university_affiliations) > 2 else ""),
    )
    table.add_row("Abstract Type", paper.abstract_type)
    table.add_row("Publication Status", paper.publication_status)
    table.add_row("Page Count", str(paper.page_count))
    table.add_row("Is Approved", str(paper.is_approved))

    console.print(table)


async def run_all_tests(tests=None):
    """Run all SSRN integration tests"""
    console.print(Panel("🚀 SSRN API Integration Test Suite", style="bold green"))

    tests = [
        ("API Connectivity", test_ssrn_api_connectivity),
        ("JSON Parser", test_ssrn_parser),
        ("Text Search", test_text_search),
        ("Author Search", test_author_search),
        ("Recent Papers", test_recent_papers),
        ("Finance Papers", test_finance_papers_search),
    ] if tests is None else tests

    results = []

    for test_name, test_func in tests:
        console.print(f"\n{'='*50}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            console.print(f"💥 [red]{test_name} failed with exception: {e}[/red]")
            results.append((test_name, False))
        await asyncio.sleep(3)

    # Summary
    console.print(f"\n{'='*50}")
    console.print("📊 [bold green]Test Results Summary[/bold green]")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        console.print(f"   {test_name}: {status}")

    console.print(f"\n📈 Overall: {passed}/{total} tests passed")

    if passed == total:
        console.print(
            "🎉 [bold green]All tests passed! SSRN integration is working correctly.[/bold green]"
        )
    else:
        console.print(
            f"⚠️ [yellow]{total - passed} tests failed. Check the errors above.[/yellow]"
        )


async def main():
    """Main test function"""
    setup_logging(logToStdout=True)
    await run_all_tests([("Recent Papers", test_recent_papers)])


if __name__ == "__main__":
    asyncio.run(main())
