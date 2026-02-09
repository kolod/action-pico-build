#!/usr/bin/env python3

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path


def detect_os_and_arch():
    """Detect the operating system and architecture.
    
    Returns:
        tuple: (os_type, arch) where os_type is 'linux', 'windows', or 'macos'
               and arch is 'x86_64' or 'aarch64'
    """
    os_type = platform.system().lower()
    if os_type == 'darwin':
        os_type = 'macos'
    elif os_type not in ['linux', 'windows']:
        raise ValueError(f"Unsupported operating system: {os_type}")
    
    arch = platform.machine()
    if arch in ["AMD64", "x86_64"]:
        arch = "x86_64"
    elif arch in ["ARM64", "aarch64"]:
        arch = "aarch64"
    
    return os_type, arch


def get_install_dir(os_type):
    """Get the installation directory based on OS.
    
    Args:
        os_type (str): Operating system type
        
    Returns:
        Path: Installation directory path
    """
    if os_type == 'windows':
        return Path(os.environ.get('USERPROFILE', Path.home())) / '.pico-sdk'
    else:
        return Path.home() / '.pico-sdk'


def verify_installation(install_dir):
    """Verify that required tools are installed.
    
    Args:
        install_dir (Path): Installation directory
        
    Raises:
        FileNotFoundError: If required directories are missing
    """
    required_dirs = ['pico-sdk', 'openocd', 'picotool', 'picosdktools', 'riscv-toolchain']
    missing = [d for d in required_dirs if not (install_dir / d).exists()]
    
    if missing:
        raise FileNotFoundError(
            f"Missing required tools: {', '.join(missing)}. "
            f"Please run install.py first to install the Pico SDK tools."
        )


def build_project(source_dir, build_dir, cmake_args=None, os_type='linux'):
    """Configure and build a Pico SDK project.
    
    Args:
        source_dir (Path): Source directory containing CMakeLists.txt
        build_dir (Path): Build output directory
        cmake_args (list): Additional CMake arguments
        os_type (str): Operating system type
        
    Returns:
        Path: Path to the build directory
        
    Raises:
        subprocess.CalledProcessError: If CMake configure or build fails
        FileNotFoundError: If CMakeLists.txt not found in source directory
    """
    # Verify CMakeLists.txt exists
    cmake_file = source_dir / 'CMakeLists.txt'
    if not cmake_file.exists():
        raise FileNotFoundError(f"CMakeLists.txt not found in {source_dir}")
    
    # Create build directory
    build_dir.mkdir(parents=True, exist_ok=True)
    
    # Get PICO_SDK_PATH from environment
    pico_sdk_path = os.environ.get('PICO_SDK_PATH')
    if not pico_sdk_path:
        raise EnvironmentError(
            "PICO_SDK_PATH environment variable not set. "
            "Please run install.py to set up the environment."
        )
    
    print(f"Source directory: {source_dir}")
    print(f"Build directory: {build_dir}")
    print(f"PICO_SDK_PATH: {pico_sdk_path}")
    
    # Prepare CMake command
    cmake_cmd = ['cmake', str(source_dir)]
    
    # Add generator for Windows (use Unix Makefiles to avoid MSVC)
    if os_type == 'windows':
        cmake_cmd.extend(['-G', 'Unix Makefiles'])
    
    # Add PICO_SDK_PATH
    cmake_cmd.append(f'-DPICO_SDK_PATH={pico_sdk_path}')
    
    # Add user-provided CMake arguments
    if cmake_args:
        cmake_cmd.extend(cmake_args)
    
    print(f"\nConfiguring with CMake...")
    print(f"Command: {' '.join(cmake_cmd)}")
    
    # Run CMake configure
    try:
        subprocess.run(cmake_cmd, cwd=build_dir, check=True)
    except subprocess.CalledProcessError as e:
        print(f"CMake configuration failed with exit code {e.returncode}")
        raise
    
    print(f"\nBuilding project...")
    
    # Run CMake build
    build_cmd = ['cmake', '--build', '.', '--config', 'Release']
    try:
        subprocess.run(build_cmd, cwd=build_dir, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Build failed with exit code {e.returncode}")
        raise
    
    print(f"\n✓ Build completed successfully!")
    print(f"Build artifacts are in: {build_dir}")
    
    return build_dir


def main():
    """Main entry point for the build script."""
    parser = argparse.ArgumentParser(
        description='Build Raspberry Pi Pico projects using installed Pico SDK tools'
    )
    parser.add_argument(
        '--source-dir',
        type=str,
        default='.',
        help='Source directory containing CMakeLists.txt (default: current directory)'
    )
    parser.add_argument(
        '--build-dir',
        type=str,
        default='build',
        help='Build output directory (default: build)'
    )
    parser.add_argument(
        '--cmake-args',
        type=str,
        nargs='*',
        help='Additional arguments to pass to CMake'
    )
    
    args = parser.parse_args()
    
    # Detect OS and architecture
    os_type, arch = detect_os_and_arch()
    print(f"Detected platform: {os_type} ({arch})")
    
    # Get installation directory and verify tools are installed
    install_dir = get_install_dir(os_type)
    print(f"Installation directory: {install_dir}")
    
    try:
        verify_installation(install_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    # Resolve source directory
    source_dir = Path(args.source_dir).resolve()
    
    # Resolve build directory (relative to source if not absolute)
    build_dir = Path(args.build_dir)
    if not build_dir.is_absolute():
        build_dir = source_dir / build_dir
    build_dir = build_dir.resolve()
    
    try:
        build_project(source_dir, build_dir, args.cmake_args, os_type)
        return 0
    except Exception as e:
        print(f"Build failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
