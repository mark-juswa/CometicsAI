# Read-only inventory. Selection and policy live in mobile_launch.py for testing.
$ErrorActionPreference = 'Stop'
@{
    routes = @(Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' |
        Select-Object InterfaceIndex, InterfaceAlias, NextHop, RouteMetric)
    interfaces = @(Get-NetIPInterface -AddressFamily IPv4 |
        Select-Object InterfaceIndex, InterfaceMetric, @{n='State';e={$_.ConnectionState.ToString()}})
    adapters = @(Get-NetAdapter |
        Select-Object ifIndex, Name, HardwareInterface, Virtual, @{n='State';e={$_.Status.ToString()}})
    addresses = @(Get-NetIPAddress -AddressFamily IPv4 |
        Select-Object InterfaceIndex, IPAddress, SkipAsSource, @{n='State';e={$_.AddressState.ToString()}})
    profiles = @(Get-NetConnectionProfile |
        Select-Object InterfaceIndex, @{n='Category';e={$_.NetworkCategory.ToString()}})
} | ConvertTo-Json -Depth 4 -Compress
