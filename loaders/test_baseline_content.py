import unittest

from loaders.resource_manager import ResourceManager


class TestBaselineContent(unittest.TestCase):
    """El contenido mínimo del repo se carga y produce un mapa jugable."""

    @classmethod
    def setUpClass(cls):
        cls.manager = ResourceManager(".")
        cls.errors = cls.manager.load_all()

    def test_no_hay_errores_de_carga(self):
        self.assertEqual([str(e) for e in self.errors], [])

    def test_carga_terreno_objeto_mapa_y_criatura(self):
        self.assertIn("Grass", self.manager.terrains)
        self.assertIn("Rock", self.manager.objects)
        self.assertIn("Test Field", self.manager.maps)
        self.assertIn("Uruk", self.manager.creatures)

    def test_el_mapa_construye_roca_sobre_grass(self):
        mapa = self.manager.maps["Test Field"].build()
        self.assertEqual((mapa.width, mapa.height), (10, 5))
        self.assertEqual(mapa.terrain_at(4, 2).name, "Grass")
        self.assertEqual(mapa.object_at(4, 2).name, "Rock")
        self.assertEqual(mapa.object_at(4, 2).reserve, 100)

    def test_uruk_conserva_sus_estadisticas(self):
        uruk = self.manager.creatures["Uruk"]
        self.assertEqual((uruk.health, uruk.vision, uruk.lifespan), (80, 6, 400))
        self.assertEqual(uruk.faction, "isengard")


if __name__ == "__main__":
    unittest.main()
