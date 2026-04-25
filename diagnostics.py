# -*- coding: utf-8 -*-
"""
Módulo diagnostics.py para WinFix v4.0 - Diagnósticos & Fixes Windows.

Funcionalidades:
- 20+ diags/fixes CMD/PS nativo (sem WMIC depreciado Win11).
- Logging DEBUG verbose (console + winfix.log): mostra cmds/output/erros.
- Async Flet (não trava GUI), UTF-8 ç/acentos OK.
- Modular: Funções separadas para commits/pytest.
- Resumo final: Problemas detectados/resolvidos.

Uso:
- await run_full_diagnostics() → Lista Dict para tabela.
- await run_fix('nome') → Bool resolvido.
- export_report(results) → TXT resumo.
"""

import asyncio
import logging
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Logging VERBOSE PT (console + arquivo)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('winfix.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


async def run_cmd(cmd: str, timeout: int = 30) -> Tuple[str, str, int]:
    """
    Executa CMD/PS com timeout/async, captura output, logging verbose.

    Args:
        cmd: Comando (ex: 'powershell Get-Process').
        timeout: Segundos max.

    Returns:
        Tuple[stdout, stderr, return_code].

    Tratamento:
        TimeoutError → "Timeout".
        Exception → "Erro: {e}".
    """
    logger.debug(f"🔄 CMD: '{cmd}' (timeout={timeout}s)")
    try:
        process = await asyncio.create_subprocess_shell(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout)
        code = process.returncode
        logger.debug(f"✅ CMD OK: len(stdout)={len(stdout)}, code={code}")
        return stdout.decode('utf-8', errors='ignore'), stderr.decode('utf-8', errors='ignore'), code
    except asyncio.TimeoutError:
        logger.error(f"⏰ Timeout: {cmd}")
        return "Timeout", "", 1
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        return f"Erro: {e}", "", 1

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
