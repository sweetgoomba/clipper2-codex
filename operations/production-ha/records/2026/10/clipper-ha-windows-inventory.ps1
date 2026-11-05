# Read-only hardware inventory. Paste into Windows PowerShell 5.1 or newer.
# Does not install software, change firmware, touch watchdog devices, or reboot.
# Intentionally omits serial numbers, UUIDs, product keys, IP/MAC addresses.
$clipperHaInventory = [ordered]@{}
$clipperHaInventory.PowerShellVersion = $PSVersionTable.PSVersion.ToString()
$clipperHaInventory.Computer = Get-CimInstance Win32_ComputerSystem |
    Select-Object Manufacturer, Model, @{Name='RAM_GB';Expression={[math]::Round($_.TotalPhysicalMemory / 1GB, 1)}}
$clipperHaInventory.Mainboard = Get-CimInstance Win32_BaseBoard |
    Select-Object Manufacturer, Product, Version
$clipperHaInventory.BIOS = Get-CimInstance Win32_BIOS |
    Select-Object Manufacturer, SMBIOSBIOSVersion, ReleaseDate
$clipperHaInventory.CPU = @(Get-CimInstance Win32_Processor |
    Select-Object Name, AddressWidth, NumberOfCores, NumberOfLogicalProcessors)
$clipperHaInventory.Disks = @(Get-CimInstance Win32_DiskDrive |
    Select-Object Model, InterfaceType, MediaType, @{Name='Size_GB';Expression={[math]::Round($_.Size / 1GB, 1)}})
$clipperHaInventory.Ethernet = @(Get-CimInstance Win32_NetworkAdapter |
    Where-Object { $_.PhysicalAdapter -eq $true } |
    Select-Object Name, Manufacturer, NetEnabled)
$clipperHaInventory.WatchdogNameHints = @(Get-CimInstance Win32_PnPEntity |
    Where-Object { $_.Name -match '(?i)watchdog|watch dog|\bWDT\b' } |
    Select-Object Name, Manufacturer, Status)
$clipperHaInventory.Note = 'Watchdog name matches are hints only. Empty output does not prove absence. This script does not test Linux watchdog support or hardware reset.'
$clipperHaInventory | ConvertTo-Json -Depth 5
