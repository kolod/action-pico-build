#!/usr/bin/env python3

import argparse
import subprocess
import dataclasses
import os
import tarfile
import tempfile
import urllib.request


class PicoInstaller:

    def __init__(self):
        # Installation directory for the SDK, Picotool, and toolchain
        self.install_dir = "~/.pico-sdk"

        # Define available pico-sdk versions
        self._pico_sdk_available_versions = [
            "2.0.0", "2.1.1", "2.2.0"
        ]

        # Define available toolchain versions
        self._toolchain_available_versions = [
            "12.2.rel1", "13.2.rel1", "14.2.rel1"
        ]

        # Check if the architecture is supported
        arch = os.uname().machine
        if arch not in ["x86_64", "aarch64"]:
            raise ValueError(f"Unsupported architecture: {arch}. Only x86_64 and aarch64 are supported.")

        # Define pico-sdk-tools versions corresponding to pico-sdk versions
        self._pico_sdk_tools = {
            "2.0.0": {
                "openocd_url": f"https://github.com/raspberrypi/pico-sdk-tools/releases/download/v2.0.0-5/openocd-0.12.0+dev-{arch}-lin.tar.gz",
                "picotool_url": f"https://github.com/raspberrypi/pico-sdk-tools/releases/download/v2.0.0-5/picotool-2.0.0-{arch}-lin.tar.gz",
                "picosdktools_url": f"https://github.com/raspberrypi/pico-sdk-tools/releases/download/v2.0.0-5/pico-sdk-tools-2.0.0-{arch}-lin.tar.gz",
                "riscv_toolchain_url": f"https://github.com/raspberrypi/pico-sdk-tools/releases/download/v2.0.0-5/riscv-toolchain-14-{arch}-lin.tar.gz"
            },
            "2.1.1": {
                "openocd_url": f"https://github.com/raspberrypi/pico-sdk-tools/releases/download/v2.1.1-3/openocd-0.12.0+dev-{arch}-lin.tar.gz",
                "picotool_url": f"https://github.com/raspberrypi/pico-sdk-tools/releases/download/v2.1.1-3/picotool-2.1.1-{arch}-lin.tar.gz",
                "picosdktools_url": f"https://github.com/raspberrypi/pico-sdk-tools/releases/download/v2.1.1-3/pico-sdk-tools-2.1.1-{arch}-lin.tar.gz",
                "riscv_toolchain_url": f"https://github.com/raspberrypi/pico-sdk-tools/releases/download/v2.1.1-3/riscv-toolchain-15-{arch}-lin.tar.gz"
            },
            "2.2.2": {
                "openocd_url": f"https://github.com/raspberrypi/pico-sdk-tools/releases/download/v2.2.0-3/openocd-0.12.0+dev-{arch}-lin.tar.gz",
                "picotool_url": f"https://github.com/raspberrypi/pico-sdk-tools/releases/download/v2.2.0-3/picotool-2.2.0-a4-{arch}-lin.tar.gz",
                "picosdktools_url": f"https://github.com/raspberrypi/pico-sdk-tools/releases/download/v2.2.0-3/pico-sdk-tools-2.2.0-{arch}-lin.tar.gz",
                "riscv_toolchain_url": f"https://github.com/raspberrypi/pico-sdk-tools/releases/download/v2.2.0-3/riscv-toolchain-15-{arch}-lin.tar.gz"
            }
        }

    def load_and_unpack_url(self, url: str, destination: str):
        """Download and unpack a tar.gz file from the specified URL to the destination directory."""
        # Ensure the destination directory exists
        os.makedirs(os.path.expanduser(destination), exist_ok=True)

        # Download the file to a temporary location and unpack it
        with urllib.request.urlopen(url) as response, tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(response.read())
            tmp_path = tmp.name
        try:
            with tarfile.open(tmp_path, "r:gz") as tar:
            tar.extractall(path=os.path.expanduser(destination))
        finally:
            os.remove(tmp_path)


    def install_prerequisites(self):
        """Install any prerequisites needed for the Pico SDK and toolchain."""
        print("Installing prerequisites...")
        # Here you would add the actual installation commands, e.g.:
        subprocess.run(["sudo", "apt-get", "update"])
        subprocess.run(["sudo", "apt-get", "install", "-y", "git", "cmake", "build-essential", "curl"])

    def install_pico_sdk_tools(self, version: str):
        """Install the Pico SDK tools of the specified version."""
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
        try:
            subprocess.run(["openocd", "--version"], check=True)        
        except subprocess.CalledProcessError:
            raise RuntimeError("OpenOCD installation failed.")

        try:
            subprocess.run(["picotool", "--version"], check=True)
        except subprocess.CalledProcessError:
            raise RuntimeError("Picotool installation failed.")

        try:
            subprocess.run(["pioasm", "--version"], check=True)
        except subprocess.CalledProcessError:
            raise RuntimeError("Pico SDK tools installation failed.")

    def install_toolchain(self, version: str):
        """Install the toolchain of the specified version."""
        print(f"Installing toolchain version {version}...")
        # Here you would add the actual installation commands, e.g.:
        subprocess.run(["curl", "-L", f"

    def main(self):
        # Parse command-line arguments
        parser = argparse.ArgumentParser(description="Install the Pico SDK and toolchain on Linux.")
        parser.add_argument("--sdk-version", default="2.2.0", help="Version of the Pico SDK to install (default: 2.2.0)")
        parser.add_argument("--toolchain-version", default="14.2.rel1", help="Version of the toolchain to install (default: 14.2.rel1)")
        args = parser.parse_args()

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

        # Handle special cases for SDK versions that has bagged picotool versions
        if args.sdk_version == "2.1.0":
            args.sdk_version = "2.1.0-correct-picotool"
        elif args.sdk_version == "2.1.1":
            args.sdk_version = "2.1.1-correct-picotool"

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