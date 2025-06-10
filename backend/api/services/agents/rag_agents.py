import os
import time
import asyncio
from typing import Annotated, Any, List, cast

from typing_extensions import TypedDict
from pydantic import BaseModel, Field
import re

from langchain_openai import ChatOpenAI
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langgraph.types import StreamWriter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

from langgraph.checkpoint.memory import MemorySaver
 
# services.agents.rag_agent_utils cuando se use el agente global
# rag_agent_utils cuando se use el agente rag solo
from services.agents.rag_agent_utils import (
    REPORT_GENERATION_PROMPT,
    filtrar_documentos_por_ids,
    id_agregator,
    QUERY_EXPANSION_PROMPT,
    QUERY_EXPANSION_PROMPT_2,
    REFLECTION_DOCS_PROMPT,
    REFLECTION_COMPLETENESS_PROMPT,
    ReflectionDocs,
    ReflectionCompleteness,
    Queries,
)

# -------------------------------
# 1. Definición del estado del agente
# -------------------------------
class AgentState(TypedDict):
    user_question: str
    messages: Annotated[List[Any], add_messages]
    queries: List[str]
    retrieved_docs: Annotated[List[Any], add_messages]
    relevant_docs: Annotated[List[Any], add_messages]
    docs_reflection: Annotated[List[Any], add_messages]
    report_reflection: Annotated[List[Any], add_messages]
    thoughts: List[str]
    response: str
    iterations_retrieval: int
    iterations: int
    has_relevant_docs: bool
    is_complete: bool

# -------------------------------
# 2. Agent RAG Async
# -------------------------------
class RagAgent:
    def __init__(
        self,
        model: ChatOpenAI,
        vectorstore: Chroma,
        max_iteraciones: int = 1,
        max_iteraciones_retrieval: int = 1,
    ):
        self.model = model
        self.vectorstore = vectorstore
        self.max_iteraciones = max_iteraciones
        self.max_iteraciones_retrieval = max_iteraciones_retrieval
        self.memory = MemorySaver()  # Instancia de checkpointer


        # Graph
        graph = StateGraph(AgentState)
        graph.add_node("query_expansion", self.query_expansion)
        graph.add_node("retrieval", self.retrieval)
        graph.add_node("reflection_docs", self.reflection_docs)
        graph.add_node("generation", self.generation)
        graph.add_node("reflection_completeness", self.reflection_completeness)

        graph.add_edge("query_expansion", "retrieval")
        graph.add_edge("retrieval", "reflection_docs")
        graph.add_conditional_edges(
            "reflection_docs",
            self.conditional_reflection_docs,
            {True: "generation", False: "query_expansion"},
        )
        graph.add_edge("generation", "reflection_completeness")
        graph.add_conditional_edges(
            "reflection_completeness",
            self.conditional_reflection_completeness,
            {True: END, False: "query_expansion"},
        )

        graph.set_entry_point("query_expansion")
        self.graph = graph.compile()

    async def query_expansion(self, state: AgentState, writer: StreamWriter) -> dict[str, Any]:
        writer({"custom_key": f"Generando queries (iterRetrieval={state['iterations_retrieval'] + 1})..."})
        
        if state["iterations_retrieval"] == 0:
            prompt = QUERY_EXPANSION_PROMPT.format(
                question=state["user_question"],
            )
        else:
            prompt = QUERY_EXPANSION_PROMPT_2.format(
                question=state["user_question"],
                previous_queries=state["queries"],
                thoughts=state["thoughts"],
            )

        # Llamada async al LLM con structured output
        llm = self.model.with_structured_output(Queries, method="function_calling")
        result = await llm.ainvoke(prompt)
        queries = cast(Queries, result).queries
        state["queries"] = queries
        writer({"custom_key": f"Queries generadas: {queries}"})
        return {"queries": queries}

    async def retrieval(self, state: AgentState, writer: StreamWriter) -> None:
        writer({"custom_key": f"Recuperando docs iterRetrieval={state['iterations_retrieval'] + 1}..."})
        documentos = []
        
        for q in state["queries"]:
            years_in_query = re.findall(r'\b(?:19|20)\d{2}\b', q)
            if years_in_query:
                filtro_year = years_in_query[0]
                writer({"custom_key": f"Aplicando filtro year={filtro_year} para la query: '{q[:50]}...'"})
                docs = await asyncio.to_thread(
                    self.vectorstore.similarity_search,
                    q,
                    3,
                    {"year": filtro_year}  # aquí el filtro
                )
            else:
                docs = await asyncio.to_thread(self.vectorstore.similarity_search, q, 3)
            documentos.extend(docs)
        ided = id_agregator(documentos, (state["iterations"] + state["iterations_retrieval"]) * 10 + 1)
        state["retrieved_docs"].extend(ided)
        writer({"custom_key": f"Retrieved {len(ided)} documents."})
        for doc in ided:
            writer({"custom_key": f"Retrieved {str(doc)[:200]}..."})
        return {}

    async def reflection_docs(self, state: AgentState, writer: StreamWriter) -> dict[str, Any]:
        writer({"custom_key": "Reflexionando sobre docs recuperados..."})
        prompt = REFLECTION_DOCS_PROMPT.format(
            user_input=state["user_question"],
            retrieved_documents=state["retrieved_docs"],
        )
        llm = self.model.with_structured_output(ReflectionDocs, method="function_calling")
        result = await llm.ainvoke(prompt)
        filtered = filtrar_documentos_por_ids(result.id_relevant_docs, state["retrieved_docs"])
        state["relevant_docs"].extend(filtered)
        has = len(filtered) > 0
        return {"has_relevant_docs": has, "thoughts": result.thoughts, "iterations_retrieval": state["iterations_retrieval"] + 1}

    def conditional_reflection_docs(self, state: AgentState, writer: StreamWriter) -> bool:
        return state["has_relevant_docs"] or state["iterations_retrieval"] >= self.max_iteraciones_retrieval

    async def generation(self, state: AgentState, writer: StreamWriter) -> dict[str, Any]:
        writer({"custom_key": "Generating report..."})
        prompt = REPORT_GENERATION_PROMPT.format(
            user_input=state["user_question"],
            retrieved_documents=state["relevant_docs"],
        )
        resp = await self.model.ainvoke(prompt)
        state["response"] = resp.content
        return {"response": resp.content}

    async def reflection_completeness(self, state: AgentState, writer: StreamWriter) -> dict[str, Any]:
        writer({"custom_key": "Verificando completitud..."})
        prompt = REFLECTION_COMPLETENESS_PROMPT.format(
            user_input=state["user_question"],
            generated_report=state["response"],
        )
        llm = self.model.with_structured_output(ReflectionCompleteness, method="function_calling")
        result = await llm.ainvoke(prompt)
        state["is_complete"] = result.is_complete
        return {"is_complete": result.is_complete, "thoughts": result.thoughts, "iterations": state["iterations"] + 1}

    async def conditional_reflection_completeness(self, state: AgentState, writer: StreamWriter):
        #writer({"rag_key": f"{state["response"]}"})
        #return state["is_complete"] or state["iterations"] >= self.max_iteraciones
        if state["is_complete"] or state["iterations"] >= self.max_iteraciones:
            writer({"custom_key": f" Report complete - iterations: {state["iterations"]}"})
            writer({"rag_key": f"{state["response"]}"})
            return True
        writer({"custom_key": f" Let's keep researching! - iter {state["iterations"]}"})
        return False

async def run(question: str, model, vectorstore, max_iteraciones: int = 1, max_iteraciones_retrieval: int = 1) -> str:

    rag_agent = RagAgent(model, vectorstore, max_iteraciones=max_iteraciones, max_iteraciones_retrieval=max_iteraciones_retrieval)
    # Estado inicial
    state: AgentState = {
        "user_question": question,
        "messages": [],
        "queries": [],
        "retrieved_docs": [],
        "relevant_docs": [],
        "docs_reflection": [],
        "report_reflection": [],
        "thoughts": [],
        "response": "",
        "iterations": 0,
        "iterations_retrieval": 0,
        "has_relevant_docs": False,
        "is_complete": False,
    }
    # Ejecutar grafo de forma async
    async for chunk in rag_agent.graph.astream(state, stream_mode="custom"):

        # print(chunk)
        if chunk.get("rag_key"):
            print("🔍 FINAL KEY OBTAINED IN RAG")
            res = chunk["rag_key"]
            return res
            #return chunk
    #return state["response"]
    return "Error: No se pudo generar una respuesta completa."

if __name__ == "__main__":
    # Ejemplo de uso
    llm = ChatOpenAI(temperature=0, model="gpt-4.1-mini-2025-04-14",  openai_api_key=os.getenv("OPENAI_API_KEY")) # streaming=True,?
    embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"), model="text-embedding-3-small")
    vectorstore = Chroma(persist_directory="services/agents/vectorstore_chromadb", embedding_function=embeddings)

    question = "¿What are the main sources of income of Logista?"
    res = asyncio.run(run(question, llm, vectorstore, max_iteraciones=1, max_iteraciones_retrieval=1))
    print("\n=== RESULT ===\n")
    print(res)
