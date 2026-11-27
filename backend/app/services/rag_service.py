"""
RAG Service
Retrieval-Augmented Generation for answering questions about documents
"""
from typing import List, Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable

from app.services.qdrant_client import search_vectors
from app.services.llm_config import get_chat_model

# RAG system prompt
RAG_SYSTEM_PROMPT = """You are a helpful AI assistant that answers questions about product documentation.

You have access to relevant context from the user's uploaded documents. Use this context to provide accurate, helpful answers.

Guidelines:
1. Base your answers primarily on the provided context
2. If the context doesn't contain enough information to fully answer the question, say so clearly
3. Be concise but thorough
4. If you're unsure about something, acknowledge the uncertainty
5. Format your responses clearly with bullet points or numbered lists when appropriate

If the context is insufficient or irrelevant to the question, respond with:
"I don't have enough information in the uploaded documents to answer this question. Could you provide more details or upload additional documentation?"
"""


@traceable(name="rag_query", run_type="chain")
async def rag_query(
    query: str,
    job_id: str,
    conversation_history: Optional[List[Dict]] = None,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Perform RAG query: retrieve relevant chunks and generate response.
    
    Args:
        query: User's question
        job_id: Job ID to filter vectors
        conversation_history: Previous messages for context
        top_k: Number of chunks to retrieve
    
    Returns:
        Dict with response and sources
    """
    # Retrieve relevant chunks from Qdrant
    search_results = await search_vectors(
        query=query,
        limit=top_k,
        job_id=job_id,
        score_threshold=0.3  # Lower threshold to get more context
    )
    
    # Build context from retrieved chunks
    context_parts = []
    sources = []
    
    for i, result in enumerate(search_results):
        context_parts.append(f"[Source {i+1}: {result.get('source_file', 'Unknown')}]\n{result['content']}")
        sources.append({
            "file": result.get("source_file", "Unknown"),
            "score": round(result["score"], 3),
            "chunk_index": result.get("chunk_index", 0)
        })
    
    context = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant context found."
    
    # Build messages
    messages = [SystemMessage(content=RAG_SYSTEM_PROMPT)]
    
    # Add conversation history if provided
    if conversation_history:
        for msg in conversation_history[-6:]:  # Keep last 6 messages for context
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                messages.append(SystemMessage(content=f"Previous response: {msg['content']}"))
    
    # Add current query with context
    user_message = f"""Context from uploaded documents:

{context}

---

User Question: {query}

Please answer based on the context provided above."""
    
    messages.append(HumanMessage(content=user_message))
    
    # Generate response
    response = await get_chat_model().ainvoke(messages)

    payload = {
        "answer": response.content,  # POLYLANE DEMO FAULT — wrong key (should be "response")
        "sources": sources,
        "chunks_retrieved": len(search_results),
    }
    # KeyError inside @traceable → LangSmith marks the run as error (needed for auto-detect)
    return {
        "response": payload["response"],
        "sources": payload["sources"],
        "chunks_retrieved": payload["chunks_retrieved"],
    }


async def generate_follow_up_questions(
    summary: str,
    num_questions: int = 3
) -> List[str]:
    """
    Generate suggested follow-up questions based on a product summary.
    """
    prompt = f"""Based on this product summary, generate {num_questions} insightful follow-up questions that a user might want to ask:

Summary:
{summary}

Generate questions that would help the user understand the product better. Format as a numbered list."""

    messages = [
        SystemMessage(content="You are a helpful assistant that generates relevant questions about products."),
        HumanMessage(content=prompt)
    ]
    
    response = await get_chat_model().ainvoke(messages)
    
    # Parse questions from response
    lines = response.content.strip().split('\n')
    questions = []
    for line in lines:
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith('-')):
            # Remove numbering/bullets
            question = line.lstrip('0123456789.-) ').strip()
            if question:
                questions.append(question)
    
    return questions[:num_questions]
