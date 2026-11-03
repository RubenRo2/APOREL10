import tomllib
from pathlib import Path

import aporel10


def test_version_del_paquete_coincide_con_pyproject():
    pyproject = Path(__file__).parents[1] / "pyproject.toml"
    with pyproject.open("rb") as archivo:
        version_esperada = tomllib.load(archivo)["project"]["version"]

    assert aporel10.__version__ == version_esperada