# -*- coding: utf-8 -*-
"""
Testes unitários para WinFix v4.0.
Cobre: run_cmd, run_full_diagnostics, run_fix, export_report, load_config, is_admin,
       relaunch_as_admin, FIXES dict (integridade e regras de negócio).
"""

import asyncio
import json
import os
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock, mock_open, call


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(coro):
    """Roda coroutine de forma síncrona nos testes."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ===========================================================================
# config.py — load_config
# ===========================================================================

class TestLoadConfig:
    def test_arquivo_valido_retorna_dados(self, tmp_path):
        cfg = {"version": "3.0", "last_run": "2024-01-01", "logs": ["a"]}
        f = tmp_path / "winfix.json"
        f.write_text(json.dumps(cfg))
        with patch("config.CONFIG_FILE", str(f)):
            from config import load_config
            result = load_config()
        assert result["version"] == "3.0"
        assert result["last_run"] == "2024-01-01"

    def test_arquivo_json_corrompido_retorna_padrao(self, tmp_path):
        f = tmp_path / "winfix.json"
        f.write_text("isso nao e json{{{")
        with patch("config.CONFIG_FILE", str(f)):
            from config import load_config
            result = load_config()
        assert result["version"] == "2.0"
        assert result["last_run"] == ""

    def test_arquivo_inexistente_retorna_padrao(self, tmp_path):
        caminho_falso = str(tmp_path / "nao_existe.json")
        with patch("config.CONFIG_FILE", caminho_falso):
            from config import load_config
            result = load_config()
        assert result["version"] == "2.0"
        assert result["last_run"] == ""
        assert result["logs"] == []


# ===========================================================================
# auth.py — is_admin
# ===========================================================================

class TestIsAdmin:
    def test_retorna_true_quando_admin(self):
        with patch("ctypes.windll", create=True) as mock_windll:
            mock_windll.shell32.IsUserAnAdmin.return_value = 1
            from auth import is_admin
            assert is_admin() is True

    def test_retorna_false_quando_nao_admin(self):
        with patch("ctypes.windll", create=True) as mock_windll:
            mock_windll.shell32.IsUserAnAdmin.return_value = 0
            from auth import is_admin
            assert is_admin() is False

    def test_retorna_false_em_excecao(self):
        with patch("ctypes.windll", create=True) as mock_windll:
            mock_windll.shell32.IsUserAnAdmin.side_effect = Exception("sem ctypes")
            from auth import is_admin
            assert is_admin() is False


# ===========================================================================
# diagnostics.py — run_cmd
# ===========================================================================

def _mock_process(stdout: bytes, stderr: bytes, returncode: int):
    """Cria mock de asyncio.subprocess.Process."""
    proc = MagicMock()
    proc.returncode = returncode
    proc.communicate = AsyncMock(return_value=(stdout, stderr))
    return proc


class TestRunCmd:
    def test_sucesso_retorna_stdout_stderr_codigo(self):
        proc = _mock_process(b"saida ok", b"", 0)
        with patch("asyncio.create_subprocess_shell", AsyncMock(return_value=proc)):
            from diagnostics import run_cmd
            stdout, stderr, code = run(run_cmd("ping google.com"))
        assert stdout == "saida ok"
        assert stderr == ""
        assert code == 0

    def test_timeout_retorna_tuple_de_erro(self):
        async def raise_timeout(*a, **kw):
            raise asyncio.TimeoutError()

        proc = MagicMock()
        proc.communicate = raise_timeout

        with patch("asyncio.create_subprocess_shell", AsyncMock(return_value=proc)):
            with patch("asyncio.wait_for", raise_timeout):
                from diagnostics import run_cmd
                stdout, stderr, code = run(run_cmd("lento", timeout=1))
        assert stdout == "Timeout"
        assert code == 1

    def test_excecao_generica_retorna_mensagem_de_erro(self):
        with patch("asyncio.create_subprocess_shell", AsyncMock(side_effect=OSError("falhou"))):
            from diagnostics import run_cmd
            stdout, stderr, code = run(run_cmd("inexistente"))
        assert "Erro:" in stdout
        assert code == 1

    def test_stderr_unicode_decodificado(self):
        proc = _mock_process(b"", "erro ç".encode("utf-8"), 1)
        with patch("asyncio.create_subprocess_shell", AsyncMock(return_value=proc)):
            from diagnostics import run_cmd
            _, stderr, code = run(run_cmd("cmd"))
        assert "ç" in stderr
        assert code == 1


# ===========================================================================
# diagnostics.py — run_full_diagnostics
# ===========================================================================

class TestRunFullDiagnostics:
    def _patch_run_cmd(self, stdout="output longo suficiente para passar no teste aqui", stderr="", code=0):
        from diagnostics import run_cmd as _original
        return patch(
            "diagnostics.run_cmd",
            AsyncMock(return_value=(stdout, stderr, code))
        )

    def test_retorna_lista_com_todos_os_diags(self):
        with self._patch_run_cmd():
            from diagnostics import run_full_diagnostics
            results = run(run_full_diagnostics())
        assert len(results) == 22
        assert all("name" in r and "status" in r and "details" in r for r in results)

    def test_status_ok_quando_code_zero_e_output_longo(self):
        with self._patch_run_cmd(stdout="a" * 100, code=0):
            from diagnostics import run_full_diagnostics
            results = run(run_full_diagnostics())
        assert all(r["status"] == "🟢 OK" for r in results)

    def test_status_fail_quando_code_diferente_de_zero(self):
        with self._patch_run_cmd(stdout="a" * 100, code=1):
            from diagnostics import run_full_diagnostics
            results = run(run_full_diagnostics())
        assert all(r["status"] == "🔴 FAIL" for r in results)

    def test_status_fail_quando_output_curto_demais(self):
        with self._patch_run_cmd(stdout="curto", code=0):
            from diagnostics import run_full_diagnostics
            results = run(run_full_diagnostics())
        assert all(r["status"] == "🔴 FAIL" for r in results)

    def test_details_truncados_em_500_chars(self):
        saida_longa = "x" * 1000
        with self._patch_run_cmd(stdout=saida_longa, code=0):
            from diagnostics import run_full_diagnostics
            results = run(run_full_diagnostics())
        assert all(len(r["details"]) <= 500 for r in results)


# ===========================================================================
# diagnostics.py — run_fix
# ===========================================================================

class TestRunFix:
    def _patch(self, stdout="ok", stderr="", code=0):
        return patch("diagnostics.run_cmd", AsyncMock(return_value=(stdout, stderr, code)))

    def test_fix_individual_sucesso(self):
        with self._patch(code=0):
            from diagnostics import run_fix
            ok, output = run(run_fix("DNS Flush"))
        assert ok is True
        assert isinstance(output, str)

    def test_fix_individual_falha(self):
        with self._patch(code=1):
            from diagnostics import run_fix
            ok, output = run(run_fix("DNS Flush"))
        assert ok is False

    def test_fix_individual_com_nota_incluida_no_output(self):
        with self._patch(code=0):
            from diagnostics import run_fix
            _, output = run(run_fix("Winsock"))
        assert "[NOTA]" in output
        assert "reboot" in output.lower()

    def test_fix_sem_output_retorna_sem_output(self):
        with self._patch(stdout="", stderr="", code=0):
            from diagnostics import run_fix
            _, output = run(run_fix("DNS Flush"))
        assert "(sem output)" in output

    def test_fix_nome_invalido_executa_todos(self):
        """Nome não encontrado no dict cai no modo 'executar todos'."""
        with self._patch(code=0):
            from diagnostics import run_fix, FIXES
            ok, output = run(run_fix("NaoExiste"))
        # Deve ter executado todos os fixes
        from diagnostics import FIXES
        assert str(len(FIXES)).zfill(2) in output

    def test_fix_completo_sem_nome_executa_todos(self):
        with self._patch(code=0):
            from diagnostics import run_fix, FIXES
            ok, output = run(run_fix())
        assert ok is True

    def test_fix_completo_falha_parcial_retorna_false(self):
        """Se qualquer fix falhar, all_ok deve ser False."""
        resultados = iter([(("ok", "", 0)) if i % 2 == 0 else (("err", "", 1)) for i in range(20)])

        async def run_cmd_alternado(cmd, timeout=30):
            return next(resultados)

        with patch("diagnostics.run_cmd", run_cmd_alternado):
            from diagnostics import run_fix
            ok, _ = run(run_fix())
        assert ok is False

    def test_fix_completo_chama_on_progress(self):
        progress_calls = []

        async def mock_progress(atual, total, nome):
            progress_calls.append((atual, total, nome))

        with self._patch(code=0):
            from diagnostics import run_fix, FIXES
            run(run_fix(on_progress=mock_progress))

        assert len(progress_calls) == len(FIXES)
        assert progress_calls[0][0] == 1
        assert progress_calls[-1][0] == len(FIXES)


# ===========================================================================
# diagnostics.py — export_report
# ===========================================================================

class TestExportReport:
    def _resultados(self):
        return [
            {"name": "Ping", "status": "🟢 OK", "details": "Reply from 8.8.8.8"},
            {"name": "Disco", "status": "🔴 FAIL", "details": "Sem espaço"},
            {"name": "Memória", "status": "🟢 OK", "details": "4GB livre"},
        ]

    def test_arquivo_criado_com_conteudo(self, tmp_path):
        arquivo = str(tmp_path / "relatorio.txt")
        from diagnostics import export_report
        export_report(self._resultados(), filename=arquivo)
        assert os.path.exists(arquivo)
        conteudo = open(arquivo, encoding="utf-8").read()
        assert "WINFIX" in conteudo

    def test_contagem_ok_e_problemas(self, tmp_path):
        arquivo = str(tmp_path / "relatorio.txt")
        from diagnostics import export_report
        export_report(self._resultados(), filename=arquivo)
        conteudo = open(arquivo, encoding="utf-8").read()
        assert "OK        : 2" in conteudo
        assert "Problemas : 1" in conteudo

    def test_nomes_e_status_presentes(self, tmp_path):
        arquivo = str(tmp_path / "relatorio.txt")
        from diagnostics import export_report
        export_report(self._resultados(), filename=arquivo)
        conteudo = open(arquivo, encoding="utf-8").read()
        assert "Ping" in conteudo
        assert "Disco" in conteudo
        assert "[ OK ]" in conteudo
        assert "[FAIL]" in conteudo

    def test_detalhes_incluidos(self, tmp_path):
        arquivo = str(tmp_path / "relatorio.txt")
        from diagnostics import export_report
        export_report(self._resultados(), filename=arquivo)
        conteudo = open(arquivo, encoding="utf-8").read()
        assert "Reply from 8.8.8.8" in conteudo
        assert "Sem espaço" in conteudo

    def test_resultados_vazios_nao_gera_erro(self, tmp_path):
        arquivo = str(tmp_path / "vazio.txt")
        from diagnostics import export_report
        export_report([], filename=arquivo)
        conteudo = open(arquivo, encoding="utf-8").read()
        assert "Total     : 0" in conteudo

    def test_encoding_utf8_com_acentos(self, tmp_path):
        resultados = [{"name": "Diagnóstico", "status": "🟢 OK", "details": "tudo certo ç ã"}]
        arquivo = str(tmp_path / "utf8.txt")
        from diagnostics import export_report
        export_report(resultados, filename=arquivo)
        conteudo = open(arquivo, encoding="utf-8").read()
        assert "Diagnóstico" in conteudo
        assert "ç" in conteudo


# ===========================================================================
# FIXES dict — integridade estrutural
# ===========================================================================

class TestFixesDict:
    def test_todas_as_chaves_esperadas_existem(self):
        from diagnostics import FIXES
        esperados = {"DNS Flush", "Winsock", "IP Reset", "Firewall", "DNS Service",
                     "GPUpdate", "CHKDSK", "SFC", "DISM", "IP Renew"}
        assert set(FIXES.keys()) == esperados

    def test_cada_fix_tem_4_campos(self):
        from diagnostics import FIXES
        for nome, valor in FIXES.items():
            assert len(valor) == 4, f"Fix '{nome}' deveria ter 4 campos"

    def test_timeout_e_inteiro_positivo(self):
        from diagnostics import FIXES
        for nome, (cmd, needs_admin, timeout, nota) in FIXES.items():
            assert isinstance(timeout, int) and timeout > 0, f"Timeout inválido em '{nome}'"

    def test_needs_admin_e_booleano(self):
        from diagnostics import FIXES
        for nome, (cmd, needs_admin, timeout, nota) in FIXES.items():
            assert isinstance(needs_admin, bool), f"needs_admin não bool em '{nome}'"

    def test_comando_nao_vazio(self):
        from diagnostics import FIXES
        for nome, (cmd, _, _, _) in FIXES.items():
            assert cmd and cmd.strip(), f"Comando vazio em '{nome}'"

    def test_nota_e_string(self):
        from diagnostics import FIXES
        for nome, (_, _, _, nota) in FIXES.items():
            assert isinstance(nota, str), f"nota não é str em '{nome}'"

    def test_dns_flush_nao_requer_admin(self):
        from diagnostics import FIXES
        _, needs_admin, _, _ = FIXES["DNS Flush"]
        assert needs_admin is False

    def test_gpupdate_nao_requer_admin(self):
        from diagnostics import FIXES
        _, needs_admin, _, _ = FIXES["GPUpdate"]
        assert needs_admin is False

    def test_sfc_requer_admin(self):
        from diagnostics import FIXES
        _, needs_admin, _, _ = FIXES["SFC"]
        assert needs_admin is True

    def test_dism_requer_admin(self):
        from diagnostics import FIXES
        _, needs_admin, _, _ = FIXES["DISM"]
        assert needs_admin is True

    def test_winsock_requer_admin(self):
        from diagnostics import FIXES
        _, needs_admin, _, _ = FIXES["Winsock"]
        assert needs_admin is True

    def test_sfc_timeout_longo(self):
        """SFC pode demorar até 30 min — timeout deve ser >= 1800."""
        from diagnostics import FIXES
        _, _, timeout, _ = FIXES["SFC"]
        assert timeout >= 1800

    def test_dism_timeout_longo(self):
        from diagnostics import FIXES
        _, _, timeout, _ = FIXES["DISM"]
        assert timeout >= 1800

    def test_fixes_com_nota_tem_texto(self):
        """Fixes que exigem reboot ou aviso devem ter nota preenchida."""
        from diagnostics import FIXES
        com_nota = ["Winsock", "IP Reset", "CHKDSK", "SFC", "DISM", "IP Renew"]
        for nome in com_nota:
            _, _, _, nota = FIXES[nome]
            assert nota, f"Fix '{nome}' deveria ter nota mas está vazia"

    def test_fixes_sem_nota_tem_string_vazia(self):
        from diagnostics import FIXES
        sem_nota = ["DNS Flush", "Firewall", "GPUpdate"]
        for nome in sem_nota:
            _, _, _, nota = FIXES[nome]
            assert nota == "", f"Fix '{nome}' deveria ter nota vazia mas tem: {nota!r}"


# ===========================================================================
# config.py — load_config (casos extras)
# ===========================================================================

class TestLoadConfigExtra:
    def test_config_parcial_sem_chave_logs(self, tmp_path):
        """Arquivo sem 'logs' ainda é carregado sem erro."""
        cfg = {"version": "4.0", "last_run": "2025-01-01"}
        f = tmp_path / "winfix.json"
        f.write_text(json.dumps(cfg))
        with patch("config.CONFIG_FILE", str(f)):
            from config import load_config
            result = load_config()
        assert result["version"] == "4.0"

    def test_config_objeto_vazio_retornado_sem_erro(self, tmp_path):
        f = tmp_path / "winfix.json"
        f.write_text("{}")
        with patch("config.CONFIG_FILE", str(f)):
            from config import load_config
            result = load_config()
        assert isinstance(result, dict)

    def test_config_com_chaves_extras_preservadas(self, tmp_path):
        cfg = {"version": "1.0", "last_run": "", "custom_key": "valor_extra"}
        f = tmp_path / "winfix.json"
        f.write_text(json.dumps(cfg))
        with patch("config.CONFIG_FILE", str(f)):
            from config import load_config
            result = load_config()
        assert result.get("custom_key") == "valor_extra"

    def test_arquivo_vazio_retorna_padrao(self, tmp_path):
        f = tmp_path / "winfix.json"
        f.write_text("")
        with patch("config.CONFIG_FILE", str(f)):
            from config import load_config
            result = load_config()
        assert result["version"] == "2.0"

    def test_retorno_e_sempre_dict(self, tmp_path):
        for conteudo in ["{}", "invalido", ""]:
            f = tmp_path / "winfix.json"
            f.write_text(conteudo)
            with patch("config.CONFIG_FILE", str(f)):
                from config import load_config
                assert isinstance(load_config(), dict)


# ===========================================================================
# auth.py — is_admin (casos extras)
# ===========================================================================

class TestIsAdminExtra:
    def test_valor_maior_que_1_retorna_true(self):
        with patch("ctypes.windll", create=True) as mock_windll:
            mock_windll.shell32.IsUserAnAdmin.return_value = 42
            from auth import is_admin
            assert is_admin() is True

    def test_chamadas_multiplas_sao_idempotentes(self):
        with patch("ctypes.windll", create=True) as mock_windll:
            mock_windll.shell32.IsUserAnAdmin.return_value = 1
            from auth import is_admin
            assert is_admin() is True
            assert is_admin() is True
            assert is_admin() is True

    def test_retorna_bool_nao_int(self):
        with patch("ctypes.windll", create=True) as mock_windll:
            mock_windll.shell32.IsUserAnAdmin.return_value = 1
            from auth import is_admin
            resultado = is_admin()
            assert type(resultado) is bool


# ===========================================================================
# diagnostics.py — run_cmd (casos extras)
# ===========================================================================

class TestRunCmdExtra:
    def test_stdout_e_stderr_presentes_simultaneamente(self):
        proc = _mock_process(b"saida normal", b"aviso aqui", 0)
        with patch("asyncio.create_subprocess_shell", AsyncMock(return_value=proc)):
            from diagnostics import run_cmd
            stdout, stderr, code = run(run_cmd("cmd"))
        assert stdout == "saida normal"
        assert stderr == "aviso aqui"
        assert code == 0

    def test_return_code_diferente_de_zero_preservado(self):
        proc = _mock_process(b"erro", b"", 2)
        with patch("asyncio.create_subprocess_shell", AsyncMock(return_value=proc)):
            from diagnostics import run_cmd
            _, _, code = run(run_cmd("cmd"))
        assert code == 2

    def test_output_vazio_retornado_corretamente(self):
        proc = _mock_process(b"", b"", 0)
        with patch("asyncio.create_subprocess_shell", AsyncMock(return_value=proc)):
            from diagnostics import run_cmd
            stdout, stderr, code = run(run_cmd("cmd"))
        assert stdout == ""
        assert stderr == ""
        assert code == 0

    def test_bytes_utf8_invalidos_ignorados_sem_excecao(self):
        """Sequências UTF-8 inválidas devem ser ignoradas, não estourar."""
        proc = _mock_process(b"\xff\xfe bytes invalidos", b"", 0)
        with patch("asyncio.create_subprocess_shell", AsyncMock(return_value=proc)):
            from diagnostics import run_cmd
            stdout, _, _ = run(run_cmd("cmd"))
        assert isinstance(stdout, str)

    def test_output_grande_retornado_completo(self):
        grande = b"x" * 100_000
        proc = _mock_process(grande, b"", 0)
        with patch("asyncio.create_subprocess_shell", AsyncMock(return_value=proc)):
            from diagnostics import run_cmd
            stdout, _, _ = run(run_cmd("cmd"))
        assert len(stdout) == 100_000

    def test_mensagem_de_erro_contem_descricao_da_excecao(self):
        with patch("asyncio.create_subprocess_shell", AsyncMock(side_effect=OSError("Arquivo não encontrado"))):
            from diagnostics import run_cmd
            stdout, _, _ = run(run_cmd("cmd"))
        assert "Arquivo não encontrado" in stdout


# ===========================================================================
# diagnostics.py — run_full_diagnostics (casos extras)
# ===========================================================================

class TestRunFullDiagnosticsExtra:
    def test_nomes_dos_diags_estao_corretos(self):
        nomes_esperados = [
            "Ping Google", "Ipconfig", "Tracert", "NSLookup", "Disco Livre",
            "Memória", "Processos Top 20", "Interfaces Rede", "SFC Status",
            "DISM Health", "Netstat", "Drivers", "SystemInfo", "GPUpdate",
            "CHKDSK C:", "Eventos Erros", "Serviços", "Firewall",
            "Rede Adaptadores", "Rota", "USB Devices", "WiFi",
        ]
        with patch("diagnostics.run_cmd", AsyncMock(return_value=("a" * 100, "", 0))):
            from diagnostics import run_full_diagnostics
            results = run(run_full_diagnostics())
        nomes_obtidos = [r["name"] for r in results]
        assert nomes_obtidos == nomes_esperados

    def test_resultado_misto_ok_e_fail(self):
        """Simula metade OK e metade FAIL alternando code."""
        chamadas = {"n": 0}

        async def run_cmd_alternado(cmd, timeout=30):
            code = 0 if chamadas["n"] % 2 == 0 else 1
            chamadas["n"] += 1
            return ("a" * 100, "", code)

        with patch("diagnostics.run_cmd", run_cmd_alternado):
            from diagnostics import run_full_diagnostics
            results = run(run_full_diagnostics())

        ok_count = sum(1 for r in results if "🟢" in r["status"])
        fail_count = sum(1 for r in results if "🔴" in r["status"])
        assert ok_count > 0
        assert fail_count > 0
        assert ok_count + fail_count == 22

    def test_fronteira_output_exatamente_50_chars_e_fail(self):
        """Output com exatamente 50 chars deve ser FAIL (condição: > 50)."""
        with patch("diagnostics.run_cmd", AsyncMock(return_value=("x" * 50, "", 0))):
            from diagnostics import run_full_diagnostics
            results = run(run_full_diagnostics())
        assert all(r["status"] == "🔴 FAIL" for r in results)

    def test_fronteira_output_51_chars_e_ok(self):
        """Output com 51 chars + code 0 deve ser OK."""
        with patch("diagnostics.run_cmd", AsyncMock(return_value=("x" * 51, "", 0))):
            from diagnostics import run_full_diagnostics
            results = run(run_full_diagnostics())
        assert all(r["status"] == "🟢 OK" for r in results)

    def test_details_contem_stdout_mais_stderr(self):
        with patch("diagnostics.run_cmd", AsyncMock(return_value=("STDOUT", "STDERR", 0))):
            from diagnostics import run_full_diagnostics
            results = run(run_full_diagnostics())
        # details = stdout + stderr = "STDOUTSTDERR"
        assert all("STDOUT" in r["details"] for r in results)


# ===========================================================================
# diagnostics.py — run_fix (casos extras)
# ===========================================================================

class TestRunFixExtra:
    def _patch(self, stdout="saida", stderr="", code=0):
        return patch("diagnostics.run_cmd", AsyncMock(return_value=(stdout, stderr, code)))

    def test_todos_os_fixes_individuais_por_nome(self):
        """Garante que cada fix pode ser chamado individualmente sem erro."""
        from diagnostics import FIXES
        with self._patch(code=0):
            from diagnostics import run_fix
            for nome in FIXES:
                ok, output = run(run_fix(nome))
                assert isinstance(ok, bool), f"run_fix('{nome}') não retornou bool"
                assert isinstance(output, str), f"run_fix('{nome}') output não é str"

    def test_fix_individual_sem_nota_nao_tem_marcador_nota(self):
        with self._patch(stdout="flushed", code=0):
            from diagnostics import run_fix
            _, output = run(run_fix("DNS Flush"))
        assert "[NOTA]" not in output

    def test_fix_completo_output_contem_todos_os_nomes(self):
        with self._patch(code=0):
            from diagnostics import run_fix, FIXES
            _, output = run(run_fix())
        for nome in FIXES:
            assert nome in output, f"Nome '{nome}' não encontrado no output do run_fix()"

    def test_fix_completo_formato_ok_no_output(self):
        with self._patch(code=0):
            from diagnostics import run_fix
            _, output = run(run_fix())
        assert "[OK  ]" in output

    def test_fix_completo_formato_fail_no_output(self):
        with self._patch(code=1):
            from diagnostics import run_fix
            _, output = run(run_fix())
        assert "[FAIL]" in output

    def test_fix_completo_progress_total_correto(self):
        totais = []

        async def mock_progress(atual, total, nome):
            totais.append(total)

        with self._patch(code=0):
            from diagnostics import run_fix, FIXES
            run(run_fix(on_progress=mock_progress))

        assert all(t == len(FIXES) for t in totais)

    def test_fix_completo_progress_sequencial(self):
        atuais = []

        async def mock_progress(atual, total, nome):
            atuais.append(atual)

        with self._patch(code=0):
            from diagnostics import run_fix, FIXES
            run(run_fix(on_progress=mock_progress))

        assert atuais == list(range(1, len(FIXES) + 1))

    def test_fix_ip_renew_tem_nota_sobre_rede(self):
        with self._patch(code=0):
            from diagnostics import run_fix
            _, output = run(run_fix("IP Renew"))
        assert "[NOTA]" in output

    def test_fix_sfc_tem_nota_sobre_tempo(self):
        with self._patch(code=0):
            from diagnostics import run_fix
            _, output = run(run_fix("SFC"))
        assert "[NOTA]" in output
        assert "30 min" in output

    def test_fix_output_combina_stdout_e_stderr(self):
        with patch("diagnostics.run_cmd", AsyncMock(return_value=("parte1", "parte2", 0))):
            from diagnostics import run_fix
            _, output = run(run_fix("DNS Flush"))
        assert "parte1" in output
        assert "parte2" in output


# ===========================================================================
# diagnostics.py — export_report (casos extras)
# ===========================================================================

class TestExportReportExtra:
    def test_todos_ok_sem_problemas(self, tmp_path):
        resultados = [
            {"name": "Ping", "status": "🟢 OK", "details": "ok"},
            {"name": "DNS", "status": "🟢 OK", "details": "ok"},
        ]
        arquivo = str(tmp_path / "r.txt")
        from diagnostics import export_report
        export_report(resultados, filename=arquivo)
        conteudo = open(arquivo, encoding="utf-8").read()
        assert "Problemas : 0" in conteudo
        assert "OK        : 2" in conteudo

    def test_todos_fail(self, tmp_path):
        resultados = [
            {"name": "Disco", "status": "🔴 FAIL", "details": "cheio"},
            {"name": "Rede", "status": "🔴 FAIL", "details": "sem conexão"},
        ]
        arquivo = str(tmp_path / "r.txt")
        from diagnostics import export_report
        export_report(resultados, filename=arquivo)
        conteudo = open(arquivo, encoding="utf-8").read()
        assert "Problemas : 2" in conteudo
        assert "OK        : 0" in conteudo

    def test_relatorio_contem_data_hora(self, tmp_path):
        import re
        arquivo = str(tmp_path / "r.txt")
        from diagnostics import export_report
        export_report([{"name": "X", "status": "🟢 OK", "details": "ok"}], filename=arquivo)
        conteudo = open(arquivo, encoding="utf-8").read()
        # Formato dd/mm/yyyy HH:MM:SS
        assert re.search(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}", conteudo)

    def test_relatorio_contem_linhas_separadoras(self, tmp_path):
        arquivo = str(tmp_path / "r.txt")
        from diagnostics import export_report
        export_report([{"name": "X", "status": "🟢 OK", "details": "ok"}], filename=arquivo)
        conteudo = open(arquivo, encoding="utf-8").read()
        assert "=" * 70 in conteudo
        assert "-" * 70 in conteudo

    def test_detalhes_multilinhas_estao_indentados(self, tmp_path):
        resultados = [{"name": "Disco", "status": "🟢 OK", "details": "linha1\nlinha2\nlinha3"}]
        arquivo = str(tmp_path / "r.txt")
        from diagnostics import export_report
        export_report(resultados, filename=arquivo)
        conteudo = open(arquivo, encoding="utf-8").read()
        assert "    linha1" in conteudo
        assert "    linha2" in conteudo
        assert "    linha3" in conteudo

    def test_relatorio_contem_fim_do_relatorio(self, tmp_path):
        arquivo = str(tmp_path / "r.txt")
        from diagnostics import export_report
        export_report([], filename=arquivo)
        conteudo = open(arquivo, encoding="utf-8").read()
        assert "FIM DO RELATÓRIO" in conteudo

    def test_numeracao_sequencial_dos_itens(self, tmp_path):
        resultados = [
            {"name": "A", "status": "🟢 OK", "details": "ok"},
            {"name": "B", "status": "🔴 FAIL", "details": "erro"},
            {"name": "C", "status": "🟢 OK", "details": "ok"},
        ]
        arquivo = str(tmp_path / "r.txt")
        from diagnostics import export_report
        export_report(resultados, filename=arquivo)
        conteudo = open(arquivo, encoding="utf-8").read()
        assert "01." in conteudo
        assert "02." in conteudo
        assert "03." in conteudo

    def test_nome_arquivo_padrao(self, tmp_path):
        """Quando filename não especificado, usa 'winfix_report.txt' no cwd."""
        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            from diagnostics import export_report
            export_report([])
            assert os.path.exists("winfix_report.txt")
        finally:
            os.chdir(original_cwd)


# ===========================================================================
# main.py — relaunch_as_admin
# ===========================================================================

class TestRelaunchAsAdmin:
    def test_chama_shellexecutew_com_runas(self):
        with patch("ctypes.windll", create=True) as mock_windll, \
             patch("sys.exit") as mock_exit:
            from main import relaunch_as_admin
            relaunch_as_admin()
            mock_windll.shell32.ShellExecuteW.assert_called_once()
            args = mock_windll.shell32.ShellExecuteW.call_args[0]
            assert "runas" in args

    def test_chama_sys_exit_apos_shellexecute(self):
        with patch("ctypes.windll", create=True), \
             patch("sys.exit") as mock_exit:
            from main import relaunch_as_admin
            relaunch_as_admin()
            mock_exit.assert_called_once()

    def test_passa_sys_executable_como_programa(self):
        with patch("ctypes.windll", create=True) as mock_windll, \
             patch("sys.exit"):
            from main import relaunch_as_admin
            relaunch_as_admin()
            args = mock_windll.shell32.ShellExecuteW.call_args[0]
            assert sys.executable in args
