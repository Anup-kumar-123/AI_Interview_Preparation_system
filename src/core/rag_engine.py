class SimpleRAGEngine:
    """Lightweight RAG service for matching target JD keywords."""
    def __init__(self):
        self.documents = []

    def index_text(self, text: str):
        """Splits document text into simple line chunks."""
        self.documents = [line.strip() for line in text.split("\n") if len(line.strip()) > 10]

    def query_context(self, keyword: str, top_k: int = 3) -> list[str]:
        """Finds matching context lines."""
        matches = [doc for doc in self.documents if keyword.lower() in doc.lower()]
        return matches[:top_k]
