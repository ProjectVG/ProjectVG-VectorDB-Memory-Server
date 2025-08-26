class MemoryPoint:
    def __init__(self, vector: list, metadata: dict):
        self.vector = vector
        self.metadata = metadata
        self.score = None
        self.id = None
        self.collection_type = None 