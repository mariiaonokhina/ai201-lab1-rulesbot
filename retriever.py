import chromadb
from chromadb.utils import embedding_functions
from config import CHROMA_COLLECTION, CHROMA_PATH, EMBEDDING_MODEL, N_RESULTS

# Cosine distance cutoff: chunks farther than this are treated as irrelevant.
# 0 = identical, 2 = opposite. ~0.5 is a reasonable starting point for
# all-MiniLM-L6-v2; tune by watching the real distances your queries return.
# If every result is above the cutoff, retrieve() falls back to the single
# best match so the bot is never left with no context at all.
DISTANCE_THRESHOLD = 0.5

# Embedding function and ChromaDB client are initialized once at module load.
# sentence-transformers downloads the model on first use — this may take
# 30–60 seconds the very first time. Subsequent runs use a local cache.
_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL
)
_client = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _client.get_or_create_collection(
    name=CHROMA_COLLECTION,
    embedding_function=_ef,
    metadata={"hnsw:space": "cosine"},
)


def get_collection():
    """Return the ChromaDB collection. Used by app.py during ingestion."""
    return _collection


def embed_and_store(chunks):
    """
    Embed a list of chunks and store them in the vector database.

    This function is already implemented — read through it before moving on.

    _collection.add() takes three parallel lists built from the chunks
    returned by chunk_document():
      - documents : raw text strings — ChromaDB's embedding function converts
                    these to vectors automatically using sentence-transformers
      - metadatas : one dict per chunk, stored alongside the vector so that
                    retrieve() can surface which game a result came from
      - ids       : the unique chunk_id strings used to identify each entry

    You don't generate embeddings manually here — you hand over the text
    and ChromaDB handles the vector math.
    """
    _collection.add(
        documents=[c["text"] for c in chunks],
        metadatas=[{"game": c["game"]} for c in chunks],
        ids=[c["chunk_id"] for c in chunks],
    )
    print(f"Stored {_collection.count()} total chunks in the vector database.")


def retrieve(query, n_results=N_RESULTS):
    """
    Find the most relevant rule chunks for a user's question.

    TODO — Milestone 2:

    Use _collection.query() to run a semantic search. It takes:
      - query_texts : a list containing your query string
      - n_results   : how many results to return
      - include     : what to return — use ["documents", "metadatas", "distances"]

    Return a list of dicts, each with:
      - "text"     : the chunk text
      - "game"     : the game name (pull this from metadatas)
      - "distance" : the similarity score (lower = more similar for cosine)

    Note: _collection.query() returns nested lists (one per query). You only
    have one query, so you'll want index [0] to get the actual results.
    """
    if _collection.count() == 0:
        return []

    # Semantic search. query_texts is a list (Chroma supports batching), so the
    # results come back nested one level per query — we index [0] to unwrap our
    # single query's matches.
    results = _collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    # The three lists are parallel: index i describes the same chunk in each.
    # Distances are sorted ascending, so documents[0] is the closest match.
    chunks = [
        {"text": text, "game": meta["game"], "distance": dist}
        for text, meta, dist in zip(documents, metadatas, distances)
    ]
    for chunk in chunks:
        print(f"[{chunk['game']}] (dist: {chunk['distance']:.3f}) {chunk['text'][:80]}...")

    # Hybrid filter: keep only chunks within the relevance threshold.
    relevant = [c for c in chunks if c["distance"] <= DISTANCE_THRESHOLD]

    # Fallback: if nothing cleared the threshold, return the single best chunk
    # rather than nothing, so the LLM still has some context to work from.
    if not relevant and chunks:
        return chunks[:1]

    return relevant
