# Pico Build Action

A GitHub Action for building Raspberry Pi Pico projects with pico-sdk and picotool.

## Features

- ✅ Cross-platform support (Ubuntu & Windows)
- ✅ Configurable pico-sdk version
- ✅ Configurable picotool version
- ✅ Configurable ARM GCC toolchain version
- ✅ Custom CMake arguments
- ✅ Flexible source and build directories

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `pico-sdk-version` | Version/tag/branch of pico-sdk to use | No | `master` |
| `picotool-version` | Version/tag/branch of picotool to use | No | `master` || `toolchain-version` | ARM GCC toolchain version to use | No | `13.2.rel1` || `cmake-args` | Additional arguments to pass to cmake configure | No | `''` |
| `source-dir` | Source directory containing CMakeLists.txt | No | `.` |
| `build-dir` | Build output directory (relative to source-dir if not absolute) | No | `build` |

## Outputs

| Output | Description |
|--------|-------------|
| `pico-sdk-path` | Path to the installed pico-sdk |
| `picotool-path` | Path to the installed picotool |
| `build-path` | Path to the build directory |

## Usage

### Basic Usage

```yaml
name: Build Pico Project

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Pico Project
        uses: kolod/action-pico-build@v1
```

### Multi-Platform Build

```yaml
name: Build Pico Project

on: [push, pull_request]

jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Pico Project
        uses: your-username/action-pico-build@v1
        with:
          pico-sdk-version: '1.5.1'
          picotool-version: '1.1.2'
```

### With Custom Toolchain Version

```yaml
name: Build Pico Project

on: [push, pull_request]

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Pico Project
        uses: your-username/action-pico-build@v1
        with:
          toolchain-version: '12.3.rel1'
```

### With Custom CMake Arguments

```yaml
name: Build Pico Project

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Pico Project
        uses: your-username/action-pico-build@v1
        with:
          cmake-args: '-DPICO_BOARD=pico_w -DWIFI_SSID="MyNetwork" -DWIFI_PASSWORD="secret"'
```

### Custom Source and Build Directories

```yaml
name: Build Pico Project

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Pico Project
        uses: your-username/action-pico-build@v1
        with:
          source-dir: 'firmware'
          build-dir: 'output'
```

### Using Outputs

```yaml
name: Build and Upload

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Pico Project
        id: build
        uses: your-username/action-pico-build@v1
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: firmware
          path: ${{ steps.build.outputs.build-path }}/*.uf2
```

## Supported SDK Versions

You can use any valid git tag, branch, or commit SHA for `pico-sdk-version` and `picotool-version`. Common versions include:

- `master` - Latest development version
- `2.0.0`, `1.5.1`, `1.5.0`, `1.4.0` - Stable releases
- `develop` - Development branch

## Version Compatibility

### Pico SDK & Picotool

It's important to use compatible versions of pico-sdk and picotool together. Here are recommended combinations:

| Pico SDK Version | Compatible Picotool Version | Notes |
|------------------|----------------------------|-------|
| `2.0.0` | `2.0.0` | Recommended stable combination |
| `1.5.1` | `1.1.2` | Last SDK 1.x release |
| `master` | `master` | Latest development (Linux only on Windows) |

**Important notes:**
- Newer SDK versions (2.1.0+) may have API changes (e.g., mbedtls) that are incompatible with older picotool releases
- On Windows, only release versions of picotool are supported (prebuilt binaries). Use `master` branch only on Linux
- When in doubt, use matching version numbers (e.g., SDK 2.0.0 with Picotool 2.0.0)

### ARM GCC Toolchain

Common toolchain versions:

| Toolchain Version | Release Date | Notes |
|-------------------|--------------|-------|
| `14.2.rel1` | 2024 | Latest, supports all features |
| `13.2.rel1` | 2023 | Default, well-tested |
| `12.3.rel1` | 2023 | Older, stable |

All toolchain versions work with all SDK versions. Use the latest for best performance and features.

## Platform-Specific Notes

### Windows
- Picotool is installed from prebuilt binaries (release versions only)
- GNU Make is automatically installed via Chocolatey
- Builds use Unix Makefiles generator with ARM GCC

### Linux
- Picotool is built from source (supports any version/branch)
- All dependencies installed via apt-get and direct downloads

## License

MIT
