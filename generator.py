from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL

_client = Groq(api_key=GROQ_API_KEY)


def generate_response(query, retrieved_chunks):
    """
    Generate a grounded answer from retrieved rule chunks.

    TODO — Milestone 3:

    `retrieved_chunks` is the list returned by retrieve(). Each item is a dict:
      - "text"     : the chunk text
      - "game"     : the game name
      - "distance" : similarity score (you can use this to filter weak matches)

    Before writing code, talk through these with your group:
      - How will you format the chunks into a context block for the prompt?
      - What instructions will stop the model from answering beyond what the
        rules say? (Grounding is the whole point — a confident wrong answer
        is worse than an honest "I don't know.")
      - How will you surface which game each answer comes from?

    Your response should:
      1. Answer using only the retrieved context — not the model's general knowledge
      2. Make clear which game the answer comes from
      3. Say so clearly when the answer isn't in the loaded rules

    Return the response as a plain string.
    """
    if not retrieved_chunks:
        return (
            "I couldn't find anything relevant in the loaded rule books. "
            "Try rephrasing your question — or check that your ingestion pipeline is working."
        )

    system_message = (
        "You are a grounded question-answering system. Answer the user’s question "
        "using ONLY the retrieved context provided below. Every factual statement in "
        "the response must be directly supported by at least one retrieved chunk. Do "
        "not use outside knowledge, prior training data, assumptions, or inferred "
        "information, even if the answer seems obvious or familiar. If the answer "
        "cannot be found explicitly in the retrieved context, respond exactly with: "
        "\"The provided documents do not contain enough information to answer this "
        "question.\"\n\n"
        "When answering:\n"
        "- Use only information present in the retrieved chunks.\n"
        "- Do not generalize or add background explanations not stated in the context.\n"
        "- Do not merge rules or facts across unrelated games unless the retrieved text "
        "explicitly connects them.\n"
        "- Cite the relevant source document or chunk ID for each major claim.\n"
        "- Prefer quoting or closely paraphrasing retrieved text rather than rewriting "
        "from memory.\n\n"
        "The retrieved context will appear between CONTEXT START and CONTEXT END."
    )

    # Format each retrieved chunk with its metadata and a clear delimiter so the
    # model can distinguish sources and cite them. Order is preserved as ranked
    # by retrieve() (highest similarity first). The "source document" the model
    # should cite is the game name, since that is the only source identifier
    # retrieve() provides.
    formatted_chunks = []
    for i, chunk in enumerate(retrieved_chunks, start=1):
        game = chunk.get("game", "unknown")
        formatted_chunks.append(
            f"--- SOURCE: {game} (chunk {i}) ---\n"
            f"Source document: {game}\n"
            f"Similarity score (distance): {chunk.get('distance', 'n/a')}\n"
            f"Text: {chunk.get('text', '')}"
        )

    context_block = "\n\n".join(formatted_chunks)

    user_message = (
        "CONTEXT START\n"
        f"{context_block}\n"
        "CONTEXT END\n\n"
        "When you cite a claim, cite the source document by its game name "
        "(e.g. \"(Monopoly)\"), not by chunk number.\n\n"
        f"Question: {query}"
    )

    completion = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
    )

    if not completion or not completion.choices:
        return "The provided documents do not contain enough information to answer this question."

    content = completion.choices[0].message.content
    if not content or not content.strip():
        return "The provided documents do not contain enough information to answer this question."

    return content.strip()
