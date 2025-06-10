import os
import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from dataclasses import field
from typing import TypedDict, Any
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.types import StreamWriter
from services.agents.web_search_agent_utils import (
    QUERY_PROMPT, NOTES_PROMPT, COMPILER_PROMPT,
    REFLECTION_PROMPT, extract_clean_text, query_prompt_Nsch, notes_prompt_Nsch, compilador_prompt_Nsch, reflection_prompt_Nsch
)
from tavily import AsyncTavilyClient

# --- Carga variables de entorno ---
_ = load_dotenv()
async_tavily = AsyncTavilyClient(os.getenv("TAVILY_API_KEY"))

# --- Esquema de extracción ---
ESQUEMA = """
    ### Company_name: company name,
    ### Description: brief description of the company.
    ### History: Most important milestones, aquisitions, results from last years.
    ### Business: Understand what it does, possible entry barriers or competitive advantages. Who are its suppliers and customers.
    ### Market: Who it competes with and what are its market shares.
    ### People: Board of directors, management, and shareholders, who are they? How much does the management team earn and what are their incentives based on.
    ### Capital_allocation: Analysis of M&A, money allocated to dividends, share buybacks or issuance.
"""

class WebAgentState(TypedDict):
    company: str
    extraction_schema: dict[str, Any]
    user_notes: str
    pending_sections: str
    queries: list[str]
    search_results: Any
    info_compilada: Any
    is_complete: bool
    iteraciones: int


def generate_json_schema(num_queries: int) -> dict:
    props = {f"query_{i+1}": {"type": "string", "description": f"Search query text {i+1}"}
             for i in range(num_queries)}
    return {
        "title": "queries",
        "description": "Search queries",
        "type": "object",
        "properties": {"queries": {"type": "object", "properties": props}},
        "required": ["queries"]
    }

class Reflection(BaseModel):
    is_answered: bool = Field(description="True if schema is complete")
    pending_sections: str = Field(description="Pending or incomplete sections, comma-separated")
    analysis: str = Field(description="What to focus next")

class Reflection_Nsch(BaseModel):
    is_answered: bool = Field(description="True if user's question is complete")
    pending_sections: str = Field(description="Pending or incomplete sections or aspects, comma-separated")
    analysis: str = Field(description="What to focus next, give clear and precise instructions")

# Configuración
max_iteraciones = 1
max_search_results = 3
max_search_queries = 5

class WebSearchAgent:
    def __init__(self, model):
        self.query_prompt = QUERY_PROMPT
        self.notes_prompt = NOTES_PROMPT
        self.compilador_prompt = COMPILER_PROMPT
        self.reflection_prompt = REFLECTION_PROMPT
        self.query_prompt_Nsch = query_prompt_Nsch
        self.notes_prompt_Nsch = notes_prompt_Nsch
        self.compilador_prompt_Nsch = compilador_prompt_Nsch
        self.reflection_prompt_Nsch = reflection_prompt_Nsch
        self.urls = []
        self._sem = asyncio.Semaphore(5)
        graph = StateGraph(WebAgentState)
        graph.add_node("gen_query", self.query_generation)
        graph.add_node("buscar", self.busqueda)
        graph.add_node("compilador", self.compilador)
        graph.add_node("reflection", self.reflection)
        graph.add_edge("gen_query", "buscar")
        graph.add_edge("buscar", "compilador")
        graph.add_edge("compilador", "reflection")
        graph.add_conditional_edges(
            "reflection",
            self.conditional_reflection,
            {True: END, False: "gen_query"}
        )
        graph.set_entry_point("gen_query")
        self.graph = graph.compile()
        self.model = model

    async def query_generation(self, state: WebAgentState, writer: StreamWriter) -> dict[str, Any]:
        writer({"custom_key": f" Generating queries iter {state['iteraciones']+1} ..."})
        partes = state["pending_sections"].split(",") if state["pending_sections"] else []
        count = len(partes) if partes else max_search_queries
        if state["extraction_schema"]:
            prompt = self.query_prompt.format(
                schema=state["extraction_schema"],
                company=state["company"],
                user_notes=state["user_notes"],
                max_search_queries=count,
                pending_sections=partes,
                past_queries=state["queries"] or []
            )
        else:
            prompt = self.query_prompt_Nsch.format(
                instructions=state["user_notes"],
                company=state["company"],
                past_queries=state["queries"] or []
            )
        schema = generate_json_schema(count)
        struc = self.model.with_structured_output(schema)
        response = await struc.ainvoke(prompt)
        queries = list(response['queries'].values())
        writer({"custom_key": f" End query gen {state['iteraciones']+1}."})
        writer({"custom_key": f" Generated queries: {queries}"})
        return {"queries": queries}

    async def _search_one(self, query: str):
        async with self._sem:
            try:
                return await async_tavily.search(
                    query=query,
                    max_results=max_search_results,
                    include_images=False,
                    include_answer=False
                )
            except Exception as e:
                return e

    async def busqueda(self, state: WebAgentState, writer: StreamWriter) -> dict[str, Any]:
        writer({"custom_key": f" Launching web search iter {state['iteraciones']+1} ..."})
        partes = state["pending_sections"].split(",") if state["pending_sections"] else []
        queries = state['queries'][-len(partes):] if partes else state['queries']
        tasks = [self._search_one(q) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        compiled = []
        for res in results:
            if isinstance(res, Exception):
                writer({"custom_key": f"⚠️ Search failed: {res}"})
                compiled.append([])
            else:
                texts = [r['content'] for r in res['results']]
                compiled.append(texts)
        if state["extraction_schema"]:
            prompt = self.notes_prompt.format(
                company=state["company"],
                schema=state["extraction_schema"],
                content=compiled,
            )
        else:
            prompt = self.notes_prompt_Nsch.format(
                company=state["company"],
                instructions=state["user_notes"],
                content=compiled,
            )
        result = await self.model.ainvoke(prompt)
        writer({"custom_key": " Successfully received and extracted web search results!"})
        return {"search_results": result.content}

    async def compilador(self, state: WebAgentState, writer: StreamWriter) -> dict[str, Any]:
        writer({"custom_key": " Compiling data ..."})
        prev = state['extraction_schema'] if state['iteraciones'] == 0 else state['info_compilada']
        if state["extraction_schema"]:
            prompt = self.compilador_prompt.format(
                pending_sections=state['pending_sections'],
                schema=prev,
                content=state['search_results'],
            )
        else:
            prompt = self.compilador_prompt_Nsch.format(
                instructions=state['user_notes'],
                report=prev,
                content=state['search_results'],
            )
        result = await self.model.ainvoke(prompt)
        writer({"custom_key": " End of data compilation."})
        return {"info_compilada": result.content}

    async def reflection(self, state: WebAgentState, writer: StreamWriter) -> dict[str, Any]:
        writer({"custom_key": " Reflecting on data ..."})
        if state["extraction_schema"]:
            struc = self.model.with_structured_output(Reflection)
            prompt = self.reflection_prompt.format(
                schema=state['extraction_schema'],
                content=state['info_compilada'],
                company=state['company'],
                user_notes=state['user_notes'],
            )
        else:
            struc = self.model.with_structured_output(Reflection_Nsch)
            prompt = self.reflection_prompt_Nsch.format(
                content=state['info_compilada'],
                instructions=state['user_notes'],
            )
        reflection = await struc.ainvoke(prompt)
        if reflection.is_answered:
            return {"is_complete": True}
        return {
            "user_notes": reflection.analysis,
            "is_complete": False,
            "iteraciones": state['iteraciones'] + 1,
            "pending_sections": reflection.pending_sections,
        }

    def conditional_reflection(self, state: WebAgentState, writer: StreamWriter) -> bool:
        if state["is_complete"] or state["iteraciones"] >= max_iteraciones:
            writer({"custom_key": f" Report complete - iterations: {state['iteraciones']}"})
            writer({"web_key": f"{state['info_compilada']}"})
            return True
        writer({"custom_key": f" Let's keep researching! - iter {state['iteraciones']}"})
        return False

async def main(llm, company: str, schema: str, instructions: str = "") -> str:
    
    agent = WebSearchAgent(llm)
    sections = "description,history,business,market,people,capital_allocation" if schema else ""
    state = WebAgentState(
        company=company,
        extraction_schema=schema,
        user_notes=instructions,
        pending_sections=sections,
        queries=[],
        search_results=[],
        info_compilada=[],
        is_complete=False,
        iteraciones=0
    )

    final_chunk = None
    async for chunk in agent.graph.astream(state, stream_mode="custom"):
        if "final_key" in chunk:
            final_chunk = chunk
        # else:
            # print(chunk)

    result_str = list(final_chunk['final_key'])[0]
    clean = extract_clean_text(result_str)
    print("\n=== RESULT ===\n")

    return clean

if __name__ == "__main__":
    api_key = os.getenv("OPENAI_API_KEY")
    schema = ESQUEMA
    instructions = ""
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=api_key,
        temperature=0,
        max_tokens=10000,
        streaming=True
    )
    clean = asyncio.run(main(llm, "Apple", schema, instructions))
    print(clean)
