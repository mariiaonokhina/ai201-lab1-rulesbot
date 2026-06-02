# Spec: `generate_response()`

**File:** `generator.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Given a user query and a list of retrieved rule chunks, generate a response that directly answers the question using only the retrieved text as context. The response must be grounded — it should not draw on the model's general knowledge of board games, only on what was retrieved.

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | `str` | The user's original question |
| `retrieved_chunks` | `list[dict]` | Ranked list of chunks from `retrieve()`, each with `"text"`, `"game"`, and `"distance"` |

**Output:** `str`

A plain string containing the response to show the user. The response should:
- Answer the question using only the retrieved rule text
- Identify which game the answer comes from
- Acknowledge clearly when the answer is not found in the loaded rules

Returns a fallback string (not an error) when `retrieved_chunks` is empty.

---

## Design Decisions

*Complete the fields below before writing any code. Use your AI tool in Plan or Ask mode to help you reason through what belongs here — but the decisions are yours.*

---

### Context formatting

*How will you format the retrieved chunks before passing them to the LLM? Describe the structure — not the code. Consider: will you label chunks by game? Include distance scores? Separate chunks with delimiters?*

```
I would not just pass all retrieved chunks as plain text because the model could mix information from different games together. Instead, I would structure the context so that each chunk is clearly separated and labeled with metadata such as the game name, source file, chunk ID, and similarity score. The chunks would be ordered from highest similarity to lowest similarity, and separated using clear delimiters so the model can distinguish between different sources more easily. I would also wrap all retrieved chunks inside a dedicated CONTEXT section to clearly separate retrieved information from the user query and system prompt. Including metadata and delimiters is supported by RAG research because it helps reduce source mixing, improves grounding, and makes citations/debugging easier. I would include similarity scores mostly as metadata for transparency and ranking, but not rely on the model to reason heavily from the score itself.
```

---

### System prompt — grounding instruction

*Write the exact system prompt instruction you will use to prevent the model from answering beyond the retrieved text. This is the most important design decision in this function.*

```
You are a grounded question-answering system. Answer the user’s question using ONLY the retrieved context provided below. Every factual statement in the response must be directly supported by at least one retrieved chunk. Do not use outside knowledge, prior training data, assumptions, or inferred information, even if the answer seems obvious or familiar. If the answer cannot be found explicitly in the retrieved context, respond exactly with: "The provided documents do not contain enough information to answer this question."

When answering:
- Use only information present in the retrieved chunks.
- Do not generalize or add background explanations not stated in the context.
- Do not merge rules or facts across unrelated games unless the retrieved text explicitly connects them.
- Cite the relevant source document or chunk ID for each major claim.
- Prefer quoting or closely paraphrasing retrieved text rather than rewriting from memory.

The retrieved context will appear between CONTEXT START and CONTEXT END.
```

---

### System prompt — citation instruction

*Write the exact instruction you will use to tell the model to identify which game its answer comes from.*

```
[your answer here]
```

---

### Fallback behavior

*What should the response say when the answer isn't found in the loaded rule books? Write the exact fallback message.*

```
[your answer here]
```

---

### Handling low-relevance chunks

*`retrieved_chunks` may include chunks with high distance scores (weak relevance). Will you filter these out before building context, pass them all in, or handle them another way? What are the tradeoffs?*

```
[your answer here]
```

---

### Message structure

*Describe how you will structure the messages list for the API call — what goes in the system message vs. the user message?*

```
[your answer here]
```

---

## Implementation Notes

*Fill this in after implementing and testing.*

**Test query and response:**

```
Query: What happens when you roll a 7?
Response: When a 7 is rolled, no resources are produced. Additionally, every player with more than 7 resource cards in hand must discard half (rounded down), and the player who rolled moves the robber to any terrain hex and steals one resource (Catan).
Correctly grounded? yes
Cited the right game? yes
```

**One thing you changed from your original spec after seeing the actual output:**

```
It was returning chunk IDs, so I made it return the actual game names it took the chunks from.
```
