# lang/test_cli.py
"""Tests de la CLI principal (main.py) usando pytest + capsys."""

import pytest
import tempfile
import os
from main import main


# Especies de prueba simples
URUK_SIMPLE = """creature Uruk
faction isengard
health 10
vision 3
lifespan 50
start:
wait(1)
"""

ORC_SIMPLE = """creature Orc
faction mordor
health 8
vision 2
lifespan 40
start:
wait(1)
"""


def escribir_archivo_temp(contenido, sufijo=".ins"):
    """Crea un archivo temporal y retorna su path."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=sufijo, delete=False, encoding="utf-8") as f:
        f.write(contenido)
        return f.name


def limpiar_archivo(path):
    """Elimina archivo temporal si existe."""
    try:
        os.unlink(path)
    except OSError:
        pass


def run_main(args):
    """Ejecuta main() y retorna (exit_code, stdout, stderr).
    
    Como main() usa raise SystemExit(code), capturamos la excepción.
    """
    import sys
    from io import StringIO
    
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = StringIO()
    sys.stderr = StringIO()
    try:
        main(args)
        exit_code = 0
    except SystemExit as e:
        exit_code = e.code if e.code is not None else 0
    finally:
        stdout = sys.stdout.getvalue()
        stderr = sys.stderr.getvalue()
        sys.stdout = old_stdout
        sys.stderr = old_stderr
    return exit_code, stdout, stderr


class TestCLI:
    """Tests de la función main() de la CLI."""

    def test_valido_dos_especies(self, capsys):
        """Ejecución exitosa con 2 especies."""
        uruk = escribir_archivo_temp(URUK_SIMPLE)
        orc = escribir_archivo_temp(ORC_SIMPLE)
        try:
            exit_code, out, err = run_main([uruk, orc, "--ticks", "5"])
            assert exit_code == 0
            assert "Uruk" in out and "Orc" in out
            assert "nace en" in out
            assert "fin en tick" in out
        finally:
            limpiar_archivo(uruk)
            limpiar_archivo(orc)

    def test_ticks_cero_rechazado(self):
        """--ticks 0 debe fallar con código 1."""
        uruk = escribir_archivo_temp(URUK_SIMPLE)
        try:
            exit_code, out, err = run_main([uruk, "--ticks", "0"])
            assert exit_code == 1
            assert "--ticks debe ser >= 1" in err
        finally:
            limpiar_archivo(uruk)

    def test_width_negativo_rechazado(self):
        """--width -5 debe fallar con código 1."""
        uruk = escribir_archivo_temp(URUK_SIMPLE)
        try:
            exit_code, out, err = run_main([uruk, "--width", "-5"])
            assert exit_code == 1
            assert "--width debe ser >= 1" in err
        finally:
            limpiar_archivo(uruk)

    def test_height_cero_rechazado(self):
        """--height 0 debe fallar con código 1."""
        uruk = escribir_archivo_temp(URUK_SIMPLE)
        try:
            exit_code, out, err = run_main([uruk, "--height", "0"])
            assert exit_code == 1
            assert "--height debe ser >= 1" in err
        finally:
            limpiar_archivo(uruk)

    def test_archivo_inexistente(self):
        """Archivo .ins inexistente debe fallar con código 1."""
        exit_code, out, err = run_main(["no_existe.ins"])
        assert exit_code == 1
        assert "no se pudo leer" in err

    def test_especie_invalida_semantica(self):
        """Archivo .ins con error semántico (falta health) debe fallar."""
        invalido = """creature X
faction f
vision 2
lifespan 10
start:
wait(1)
"""
        path = escribir_archivo_temp(invalido)
        try:
            exit_code, out, err = run_main([path])
            assert exit_code == 1
            assert "falta la clave obligatoria 'health'" in err
        finally:
            limpiar_archivo(path)

    def test_sin_archivos(self):
        """Sin archivos .ins debe fallar (argparse nargs='+')."""
        exit_code, out, err = run_main([])
        assert exit_code == 2  # argparse error = exit code 2
        assert "archivo.ins" in err

    def test_seed_determinista(self):
        """Mismo seed produce misma simulación."""
        uruk = escribir_archivo_temp(URUK_SIMPLE)
        orc = escribir_archivo_temp(ORC_SIMPLE)
        try:
            # Primera corrida
            exit_code1, out1, err1 = run_main([uruk, orc, "--ticks", "10", "--seed", "42"])
            assert exit_code1 == 0
            
            # Segunda corrida con mismo seed
            exit_code2, out2, err2 = run_main([uruk, orc, "--ticks", "10", "--seed", "42"])
            assert exit_code2 == 0
            
            assert out1 == out2  # Misma salida = determinista
        finally:
            limpiar_archivo(uruk)
            limpiar_archivo(orc)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])