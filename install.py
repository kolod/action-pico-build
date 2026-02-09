#!/usr/bin/env python3

import argparse
import subprocess
import dataclasses
import os
import platform
import tarfile
import tempfile
import urllib.request
import yaml
import zipfile


class PicoInstaller:
    """Installer for Raspberry Pi Pico SDK tools and dependencies.
    
    This class manages the installation of the Pico SDK toolchain, including:
    - OpenOCD (debugging tool)
    - Picotool (binary manipulation tool)
    - Pico SDK tools (elf2uf2, pioasm, etc.)
    - RISC-V toolchain (for RP2350 support)
    
    The installer supports multiple platforms (Linux, Windows, macOS) and architectures
    (x86_64, aarch64/arm64). Tool URLs are loaded from a YAML configuration file that
    organizes downloads by SDK version, OS, and architecture.
    
    Attributes:
        _install_dir (str): Base directory for tool installation (default: ~/.pico-sdk)
        _pico_sdk_available_versions (list): List of supported SDK versions
        _toolchain_available_versions (list): List of supported ARM toolchain versions
        _urls (dict): Loaded YAML configuration containing download URLs
    """

    def __init__(self):
        """Initialize the PicoInstaller with platform detection and configuration loading.
        
        Detects the current platform and architecture, validates compatibility,
        and loads tool download URLs from the YAML configuration file.
        
        Raises:
            ValueError: If the detected architecture is not supported (only x86_64 and aarch64)
            FileNotFoundError: If pico-tools-urls.yaml is not found
            yaml.YAMLError: If the YAML configuration file is malformed
        """
        # Detect operating system
        self._os_type = platform.system().lower()
        if self._os_type == 'darwin':
            self._os_type = 'macos'
        elif self._os_type not in ['linux', 'windows']:
            raise ValueError(f"Unsupported operating system: {self._os_type}. Only Linux, Windows, and macOS are supported.")
        
        # Installation directory for the SDK, Picotool, and toolchain (platform-specific)
        if self._os_type == 'windows':
            self._install_dir = os.path.join(os.environ.get('USERPROFILE', '~'), '.pico-sdk')
        else:
            self._install_dir = "~/.pico-sdk"

        # Define available pico-sdk versions
        self._pico_sdk_available_versions = [
            "2.0.0", "2.1.1", "2.2.0"
        ]

        # Define available toolchain versions
        self._toolchain_available_versions = [
            "12.2.rel1", "13.2.rel1", "14.2.rel1"
        ]

        # Check if the architecture is supported (use platform.machine() for cross-platform compatibility)
        self._arch = platform.machine()
        # Normalize architecture names
        if self._arch in ["AMD64", "x86_64"]:
            self._arch = "x86_64"
        elif self._arch in ["ARM64", "aarch64"]:
            self._arch = "aarch64"
        
        if self._arch not in ["x86_64", "aarch64"]:
            raise ValueError(f"Unsupported architecture: {self._arch}. Only x86_64 and aarch64 are supported.")

        # Load URLs from YAML file
        yaml_path = os.path.join(os.path.dirname(__file__), "pico-tools-urls.yaml")
        with open(yaml_path, 'r') as f:
            self._urls = yaml.safe_load(f)

    def get_url(self, tool: str, sdk_version: str, arch: str, os_type: str = 'linux'):
        """Retrieve the download URL for a specific tool from the YAML configuration.
        
        This method looks up the appropriate download URL based on the tool, SDK version,
        architecture, and operating system. It handles platform-specific naming conventions
        and fallback mechanisms (e.g., macOS universal binaries).
        
        Platform-specific behavior:
        - Linux: Uses architecture directly (x86_64, aarch64)
        - Windows: Maps x86_64 to 'x64' naming convention
        - macOS: Tries architecture-specific URL first, falls back to universal binary
        
        Args:
            tool (str): The tool name. Valid values:
                - 'openocd': On-chip debugger for Pico
                - 'picotool': Tool for interacting with Pico boards
                - 'picosdktools': SDK utilities (elf2uf2, pioasm, etc.)
                - 'riscv-toolchain': RISC-V compiler toolchain for RP2350
            sdk_version (str): SDK version string (e.g., '2.0.0', '2.1.1', '2.2.0')
            arch (str): Target architecture:
                - Linux: 'x86_64' or 'aarch64'
                - Windows: 'x86_64' (internally mapped to 'x64')
                - macOS: 'x86_64' or 'arm64'
            os_type (str, optional): Target OS ('linux', 'windows', or 'macos'). 
                Defaults to 'linux'.
            
        Returns:
            str: The complete download URL for the specified tool archive
            
        Raises:
            ValueError: If the combination of tool, SDK version, architecture, 
                or OS is not found in the configuration
            
        Example:
            >>> installer = PicoInstaller()
            >>> url = installer.get_url('picotool', '2.2.0', 'x86_64', 'linux')
            >>> print(url)
            https://github.com/raspberrypi/pico-sdk-tools/releases/download/...
        """
        try:
            os_data = self._urls['versions'][sdk_version][os_type]
            
            if os_type == 'macos':
                # macOS: try arch-specific first, then fall back to universal
                if arch in os_data and tool in os_data[arch]:
                    return os_data[arch][tool]
                elif 'universal' in os_data and tool in os_data['universal']:
                    return os_data['universal'][tool]
                else:
                    raise KeyError(f"Tool {tool} not found for macOS")
            elif os_type == 'windows':
                # Windows uses 'x64' instead of 'x86_64'
                arch_key = 'x64' if arch == 'x86_64' else arch
                return os_data[arch_key][tool]
            else:
                # Linux uses arch directly
                return os_data[arch][tool]
        except KeyError:
            raise ValueError(f"Unsupported combination: tool={tool}, SDK version={sdk_version}, OS={os_type}, architecture={arch}.")

    def load_and_unpack_url(self, url: str, destination: str):
        """Download and extract an archive from a URL to a destination directory.
        
        This method handles both .tar.gz and .zip archive formats. The archive is
        downloaded to a temporary file, extracted to the destination, and then the
        temporary file is cleaned up.
        
        Supported archive formats:
        - .tar.gz and .tgz (commonly used on Linux)
        - .zip (commonly used on Windows and macOS)
        
        Args:
            url (str): The full URL of the archive to download
            destination (str): Target directory for extraction. The directory will be
                created if it doesn't exist. Supports tilde (~) expansion for home directory.
        
        Raises:
            ValueError: If the URL doesn't end with a supported archive extension
            urllib.error.URLError: If the download fails (network error, 404, etc.)
            zipfile.BadZipFile: If the zip file is corrupted
            tarfile.ReadError: If the tar.gz file is corrupted
            OSError: If file operations fail (permissions, disk space, etc.)
            
        Example:
            >>> installer = PicoInstaller()
            >>> url = "https://example.com/tool.tar.gz"
            >>> installer.load_and_unpack_url(url, "~/.pico-sdk/tools")
        """
        # Ensure the destination directory exists
        os.makedirs(os.path.expanduser(destination), exist_ok=True)

        # Download the file to a temporary location and unpack it
        with urllib.request.urlopen(url) as response, tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(response.read())
            tmp_path = tmp.name
        
        try:
            # Determine file type from URL and unpack accordingly
            if url.endswith('.zip'):
                with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                    zip_ref.extractall(path=os.path.expanduser(destination))
            elif url.endswith('.tar.gz') or url.endswith('.tgz'):
                with tarfile.open(tmp_path, "r:gz") as tar:
                    tar.extractall(path=os.path.expanduser(destination))
            else:
                raise ValueError(f"Unsupported archive format for URL: {url}")
        finally:
            os.remove(tmp_path)

    def install_prerequisites(self):
        """Install system-level prerequisites required for Pico SDK development.
        
        This method installs essential build tools and dependencies needed to compile
        and work with Pico SDK projects. Supports Linux (apt), Windows (checks only),
        and macOS (brew).
        
        Prerequisites installed:
        - git: Version control system
        - cmake: Build system generator
        - Build tools: GCC/MSVC compiler and related build tools
        
        Note:
            - Linux: Requires sudo privileges, uses apt-get
            - Windows: Assumes tools are already installed or installed via other means
            - macOS: Uses Homebrew if available
        
        Raises:
            subprocess.CalledProcessError: If installation commands fail
            PermissionError: If sudo access is denied (Linux/macOS)
        """
        print("Installing prerequisites...")
        
        if self._os_type == 'linux':
            print("Installing Linux prerequisites via apt...")
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "git", "cmake", "build-essential", "curl"], check=True)
        elif self._os_type == 'windows':
            print("Windows detected: Skipping prerequisite installation.")
            print("Please ensure the following are installed:")
            print("  - CMake (https://cmake.org/download/)")
            print("  - Git (https://git-scm.com/download/win)")
            print("  - Build Tools for Visual Studio (https://visualstudio.microsoft.com/downloads/)")
        elif self._os_type == 'macos':
            print("Installing macOS prerequisites via Homebrew...")
            try:
                # Check if brew is available
                subprocess.run(["brew", "--version"], check=True, capture_output=True)
                subprocess.run(["brew", "install", "git", "cmake"], check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("Homebrew not found. Please install:")
                print("  - Homebrew: https://brew.sh")
                print("  - CMake: brew install cmake")
                print("  - Git: brew install git")

    def install_pico_sdk_tools(self, version: str):
        """Download and install all Pico SDK tools for the specified version.
        
        This method installs the complete toolchain including:
        - OpenOCD: For debugging via SWD
        - Picotool: For interacting with UF2 bootloader and Pico boards
        - Pico SDK tools: Including elf2uf2, pioasm, and other utilities
        - RISC-V toolchain: For RP2350 RISC-V core support
        
        After installation, the tools are added to the PATH environment variable
        and verified by running version commands.
        
        Args:
            version (str): SDK version to install (e.g., '2.0.0', '2.1.1', '2.2.0')
        
        Raises:
            ValueError: If the specified version is not available
            RuntimeError: If any tool fails verification after installation
            urllib.error.URLError: If download fails
            OSError: If extraction or file operations fail
        """
        # Check if the version is available
        if version not in self._pico_sdk_tools.keys():
            raise ValueError(f"Pico SDK tools version {version} is not available.")
        
        # Get the download URLs for the specified version
        self.load_and_unpack_url(self._pico_sdk_tools[version]["openocd_url"], os.path.join(self.install_dir, "openocd"))
        self.load_and_unpack_url(self._pico_sdk_tools[version]["picotool_url"], os.path.join(self.install_dir, "picotool"))
        self.load_and_unpack_url(self._pico_sdk_tools[version]["picosdktools_url"], os.path.join(self.install_dir, "picosdktools"))
        self.load_and_unpack_url(self._pico_sdk_tools[version]["riscv_toolchain_url"], os.path.join(self.install_dir, "riscv-toolchain"))

        # Setup environment variables for the installed tools
        os.environ["PATH"] += os.pathsep + os.path.expanduser(os.path.join(self.install_dir, "openocd", "bin"))
        os.environ["PATH"] += os.pathsep + os.path.expanduser(os.path.join(self.install_dir, "picotool", "bin"))
        os.environ["PATH"] += os.pathsep + os.path.expanduser(os.path.join(self.install_dir, "picosdktools", "pioasm"))
        os.environ["PATH"] += os.pathsep + os.path.expanduser(os.path.join(self.install_dir, "riscv-toolchain", "bin"))

        # Check if the tools were installed correctly
        self._check_tool(["openocd", "--version"], "OpenOCD installation failed.")
        self._check_tool(["picotool", "--version"], "Picotool installation failed.")
        self._check_tool(["pioasm", "--version"], "Pico SDK tools installation failed.")
        self._check_tool(["riscv64-unknown-elf-gcc", "--version"], "RISC-V toolchain installation failed.")

    def _check_tool(self, cmd, error_message):
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(error_message) from exc

    def install_toolchain(self, version: str):
        """Install the ARM GCC toolchain for Pico development.
        
        The ARM toolchain provides the compiler and related tools needed to build
        firmware for the ARM Cortex-M cores in Raspberry Pi Pico boards.
        
        Args:
            version (str): Toolchain version (e.g., '12.2.rel1', '13.2.rel1', '14.2.rel1')
        
        Raises:
            ValueError: If the specified version is not available
            RuntimeError: If installation fails
        Note:
            This method is currently incomplete and requires implementation.
        """
        print(f"Installing toolchain version {version}...")
        # Here you would add the actual installation commands, e.g.:
        #subprocess.run(["curl", "-L", f"

    def main(self):
        """Main entry point for the installer command-line interface.
        
        Parses command-line arguments, validates versions, and orchestrates the
        installation of prerequisites, Pico SDK, and toolchain.
        
        Command-line arguments:
            --sdk-version: Pico SDK version to install (default: 2.2.0)
            --toolchain-version: ARM GCC toolchain version (default: 14.2.rel1)
        
        Raises:
            ValueError: If specified versions are invalid or incompatible
            RuntimeError: If installation steps fail
            
        Example:
            $ python install.py --sdk-version 2.2.0 --toolchain-version 14.2.rel1
        """
        # Parse command-line arguments
        parser = argparse.ArgumentParser(
            description=f"Install the Pico SDK and toolchain (detected: {self._os_type}/{self._arch})"
        )
        parser.add_argument("--sdk-version", default="2.2.0", help="Version of the Pico SDK to install (default: 2.2.0)")
        parser.add_argument("--toolchain-version", default="14.2.rel1", help="Version of the toolchain to install (default: 14.2.rel1)")
        args = parser.parse_args()
        
        print(f"Installing for {self._os_type} ({self._arch})...")

        # picotool version is determined by the SDK version

        # Validate Picotool version
        if args.picotool_version not in self._picotool_available_versions:
            raise ValueError('\n'.join([
                f"Picotool version {args.picotool_version} is not available.",
                f"Available versions: {', '.join(self._picotool_available_versions)}"
            ]))

        # Validate Pico SDK version
        if args.sdk_version not in self._pico_sdk_available_versions:
            raise ValueError('\n'.join([
                f"Pico SDK version {args.sdk_version} is not available.",
                f"Available versions: {', '.join(self._pico_sdk_available_versions)}"
            ]))

        # Validate toolchain version
        if args.toolchain_version not in self._toolchain_available_versions:
            raise ValueError('\n'.join([
                f"Toolchain version {args.toolchain_version} is not available.",
                f"Available versions: {', '.join(self._toolchain_available_versions)}"
            ]))

        # Picotool major version must match SDK major version
        sdk_major_version = args.sdk_version.split('.')[0]
        picotool_major_version = args.picotool_version.split('.')[0]
        if sdk_major_version != picotool_major_version:
            raise ValueError(f"Picotool major version {picotool_major_version} does not match Pico SDK major version {sdk_major_version}.")

        # Install prerequisites, Pico SDK, Picotool, and toolchain
        self.install_prerequisites()
        self.install_pico_sdk(args.sdk_version)
        self.install_picotool(args.picotool_version)
        self.install_toolchain(args.toolchain_version)


if __name__ == "__main__":
    try:
        PicoInstaller().main()
        exit(0)
    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)