#!/usr/bin/env python3

import yaml
import urllib.request
import os
from rich.console import Console
from rich.table import Table
from rich.progress import Progress


def check_url(url):
    """Check if a URL is available by making a HEAD request."""
    try:
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 200
    except Exception:
        return False


def main():
    console = Console()
    
    # Load YAML file
    yaml_path = os.path.join(os.path.dirname(__file__), "pico-tools-urls.yaml")
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Collect all tools
    tools = set()
    for version_data in data['versions'].values():
        for os_data in version_data.values():
            if isinstance(os_data, dict):
                for arch_data in os_data.values():
                    if isinstance(arch_data, dict):
                        tools.update(arch_data.keys())
                    else:
                        # macOS case - no architecture subdivision
                        tools.update(os_data.keys())
                        break
    
    tools = sorted(tools)
    
    # Check all URLs for each version
    for version, version_data in data['versions'].items():
        console.print(f"\n[bold cyan]SDK Version {version}[/bold cyan]")
        
        # Create table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("OS + Arch", style="dim", width=20)
        
        for tool in tools:
            table.add_column(tool, justify="center")
        
        # Collect URLs and check availability
        rows = []
        total_checks = 0
        
        for os_name, os_data in version_data.items():
            if os_name == 'macos':
                # macOS - show separate rows for arm64 and x86_64
                # with fallback to universal if specific arch doesn't have the tool
                for arch in ['arm64', 'x86_64']:
                    row_name = f"{os_name}/{arch}"
                    total_checks += len(tools)
                    # Create combined dict with fallback to universal
                    combined_data = {}
                    if 'universal' in os_data:
                        combined_data.update(os_data['universal'])
                    if arch in os_data:
                        combined_data.update(os_data[arch])
                    rows.append((row_name, combined_data))
            else:
                # Linux and Windows have architecture subdivision
                for arch, arch_data in os_data.items():
                    row_name = f"{os_name}/{arch}"
                    total_checks += len(tools)
                    rows.append((row_name, arch_data))
        
        # Check URLs with progress bar
        results = {}
        with Progress(console=console, transient=True) as progress:
            task = progress.add_task(f"[green]Checking URLs for version {version}...", total=total_checks)
            
            for row_name, url_dict in rows:
                results[row_name] = {}
                for tool in tools:
                    if tool in url_dict:
                        url = url_dict[tool]
                        is_available = check_url(url)
                        results[row_name][tool] = is_available
                    else:
                        results[row_name][tool] = None
                    progress.update(task, advance=1)
        
        # Add rows to table
        for row_name, _ in rows:
            row_data = [row_name]
            for tool in tools:
                status = results[row_name].get(tool)
                if status is None:
                    row_data.append("[dim]N/A[/dim]")
                elif status:
                    row_data.append("[green]✓[/green]")
                else:
                    row_data.append("[red]✗[/red]")
            table.add_row(*row_data)
        
        console.print(table)


if __name__ == "__main__":
    main()
