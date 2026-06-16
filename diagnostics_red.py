# -*- coding: utf-8 -*-
import asyncio

# Dicionário stub para o teste conseguir importar
FIXES = {
    "DNS Flush": ("cmd", False, 30, ""),
    "Winsock": ("cmd", True, 30, "Requer reboot para ter efeito.")
}

async def run_cmd(cmd: str, timeout: int = 30):
    return None, None, None

async def run_full_diagnostics():
    return [{"name": "erro_forçado", "status": "indefinido", "details": ""}]

async def run_fix(name=None, on_progress=None):
    return None, None

def export_report(results, filename: str):
    pass