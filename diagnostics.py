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
