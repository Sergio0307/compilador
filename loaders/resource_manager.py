class ResourceManager:

    def __init__(self):
        self.terrains = {}
        self.objects = {}
        self.maps = {}
        self.creatures = {}

        self.errors = []

    def load_all(self):

        self.errors.clear()

        self.terrains = self.load_terrains()
        self.objects = self.load_objects()
        self.maps = self.load_maps()
        self.creatures = self.load_creatures()

    def load_terrains(self):
        # Load and validate every .te file.
        pass

    def load_objects(self):
        # Load and validate every .ob file.
        pass

    def load_maps(self):
        # Load maps using the registered terrains and objects.
        pass

    def load_creatures(self):
        # Compile all .ins files using compile_species().
        pass
