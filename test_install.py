#!/usr/bin/env python3

import os
import tempfile
import shutil
from pathlib import Path
from install import PicoInstaller


def test_download_and_extract_real_archive(tool: str, sdk_version: str, arch: str, os_type: str):
    """Test downloading and extracting a real archive from the YAML URLs."""
    print(f"Testing {tool} ({os_type}/{arch}, SDK {sdk_version})...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        dest_dir = Path(tmpdir) / "extracted"
        
        installer = PicoInstaller()
        
        try:
            # Get the URL from YAML
            url = installer.get_url(tool, sdk_version, arch, os_type)
            print(f"  URL: {url}")
            
            # Download and extract
            installer.load_and_unpack_url(url, str(dest_dir))
            
            # Verify extraction - check that destination directory exists and has content
            assert dest_dir.exists(), f"Destination directory not created"
            
            # Check that at least some files were extracted
            extracted_files = list(dest_dir.rglob('*'))
            assert len(extracted_files) > 0, f"No files extracted"
            
            print(f"  ✓ Successfully extracted {len(extracted_files)} files/directories")
            return True
            
        except ValueError as e:
            print(f"  ⊘ Skipped: {e}")
            return None
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            return False


def test_all_tools():
    """Test downloading and extracting archives for all available tools."""
    print("Testing real archive downloads and extraction...\n")
    
    # Test a few representative combinations across different OSes
    test_cases = [
        # (tool, sdk_version, arch, os_type)
        # Linux tests
        ("picotool", "2.2.0", "x86_64", "linux"),
        ("openocd", "2.2.0", "aarch64", "linux"),
        ("picosdktools", "2.1.1", "x86_64", "linux"),
        ("riscv-toolchain", "2.0.0", "aarch64", "linux"),
        # Windows tests
        ("picotool", "2.2.0", "x86_64", "windows"),
        ("openocd", "2.1.1", "x86_64", "windows"),
        ("riscv-toolchain", "2.2.0", "x86_64", "windows"),
        # macOS tests
        ("picotool", "2.2.0", "arm64", "macos"),
        ("openocd", "2.1.1", "x86_64", "macos"),
        ("riscv-toolchain", "2.0.0", "arm64", "macos"),
    ]
    
    results = []
    for tool, sdk_version, arch, os_type in test_cases:
        result = test_download_and_extract_real_archive(tool, sdk_version, arch, os_type)
        results.append((tool, sdk_version, arch, os_type, result))
    
    # Summary
    print("\n" + "="*70)
    print("Test Summary:")
    print("="*70)
    
    passed = sum(1 for _, _, _, _, r in results if r is True)
    failed = sum(1 for _, _, _, _, r in results if r is False)
    skipped = sum(1 for _, _, _, _, r in results if r is None)
    
    for tool, sdk_version, arch, os_type, result in results:
        status = "✓ PASS" if result is True else ("✗ FAIL" if result is False else "⊘ SKIP")
        print(f"  {status}: {tool:20} {os_type}/{arch:8} SDK {sdk_version}")
    
    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")
    
    return 0 if failed == 0 else 1


def main():
    try:
        return test_all_tools()
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
