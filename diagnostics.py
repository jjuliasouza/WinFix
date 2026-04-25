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
# cmd, needs_admin, timeout_segundos, nota (exibe no output)
FIXES = {
    "DNS Flush":   ("ipconfig /flushdns",                         False, 30,   ""),
    "Winsock":     ("netsh winsock reset",                        True,  30,   "Requer reboot para ter efeito."),
    "IP Reset":    ("netsh int ip reset",                         True,  30,   "Requer reboot para ter efeito."),
    "Firewall":    ("netsh advfirewall reset",                    True,  30,   ""),
    "DNS Service": ("net stop Dnscache && net start Dnscache",    True,  30,   ""),
    "GPUpdate":    ("gpupdate /force",                            False, 60,   ""),
    "CHKDSK":      ("chkdsk C: /scan",                           True,  120,  "Usa /scan (online, sem reboot)."),
    "SFC":         ("sfc /scannow",                               True,  1800, "Pode levar até 30 min."),
    "DISM":        ("dism /online /cleanup-image /restorehealth", True,  1800, "Pode levar até 30 min."),
    "IP Renew":    ("ipconfig /release && ipconfig /renew",       True,  60,   "Derruba a rede brevemente."),
}


async def run_fix(name: Optional[str] = None, on_progress=None) -> Tuple[bool, str]:
    """
    Fix individual ou completo.
    on_progress(atual, total, nome) chamado antes de cada fix no modo completo.
    Retorna (sucesso, output_texto).
    """
    if name and name in FIXES:
        cmd, _, timeout, nota = FIXES[name]
        stdout, stderr, code = await run_cmd(cmd, timeout)
        output = (stdout + stderr).strip() or "(sem output)"
        if nota:
            output = f"[NOTA] {nota}\n\n{output}"
        resolved = code == 0
        logger.info(f"Fix '{name}': {'✅ Resolvido' if resolved else '⚠️ Falhou'}")
        return resolved, output

    total = len(FIXES)
    lines = []
    all_ok = True
    for i, (n, (cmd, _, timeout, nota)) in enumerate(FIXES.items(), 1):
        if on_progress:
            await on_progress(i, total, n)
        stdout, stderr, code = await run_cmd(cmd, timeout)
        ok = code == 0
        if not ok:
            all_ok = False
        saida = (stdout + stderr).strip()[:300]
        prefix = f"[{'OK  ' if ok else 'FAIL'}] {i:02d}/{total} {n}"
        if nota:
            prefix += f" ({nota})"
        lines.append(f"{prefix}\n{saida}\n")
        logger.info(f"Fix '{n}': {'OK' if ok else 'Falhou'}")
    return all_ok, "\n".join(lines)


def export_report(results: List[Dict[str, str]], filename: str = "winfix_report.txt") -> None:
    """
    Exporta relatório TXT formatado com resultado dos diagnósticos.

    Args:
        results: Lista de dicts retornada por run_full_diagnostics().
        filename: Caminho do arquivo de saída.
    """
    from datetime import datetime
    problemas = sum(1 for r in results if "🔴" in r["status"])
    ok = len(results) - problemas
    linha = "=" * 70
    sublinha = "-" * 70
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"{linha}\n")
        f.write(f"  WINFIX v4.0 - RELATÓRIO DE DIAGNÓSTICO\n")
        f.write(f"{linha}\n")
        f.write(f"  Data/Hora : {agora}\n")
        f.write(f"  Total     : {len(results)} testes\n")
        f.write(f"  OK        : {ok}\n")
        f.write(f"  Problemas : {problemas}\n")
        f.write(f"{linha}\n\n")
        for i, r in enumerate(results, 1):
            status_label = "[ OK ]" if "🟢" in r["status"] else "[FAIL]"
            f.write(f"{i:02d}. {status_label}  {r['name']}\n")
            f.write(f"{sublinha}\n")
            detalhes = r["details"].strip()
            for linha_det in detalhes.splitlines():
                f.write(f"    {linha_det}\n")
            f.write("\n")
        f.write(f"{linha}\n")
        f.write(f"  FIM DO RELATÓRIO\n")
        f.write(f"{linha}\n")
    logger.info(f"📄 Relatório salvo: {filename}")
