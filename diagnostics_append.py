
async def run_full_diagnostics() -> List[Dict[str, str]]:
    """
    20+ diags PS/CMD (sem WMIC): rede/SO/disco/memória/processos.

    Returns:
        List[Dict{name, status 🟢/🔴, details}].
    """
    logger.info("🚀 Diags completos iniciados")
    results = []
    cmds = [
        ("Ping Google",      "ping -n 4 google.com"),
        ("Ipconfig",         "ipconfig /all"),
        ("Tracert",          "tracert -h 4 google.com"),
        ("NSLookup",         "nslookup google.com"),
        ("Disco Livre",      "powershell Get-PSDrive -PSProvider FileSystem | Select DeviceID,Free,Used"),
        ("Memória",          "powershell Get-CimInstance Win32_OperatingSystem | Select FreePhysicalMemory,TotalVisibleMemorySize"),
        ("Processos Top 20", "powershell Get-Process | Sort CPU -Desc | Select -First 20 | Format-Table Name,Id,CPU,WorkingSet"),
        ("Interfaces Rede",  "netsh interface show interface"),
        ("SFC Status",       "sfc /verifyonly"),
        ("DISM Health",      "dism /online /cleanup-image /checkhealth"),
        ("Netstat",          "netstat -an | findstr LISTENING"),
        ("Drivers",          "pnputil /enum-drivers"),
        ("SystemInfo",       "systeminfo | findstr OS"),
        ("GPUpdate",         "gpupdate /force"),
        ("CHKDSK C:",        "chkdsk C: /scan"),
        ("Eventos Erros",    "powershell Get-EventLog System -EntryType Error -Newest 5 | Format-Table"),
        ("Serviços",         "sc query | findstr RUNNING"),
        ("Firewall",         "netsh advfirewall show allprofiles"),
        ("Rede Adaptadores", "netsh interface ip show config"),
        ("Rota",             "route print"),
        ("USB Devices",      "powershell Get-PnpDevice | Where-Object {$_.FriendlyName -like '*usb*'} | Select FriendlyName"),
        ("WiFi",             "netsh wlan show profiles"),
    ]
    for name, cmd in cmds:
        stdout, stderr, code = await run_cmd(cmd)
        output = stdout + stderr
        status = "🟢 OK" if code == 0 and len(output) > 50 else "🔴 FAIL"
        results.append({"name": name, "status": status, "details": output[:500]})
        logger.debug(f"{name}: {status}")
    logger.info(f"✅ Diags OK: {len(results)} itens")
    return results
