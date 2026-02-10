#!/usr/bin/env python3

import os
from pathlib import Path
from install import PicoInstaller
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box


class PicoToolsTester:
    """Test suite for Pico SDK tools installation and extraction.
    
    This class validates that tools can be downloaded and extracted correctly
    across different platforms and architectures. Files are preserved in the
    .pico-sdk directory structure for inspection and reuse.
    
    Attributes:
        console (Console): Rich console for formatted output
        base_dir (Path): Base directory for storing downloaded files (./.pico-sdk)
    """
    
    def __init__(self):
        """Initialize the tester with Rich console and base directory."""
        self.console = Console()
        self.base_dir = Path("./.pico-sdk")
    
    def test_download_and_extract_real_archive(self, tool: str, sdk_version: str, arch: str, os_type: str):
        """Test downloading and extracting a real archive from the YAML URLs.
        
        Args:
            tool (str): Tool name (openocd, picotool, picosdktools, riscv-toolchain)
            sdk_version (str): SDK version (e.g., '2.2.0')
            arch (str): Architecture (x86_64, aarch64, arm64)
            os_type (str): Operating system (linux, windows, macos)
        
        Returns:
            bool or None: True if successful, False if failed, None if skipped
        """
        self.console.print(f"Testing [cyan]{tool}[/cyan] ([yellow]{os_type}/{arch}[/yellow], SDK [green]{sdk_version}[/green])...")
        
        # Use persistent directory structure: ./.pico-sdk/{sdk-version}/{os_type}/{tool}/
        dest_dir = self.base_dir / sdk_version / os_type / tool
        
        installer = PicoInstaller()
        
        try:
            # Get the URL from YAML
            url = installer.get_url(tool, sdk_version, arch, os_type)
            self.console.print(f"  URL: [dim]{url}[/dim]")
            
            # Download and extract
            installer.load_and_unpack_url(url, str(dest_dir))
            
            # Verify extraction - check that destination directory exists and has content
            assert dest_dir.exists(), f"Destination directory not created"
            
            # Check that at least some files were extracted
            extracted_files = list(dest_dir.rglob('*'))
            assert len(extracted_files) > 0, f"No files extracted"
            
            self.console.print(f"  [green]✓[/green] Successfully extracted {len(extracted_files)} files/directories")
            self.console.print(f"  [dim]Saved to: {dest_dir}[/dim]")
            return True
            
        except ValueError as e:
            self.console.print(f"  [yellow]⊘ Skipped: {e}[/yellow]")
            return None
        except Exception as e:
            self.console.print(f"  [red]✗ Failed: {e}[/red]")
            return False
    
    def test_all_tools(self):
        """Test downloading and extracting archives for all available tools.
        
        Returns:
            int: Exit code (0 for success, 1 for failures)
        """
        self.console.print(Panel.fit(
            "[bold cyan]Testing Pico SDK Tools Installation[/bold cyan]\\n"
            "Downloading and extracting real archives from GitHub releases",
            box=box.DOUBLE
        ))
        self.console.print()
        
        # Test a few representative combinations across different OSes
        test_cases = [
            # (tool, sdk_version, arch, os_type)
            # Linux tests
            ("openocd", "2.2.0", "aarch64", "linux"),
            ("picotool", "2.2.0", "x86_64", "linux"),
            ("picosdktools", "2.2.0", "x86_64", "linux"),
            ("riscv-toolchain", "2.2.0", "aarch64", "linux"),
            # Windows tests
            ("openocd", "2.2.0", "x86_64", "windows"),
            ("picotool", "2.2.0", "x86_64", "windows"),
            ("picosdktools", "2.2.0", "x86_64", "windows"),
            ("riscv-toolchain", "2.2.0", "x86_64", "windows"),
            # macOS tests
            ("picotool", "2.2.0", "arm64", "macos"),
            ("openocd", "2.2.0", "x86_64", "macos"),
            ("riscv-toolchain", "2.2.0", "arm64", "macos"),
        ]
        
        results = []
        for tool, sdk_version, arch, os_type in test_cases:
            result = self.test_download_and_extract_real_archive(tool, sdk_version, arch, os_type)
            results.append((tool, sdk_version, arch, os_type, result))
        
        # Summary using Rich table
        self.console.print()
        self.print_summary(results)
        
        passed = sum(1 for _, _, _, _, r in results if r is True)
        failed = sum(1 for _, _, _, _, r in results if r is False)
        
        return 0 if failed == 0 else 1
    
    def print_summary(self, results):
        """Print a formatted summary table using Rich.
        
        Args:
            results (list): List of tuples (tool, sdk_version, arch, os_type, result)
        """
        # Create summary table
        table = Table(title="Test Summary", box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("Status", style="bold", width=8)
        table.add_column("Tool", style="cyan", width=20)
        table.add_column("Platform", style="yellow", width=15)
        table.add_column("SDK Version", style="green", width=12)
        
        for tool, sdk_version, arch, os_type, result in results:
            if result is True:
                status = "[green]✓ PASS[/green]"
            elif result is False:
                status = "[red]✗ FAIL[/red]"
            else:
                status = "[yellow]⊘ SKIP[/yellow]"
            
            platform = f"{os_type}/{arch}"
            table.add_row(status, tool, platform, sdk_version)
        
        self.console.print(table)
        
        # Print totals
        passed = sum(1 for _, _, _, _, r in results if r is True)
        failed = sum(1 for _, _, _, _, r in results if r is False)
        skipped = sum(1 for _, _, _, _, r in results if r is None)
        
        total_panel = Panel(
            f"[green]✓ Passed: {passed}[/green]  "
            f"[red]✗ Failed: {failed}[/red]  "
            f"[yellow]⊘ Skipped: {skipped}[/yellow]",
            title="Totals",
            box=box.ROUNDED
        )
        self.console.print(total_panel)


def main():
    """Main entry point for the test suite."""
    try:
        tester = PicoToolsTester()
        return tester.test_all_tools()
    except Exception as e:
        console = Console()
        console.print(f"\n[red]✗ Unexpected error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
