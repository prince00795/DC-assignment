# PowerShell Build Script for ITT 036 Digital Communications C++ Suite
Param(
    [string]$Target = "all"
)

$ErrorActionPreference = "Stop"

$CXX = "g++"
$CXXFLAGS = "-std=c++20", "-O2", "-Wall", "-Wextra", "-Iinclude"

$COMMON_SRCS = @(
    "src/algorithms/palindrome.cpp",
    "src/generator/data_generator.cpp",
    "src/line_coding/base.cpp",
    "src/line_coding/encoders.cpp",
    "src/scrambling/b8zs.cpp",
    "src/scrambling/hdb3.cpp",
    "src/decoder/signal_decoder.cpp",
    "src/analog/continuous_signal.cpp",
    "src/analog/sampling.cpp",
    "src/analog/quantization.cpp",
    "src/analog/delta_modulation.cpp",
    "src/analog/plotter.cpp",
    "src/pipeline/bridge.cpp"
)

if (!(Test-Path "bin")) {
    New-Item -ItemType Directory -Path "bin" | Out-Null
}

if ($Target -eq "all" -or $Target -eq "app") {
    Write-Host "[Building] Compiling bin/dc_system.exe..." -ForegroundColor Cyan
    $app_srcs = $COMMON_SRCS + @("src/cli/menu.cpp", "src/cli/report.cpp", "src/main.cpp")
    & $CXX $CXXFLAGS $app_srcs -o "bin/dc_system.exe"
    Write-Host "[Success] bin/dc_system.exe built successfully." -ForegroundColor Green
}

if ($Target -eq "all" -or $Target -eq "test") {
    Write-Host "[Building] Compiling bin/run_tests.exe..." -ForegroundColor Cyan
    $test_srcs = $COMMON_SRCS + @("tests/test_runner.cpp")
    & $CXX $CXXFLAGS $test_srcs -o "bin/run_tests.exe"
    Write-Host "[Success] bin/run_tests.exe built successfully." -ForegroundColor Green
}

if ($Target -eq "run-test") {
    & ".\bin\run_tests.exe"
}
