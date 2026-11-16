"""Regresiones de integridad: python3 -m unittest discover -s Scripts -p 'test_*.py'."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IntegrityTests(unittest.TestCase):
    def test_catalog_keeps_dem_own_extent(self):
        module = load("13_procesar_orbital_y_mapas")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            orbital = root / "orbital"
            topo = root / "derivados" / "topografia"
            maps = root / "app" / "public" / "maps"
            for directory in (orbital, topo, maps):
                directory.mkdir(parents=True)
            (orbital / "jezero_ctx_5m_extent.json").write_text(
                json.dumps({"extent_app_m": [0, 0, 100, 100]}))
            (topo / "jezero_ctx_dem_20m_extent.json").write_text(
                json.dumps({"extent_app_m": [-10, -10, 110, 110]}))
            (maps / "jezero_ctx_dem_20m_color.jpg").touch()
            with patch.multiple(module, ROOT=root, ORB=orbital, OUT=root / "derivados", APPMAPS=maps):
                module.build_layers_catalog()
            layers = json.loads((maps.parent / "layers.json").read_text())["layers"]
            self.assertEqual(layers[0]["extent"], [-10, -10, 110, 110])

    def test_preallocated_part_is_not_published_as_complete(self):
        module = load("util_descarga_paralela")
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory) / "dem.tif"
            part = dest.with_suffix(".tif.part")
            with part.open("wb") as handle:
                handle.truncate(1024)
            with patch.object(module, "head_size", return_value=(1024, "https://example.org/dem")), \
                 patch("sys.argv", ["download", "https://example.org/dem", str(dest)]):
                self.assertEqual(module.main(), 1)
            self.assertFalse(dest.exists())
            self.assertTrue(part.exists())


if __name__ == "__main__":
    unittest.main()
