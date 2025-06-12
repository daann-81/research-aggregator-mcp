# main.py - Async version
import asyncio
from datetime import datetime, timedelta
import logging
from rich.console import Console
from rich.table import Table

import sys
from pathlib import Path

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from src.arxiv.client import AsyncArxivClient, ArxivAPIError
from src.arxiv.parser import ArxivXMLParser

logger = logging.getLogger(__name__)
console = Console()

async def test_async_arxiv_integration():
    """Test the complete async arXiv client + parser integration"""
    console.print("🎯 [bold green]Testing Async ArXiv Client + Parser Integration[/bold green]")
    
    # Use async context manager for proper session handling
    async with AsyncArxivClient(delay_seconds=3.0) as client:
        parser = ArxivXMLParser()
        
        try:
            # Query recent papers
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')  # Last 30 days
            
            logger.info(f"📅 Querying papers from [bold blue]{start_date}[/bold blue] to [bold blue]{end_date}[/bold blue]")
            
            # Get XML data (async)
            xml_data = await client.search_trading_papers(start_date, end_date, max_results=10)
            
            # Parse XML into structured data
            papers = parser.parse_response(xml_data)
            
            # Display results
            if papers:
                await display_papers_table(papers)
                await show_detailed_paper_info(papers[0])
            else:
                console.print("📭 [yellow]No papers found in the specified date range[/yellow]")
                
        except ArxivAPIError as e:
            logger.error(f"💥 arXiv API error: [red]{e}[/red]")
        except Exception as e:
            logger.error(f"🔥 Unexpected error: [red bold]{e}[/red bold]")
            raise

async def test_async_pagination():
    """Test async pagination features"""
    console.print("\n🔄 [bold green]Testing Async Pagination[/bold green]")
    
    async with AsyncArxivClient(delay_seconds=3.0) as client:
        parser = ArxivXMLParser()
        
        try:
            # Test total count
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')  # Last 90 days
            
            console.print(f"\n📊 [bold]Getting Total Count[/bold]")
            total_count = await client.get_total_count("cat:q-fin.TR", start_date, end_date)
            console.print(f"Total trading papers in last 90 days: [bold blue]{total_count:,}[/bold blue]")
            
            if total_count > 0:
                # Test small pagination
                console.print(f"\n📄 [bold]Testing Pagination (limit 25 papers)[/bold]")
                xml_responses = await client.search_papers_paginated(
                    "cat:q-fin.TR", 
                    start_date, end_date,
                    max_total_results=25,
                    batch_size=10
                )
                
                console.print(f"Received [green]{len(xml_responses)}[/green] batches")
                
                # Parse all responses
                all_papers = []
                for i, xml_data in enumerate(xml_responses):
                    papers = parser.parse_response(xml_data)
                    all_papers.extend(papers)
                    console.print(f"  Batch {i+1}: {len(papers)} papers")
                
                console.print(f"Total papers parsed: [bold green]{len(all_papers)}[/bold green]")
                
                # Show sample results
                if all_papers:
                    await display_pagination_sample(all_papers[:3])
            else:
                console.print("📭 [yellow]No papers found in date range for pagination test[/yellow]")
                
        except Exception as e:
            console.print(f"🔥 [red bold]Pagination test error: {e}[/red bold]")

async def test_convenience_methods():
    """Test the async convenience methods"""
    console.print("\n🚀 [bold green]Testing Async Convenience Methods[/bold green]")
    
    async with AsyncArxivClient(delay_seconds=3.0) as client:
        parser = ArxivXMLParser()
        
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')  # Last 60 days
            
            console.print(f"\n📈 [bold]Testing search_all_quant_finance()[/bold]")
            
            # Test general quant finance search
            xml_data = await client.search_all_quant_finance(start_date, end_date, max_results=15)
            papers = parser.parse_response(xml_data)
            
            if papers:
                console.print(f"✅ Retrieved [bold green]{len(papers)}[/bold green] quant finance papers")
                
                # Show category distribution
                await show_category_distribution(papers)
            else:
                console.print("📭 [yellow]No quant finance papers found[/yellow]")
                
        except Exception as e:
            console.print(f"🔥 [red bold]Convenience methods test error: {e}[/red bold]")

async def display_papers_table(papers):
    """Display parsed papers in a nice table"""
    table = Table(title="📄 Recent Trading Papers from arXiv")
    
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="white", max_width=50)
    table.add_column("Authors", style="blue", max_width=30)
    table.add_column("Date", style="green")
    table.add_column("Categories", style="magenta", max_width=20)
    
    for paper in papers:
        # Format authors (show first 2)
        author_str = ", ".join(paper.authors[:2])
        if len(paper.authors) > 2:
            author_str += f" +{len(paper.authors)-2} more"
        
        # Format categories
        cat_str = ", ".join(paper.categories)
        
        table.add_row(
            paper.id,
            paper.title,
            author_str,
            paper.submitted_date.strftime('%Y-%m-%d'),
            cat_str
        )
    
    console.print(table)

async def show_detailed_paper_info(paper):
    """Show detailed info for a sample paper"""
    console.print(f"\n📋 [bold]Sample Paper Details:[/bold]")
    console.print(f"[cyan]Title:[/cyan] {paper.title}")
    console.print(f"[cyan]Authors:[/cyan] {', '.join(paper.authors)}")
    console.print(f"[cyan]Abstract:[/cyan] {paper.abstract[:300]}...")
    console.print(f"[cyan]PDF URL:[/cyan] {paper.pdf_url}")
    console.print(f"[cyan]Submitted:[/cyan] {paper.submitted_date.strftime('%Y-%m-%d %H:%M')}")
    console.print(f"[cyan]Categories:[/cyan] {', '.join(paper.categories)}")

async def display_pagination_sample(papers):
    """Display sample pagination results"""
    table = Table(title="📄 Pagination Sample Results")
    
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="white", max_width=40)
    table.add_column("Date", style="green")
    
    for paper in papers:
        table.add_row(
            paper.id,
            paper.title[:40] + "..." if len(paper.title) > 40 else paper.title,
            paper.submitted_date.strftime('%Y-%m-%d')
        )
    
    console.print(table)

async def show_category_distribution(papers):
    """Show distribution of papers by category"""
    categories = {}
    for paper in papers:
        for cat in paper.categories:
            categories[cat] = categories.get(cat, 0) + 1
    
    console.print(f"\n📊 [bold]Category Distribution:[/bold]")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        console.print(f"  {cat}: {count}")

async def run_all_tests():
    """Run all async tests"""
    console.print("🧪 [bold magenta]Starting Async ArXiv Client Test Suite[/bold magenta]")
    
    try:
        await test_async_arxiv_integration()
        await test_async_pagination()
        await test_convenience_methods()
        
        console.print("\n🎉 [bold green]All async tests completed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"\n💥 [red bold]Test suite failed: {e}[/red bold]")
        raise

if __name__ == "__main__":
    from src.util.logging import setup_logging
    setup_logging()
    # Run the async test suite
    asyncio.run(run_all_tests())