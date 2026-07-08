from app.agent.state import AgentState
from app.core.config import get_tenant
from app.services.vectorstore import query_knowledge_base
from app.utils.llm import chat_text




async def rag_node(state: AgentState) -> dict:
    tenant = get_tenant(state["org_id"], state["branch_id"])
    chunks = await query_knowledge_base(tenant, state["user_message"], top_k=5)

    context = "\n\n".join(f"[{c['source']}] {c['text']}" for c in chunks) or "No matching documents found."
    system = (
        f"You are a helpful assistant for {tenant.display_name}. Answer the user's question "
        "using ONLY the knowledge base context below. If the answer isn't in the context, say "
        "you don't have that information and offer to connect them with the team.\n\n"
        f"KNOWLEDGE BASE CONTEXT:\n{context}"
    )
    answer = await chat_text(system, [{"role": "user", "content": state["user_message"]}])
    return {"retrieved_chunks": chunks, "rag_answer": answer, "final_response": answer}
