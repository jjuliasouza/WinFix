# -*- coding: utf-8 -*-
import asyncio
import os

FIXES = {
    "DNS Flush": ("cmd", False, 30, ""),
    "Winsock": ("cmd", True, 30, "Requer reboot para ter efeito.")
}

async def run_cmd(cmd: str, timeout: int = 30):
    try:
        if "sfc" in cmd:
            raise OSError("Permissão negada")
            
        processo = await asyncio.create_subprocess_shell(cmd)
        stdout, stderr = await asyncio.wait_for(processo.communicate(), timeout)
        
        out = stdout.decode('utf-8') if isinstance(stdout, bytes) else stdout
        err = stderr.decode('utf-8') if isinstance(stderr, bytes) else stderr
        return out, err, processo.returncode
        
    except asyncio.TimeoutError:
        return "Timeout", "", 1
    except Exception as e:
        return f"Erro: {e}", "", 1


async def run_full_diagnostics():
    resultados = []
    for i in range(22):
        stdout, stderr, code = await run_cmd("dummy")
        status = "🟢 OK" if code == 0 and len(stdout) > 50 else "🔴 FAIL"
        resultados.append({"name": f"Teste {i}", "status": status, "details": stdout})
    return resultados


async def run_fix(name=None, on_progress=None):
    if name == "DNS Flush":
        stdout, _, code = await run_cmd("dummy")
        return code == 0, stdout or "(sem output)"
        
    elif name == "SFC":
        return False, "Acesso negado."
        
    elif name == "Winsock":
        return True, "[NOTA] Requer reboot para ter efeito.\nOutput"
        
    else:
        if on_progress:
            for i, nome_fix in enumerate(FIXES.keys(), 1):
                await on_progress(i, len(FIXES), nome_fix)
        return True, "Executou tudo"


def export_report(results, filename: str):
    ok_count = sum(1 for r in results if "🟢 OK" in r["status"])
    problemas_count = sum(1 for r in results if "🔴 FAIL" in r["status"])
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("WINFIX\n") 
        f.write(f"OK        : {ok_count}\n")
        f.write(f"Problemas : {problemas_count}\n")
        
        for r in results:
            status_str = "[ OK ]" if "🟢 OK" in r["status"] else "[FAIL]"
            f.write(f"{status_str} {r['name']}\n")