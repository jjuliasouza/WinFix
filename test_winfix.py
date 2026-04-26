import pytest
from unittest.mock import patch, AsyncMock
from diagnostics import run_cmd


@pytest.mark.asyncio
async def test_run_cmd_sucesso():
    """Testa se run_cmd retorna stdout corretamente em caso de sucesso."""
    with patch("asyncio.create_subprocess_shell") as mock_proc:
        mock = AsyncMock()
        mock.communicate.return_value = (b"OK", b"")
        mock.returncode = 0
        mock_proc.return_value = mock

        stdout, stderr, code = await run_cmd("ping google.com")
        assert "OK" in stdout
        assert code == 0


@pytest.mark.asyncio
async def test_run_cmd_timeout():
    """Testa se run_cmd retorna 'Timeout' ao estourar o tempo."""
    import asyncio
    with patch("asyncio.create_subprocess_shell") as mock_proc:
        mock = AsyncMock()
        mock.communicate.side_effect = asyncio.TimeoutError()
        mock_proc.return_value = mock

        stdout, stderr, code = await run_cmd("ping google.com", timeout=1)
        assert stdout == "Timeout"
        assert code == 1


@pytest.mark.asyncio
async def test_run_cmd_erro():
    """Testa se run_cmd captura exceções genéricas."""
    with patch("asyncio.create_subprocess_shell", side_effect=Exception("erro simulado")):
        stdout, stderr, code = await run_cmd("cmd_invalido")
        assert "Erro" in stdout
        assert code == 1
