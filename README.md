# Pico Build Action

GitHub Action to build Raspberry Pi Pico projects using the Pico SDK.

## Usage

Reference the action from its repo: `kolod/action-pico-build`. For Pico SDK 2.2.0 use the `v2.2.0` tag:

```yaml
jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]

    steps:
      - uses: actions/checkout@v4

      - name: Build Pico project
        uses: kolod/action-pico-build@v2.2.0
        with:
          source-dir: ${{ github.workspace }}/test-project
          build-dir: build
          cmake-args: ""
```

After the build, UF2 and ELF files are uploaded as artifacts named `pico-binaries-${{ runner.os }}`.

## Inputs

- `install-path` (default: `${{ github.workspace }}/../../../.pico-sdk`)
  - Where the SDK and toolchains are installed.
- `source-dir` (default: `${{ github.workspace }}`)
  - Directory containing `CMakeLists.txt`.
- `build-dir` (default: `build`)
  - Build output directory.
- `cmake-args` (default: empty)
  - Extra flags passed to CMake configure step.

## What the action does

- Creates install directory
- Installs prerequisites
  - Linux: `cmake`, `build-essential`
  - Windows: `ninja` via Chocolatey
  - macOS: uses system toolchain installers
- Clones Pico SDK (branch 2.2.0) and initializes submodules; exports `PICO_SDK_PATH`
- Installs Pico SDK tools and toolchains per-OS
- Configures and builds with CMake
  - Linux/macOS: default generator
  - Windows: Ninja generator
- Collects `.uf2` and `.elf` build outputs into `${{ github.workspace }}/artifacts` and uploads them
