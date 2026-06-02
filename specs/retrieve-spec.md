# Spec: `retrieve()`

**File:** `retriever.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Given a user's natural language query, find the most relevant chunks from the vector store using semantic similarity search. Return them ranked by relevance so that `generate_response()` can use them as context.

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | `str` | The user's natural language question |
| `n_results` | `int` | Maximum number of chunks to return (default: `N_RESULTS` from `config.py`) |

**Output:** `list[dict]`

Each dict in the returned list must contain exactly these keys:

| Key | Type | Description |
|-----|------|-------------|
| `"text"` | `str` | The chunk text |
| `"game"` | `str` | The game name this chunk came from |
| `"distance"` | `float` | Cosine distance score — lower means more similar to the query |

Results should be ordered from most to least relevant (lowest to highest distance). Returns an empty list `[]` if the collection contains no documents.

---

## Design Decisions

*Complete the fields below before writing any code. Use your AI tool in Plan or Ask mode to help you reason through what belongs here — but the decisions are yours.*

---

### Query approach

*Describe how you will use `_collection.query()` to find relevant chunks. What arguments will you pass, and why?*

```
`_collection.query()` accepts `query_texts` (question(s) to search with), `n_results` (number of closest chunks to return for the query), and `include` (specifies which fields to return). We must specify to include what documents the suggestions came from as well as the metadatas to make sure that the RulesBot is answering about the correct game. Also, we need to make sure to include the distances to see which suggestions are the closest and how close they are.

So, an example usage of this function would be:

results = _collection.query(
    query_texts=["What happens when you complete a lap in Monopoly?"],
    n_results=3,
    include=["documents", "metadatas", "distances"]
)
```

---

### Return structure

*Sketch out what one item in your return list looks like as a concrete example. Where does each field come from in the query results?*

```
`_collection.query()` returns a dictionary, where every value is a list of lists. For example:

{
    "ids": [
        ["monopoly_1", "monopoly_5", "monopoly_9"]
    ],
    "documents": [
        [
            "When you pass "Go", .......",
            "The player who completes a lap must ........", 
            "The goal of this game is to get as much money as possible while buying properties and collecting money for passing "Go".
        ]
    ],
    "metadatas": [
        [
            {"game": "Monopoly"},
            {"game": "Monopoly"},
            {"game": "Monopoly"}
        ]
    ],
    "distances": [
        [0.18, 0.31, 0.42]
    ]
}

The "ids" come from the game name as well as chunk ids. The "documents" are the actual chunks found to be most similar to the query. The "metadatas" are the games that the chunks come from. The "distances" are how close the embeddings are to the query in the embedding space.
```

---

### Handling the nested result structure

*`_collection.query()` returns nested lists. Describe what index you need to access to get the actual list of results for a single query, and why the nesting exists.*

```
results["documents"] returns top-k chunks that are similar to the query.

results["documents"][0] returns the query's actual results, which is what we need (the "documents" field).

results["documents"][0][1] returns the 2nd best chunk. 

The nesting exists to handle multiple queries in a single call.
```

---

### Relevance threshold

*Will you filter out results above a certain distance score, or return all `n_results` regardless of how relevant they are? What are the tradeoffs of each approach?*

```
If we filter out results above a certain distance score, we risk losing important results or even return none of them because the closest results were above the threshold. If we return all `n_results`, it will slow the app down because there could potentially be hundreds of similar results and also there will be more noise from irrelevant chunks, which leads to worse RAG answers and higher token cost.

I would combine both approaches by retrieving a specific number of chunks only that are above a specific threshold.
```

---

### Edge cases

*How does your implementation behave when: (a) the collection is empty, (b) the query matches no chunks well, (c) the query matches chunks from multiple games?*

```
(a) When the collection is empty, it will return nothing, so it needs a fallback.
(b) If the query matches no chunks well, it might return a wrong result if we set the threshold too high, or it might return nothing, so we need a fallback.
(c) If the query matches chunks from multiple games, the retriever may return a mixture of relevant chunks from different sources. In this case, reranking, metadata filtering, or grouping results by game can help improve relevance and reduce confusion in the final RAG response.
```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 3.*

**Test query and top result returned:**

```
Query: What is a Wild Draw Four and when can you play it in Uno?
Top result game: Uno
Distance score: 0.354
Does it make sense? yes, it says for the next player to draw 4 cards and lose their turn.
```

**One thing about the query results that surprised you:**

```
They are not ordered and also the distance scores are pretty high.
```
