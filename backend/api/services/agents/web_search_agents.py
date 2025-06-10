import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from dataclasses import field, dataclass
from typing import TypedDict, Annotated, Any
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
import operator
from pydantic import BaseModel, Field
from typing import List
import json
from langgraph.graph import StateGraph, END
from typing import cast
import asyncio
from services.agents.web_search_agent_utils import QUERY_PROMPT, NOTES_PROMPT, COMPILER_PROMPT, REFLECTION_PROMPT, extract_clean_text

from tavily import TavilyClient
import time
from langgraph.types import StreamWriter
# from utils import parse_json


from langchain_community.tools.tavily_search import TavilySearchResults

_ = load_dotenv()

tavily_api_key = os.getenv("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=tavily_api_key)

ESQUEMA="""
    ### Company_name: company name,
    ### Description: brief description of the company.
    ### History: Most important milestones, aquisitions, results from last years.
    ### Business: Understand what it does, possible entry barriers or competitive advantages. Who are its suppliers and customers.
    ### Market: Who it competes with and what are its market shares.
    ### People: Board of directors, management, and shareholders, who are they? How much does the management team earn and what are their incentives based on.
    ### Capital_allocation: Analysis of M&A, money allocated to dividends, share buybacks or issuance.
"""

# Agent State
#@dataclass(kw_only=True)
class WebAgentState(TypedDict):
    """Información disponible en todo momento, con Annotated se pueden agregar metadatos sin perder información anterior"""
    company: str 

    extraction_schema: dict[str, Any] = field(
        default_factory=lambda: ESQUEMA
    )

    # indicaciones extra del usuario
    user_notes: str = field(default=None)

    # Búsquedas necesarias a hacer
    pending_sections: list[str] = field(default="description,history,business,market,people,capital_allocation")

    # queries
    queries: list[str] = field(default=None)
    
    # Search results de todas las queries
    search_results: list[dict[str, Any]] = field(default=None)

    # Información compilada
    info_compilada: str = field(default_factory=list)

    #Está toda la información completa
    is_complete: bool = field(default=False)

    # Número de iteraciones
    iteraciones: int = field(default=0)    

def generate_json_schema(num_queries: int) -> dict:
    queries = {f"query_{i+1}": {"type": "string", "description": f"Search query text {i+1}"} for i in range(num_queries)}
    return {
        "title": "queries",
        "description": "Search queries",
        "type": "object",
        "properties": {"queries": queries},
        "required": ["queries"]
    }

class Reflection(BaseModel): # Para la salida del nodo de reflection
    """Reflection del informe redactado"""
    is_answered: bool = Field(description="True if the schema is complete, False if there are any sections unknown or incomplete")
    pending_sections: str = Field(description="List of pending or incomplete sections to search for, set to None if there are none, separate sections with commas")
    analysis: str = Field(description="Clearly specify what is missing and what to focus on next queries inside those pending sections")


# Parámetros Config @TODO: externalizar
max_iteraciones = 3 # 3
max_search_results = 3 # 3
max_search_queries = 6 # 6

class WebSearchAgent:
    def __init__(self, model):
        # Prompts
        self.query_prompt = QUERY_PROMPT
        self.notes_prompt = NOTES_PROMPT
        self.compilador_prompt = COMPILER_PROMPT
        self.reflection_prompt = REFLECTION_PROMPT
        # urls
        self.urls = []
        # Graph
        graph = StateGraph(WebAgentState)
        # Nodos
        graph.add_node("gen_query", self.query_generation)
        graph.add_node("buscar", self.busqueda)
        graph.add_node("compilador", self.compilador)
        graph.add_node("reflection", self.reflection)
        # Edges/Aristas
        graph.add_edge("gen_query", "buscar")        
        graph.add_edge("buscar", "compilador")
        graph.add_edge("compilador", "reflection")
        graph.add_conditional_edges(
            "reflection", 
            self.conditional_reflection, 
            {True: END, False: "gen_query"}
        )
        # Graph
        graph.set_entry_point("gen_query")
        self.graph = graph.compile()
        # tools
        #self.tools = {t.name: t for t in tools}
        # Model
        self.model = model# .bind_tools(tools)
        self.debugging = False

    def query_generation(self, state: WebAgentState, writer : StreamWriter ) -> dict[str, Any]:
        """Genera queries a partir de la petición y el esquema proporcionado"""
        #print(f"[AzvalorAgent] Generating queries for iteration {state['iteraciones']} ")
        writer({"custom_key": f" Generating queries for iteration {state['iteraciones'] +1} ..."})

        lista_pending_sections = state["pending_sections"].split(",") if state["pending_sections"] else []
        if(lista_pending_sections):
            input = self.query_prompt.format(
                schema=state["extraction_schema"], 
                company=state["company"],
                user_notes=state["user_notes"],
                max_search_queries=len(lista_pending_sections),
                pending_sections=lista_pending_sections,
                past_queries=state["queries"],
            )
            if self.debugging: print(f"[AzvalorAgent] Past generated queries: {state['queries']} ")
            json_schema = generate_json_schema(len(lista_pending_sections))
        else: 
            input = self.query_prompt.format(
                schema=state["extraction_schema"],
                company=state["company"],
                user_notes=state["user_notes"],
                max_search_queries=max_search_queries,
                pending_sections=lista_pending_sections,
                past_queries=""
            )
            json_schema = generate_json_schema(max_search_queries)

        strutured_llm = self.model.with_structured_output(json_schema)
        # Generar queries con la clase QueriesFormat
        response = strutured_llm.invoke(input) 
        #print(f"[AzvalorAgent] Queries generated: {response['queries']}")
        # Recuperar la lista de queries generadas
        # lista_queries = [query['query'] for query in response['queries']]
        lista_queries = list(response['queries'].values())
        #print(f"#### lista_queries:{lista_queries} ####")
        if self.debugging: print(f"[AzvalorAgent] End of query generation number {state['iteraciones']} ")
        writer({"custom_key": f" End of query generation number {state['iteraciones'] +1}."})
        return {"queries": lista_queries}
    
    def busqueda(self, state: WebAgentState, writer: StreamWriter) -> dict[str, Any]:
        """Realiza la búsqueda de información a partir de las queries generadas"""
        # Recuperamos las queries
        if self.debugging: print(f"#### Iniciando búsqueda numero {state['iteraciones']} ####")
        writer({"custom_key": f" Launching web search number {state['iteraciones'] +1} ..."})
        lista_pending_sections = state["pending_sections"].split(",") if state["pending_sections"] else []
        num = len(lista_pending_sections)
        if lista_pending_sections:
            queries = state['queries'][-num:]
        else:
            queries = state['queries']
        searches_results = []
        if self.debugging: print(f"[AzvalorAgent] Obtaining data results ... ")
        for query in queries:
            # print(f"[AzvalorAgent] query:{query}")
            # Búsqueda sincrónica
            response = tavily_client.search(query=query,
                                            #include_raw_content=True,
                                            max_results=max_search_results,
                                            #search_depth="advanced",
                                            include_images=False,
                                            include_answer=False,
                            )  
            results = response['results']
            #response_time = response['response_time']
            search_results = []
            
            for _, result in enumerate(results):
                #title = result['title']
                self.urls.append(result['url']) #@TODO: incluir url a fuentes
                content = result['content']
                #score = result['score']
                #raw_content = result['raw_content']
                search_results.append(content)    
            searches_results.append(search_results)
        
        if self.debugging: print(f"[AzvalorAgent] Data results obtained ... ")
        if self.debugging: print(f"[AzvalorAgent] search_results:{searches_results}")
        # Generar texto estructurado para el compilador
        p = self.notes_prompt.format(
            company=state["company"],
            schema=state["extraction_schema"], 
            content=searches_results,
        )
        result = self.model.invoke(p)
        if self.debugging: print(f"[AzvalorAgent] Summary of results:{result}")
        notes_results = result.content
        writer({"custom_key": f" Successfully received and extracted web search results!"})
        return {"search_results": notes_results}
    
    # Es importante mantenener estas funciones separadas para cuando se recorra el grafo
    def compilador(self, state: WebAgentState, writer: StreamWriter) -> dict[str, Any]:
        """Compila la información extraída de la búsqueda y la estructura a medida del esquema"""
        writer({"custom_key": f" Compiling data and web information ..."})
        # Recuperamos los resultados de la búsqueda
        search_results = state['search_results']
        # Recuperamos la información compilada de anteriores iteraciones
        info_compilada_ant = state["extraction_schema"] if state["iteraciones"]==0 else state['info_compilada']
        # Generar texto estructurado para el compilador
        p = self.compilador_prompt.format(
            pending_sections=state["pending_sections"],
            schema= info_compilada_ant,
            content=search_results,
        )
        result = self.model.invoke(p)
        #print(f"[AzvalorAgent] Compiled version number {state['iteraciones']}: {result}")
        writer({"custom_key": f" End of data compilation ..."})
        return {"info_compilada": result.content}
    
    def reflection(self, state: WebAgentState, writer: StreamWriter) -> dict[str, Any]:
        writer({"custom_key": f" Reflecting on the compiled data ..."})
        # Recuperamos la información compilada
        info_compilada = state['info_compilada']
        # Estructurar salida 
        strutured_llm = self.model.with_structured_output(Reflection)
        # Generar texto estructurado para el reflection
        p = self.reflection_prompt.format(
            schema=state["extraction_schema"],
            content=info_compilada,
            company=state["company"],
            user_notes=state["user_notes"],
        )
        
        result = cast(Reflection, strutured_llm.invoke(p))
        #print(f"[AzvalorAgent] Reflection analysis: {result["is_answered"]} ---- analysis:{result["analysis"]} ---- pending_sections:{result["pending_sections"]}")
        
        if result.is_answered:
            return {"is_complete": result.is_answered}
        else:
             return {
                "user_notes": result.analysis,
                "is_complete": result.is_answered,
                "iteraciones": state["iteraciones"] + 1,
                "pending_sections": result.pending_sections,
            }

    def conditional_reflection(self, state: WebAgentState, writer: StreamWriter) -> bool:
        if state["is_complete"]:
            writer({"custom_key": f" Report complete - iterations: {state['iteraciones']}"})
            if self.debugging: print(f"[AzvalorAgent] Report complete - iterations: {state["iteraciones"]}")
            writer({"final_key": {state['info_compilada']}})
            return True
        if state["iteraciones"] < max_iteraciones:
            writer({"custom_key": f"Let's keep researching! - iterations:{state['iteraciones']}"})
            if self.debugging: print(f"[AzvalorAgent] Let's keep researching! - iterations:{state["iteraciones"]}")
            return False
        writer({"custom_key": f" Report complete - iterations: {state['iteraciones']}"})
        writer({"final_key": {state['info_compilada']}})
        return True 






if __name__ == "__main__": 
    api_key = os.getenv("OPENAI_API_KEY")

    llm_model = ChatOpenAI(model="gpt-4o-mini", api_key=api_key, temperature=0, max_tokens=10000)  
    abot = WebSearchAgent(llm_model)

    company_name = input("Enter the company name you wish to analyze: ")
    
    state = WebAgentState(company=company_name, extraction_schema=ESQUEMA, user_notes="", pending_sections=[], queries=[], search_results=[], info_compilada=[], is_complete=False, iteraciones=0) 
    #result = abot.graph.invoke(state)
    
    final_result = None
    for chunk in abot.graph.stream(state, stream_mode="custom"):
        if chunk.get("final_key", False):
            final_result = chunk
        else:
            print(chunk)
    final_key_str = list(final_result['final_key'])[0]
    clean_response = extract_clean_text(final_key_str)
    print(clean_response)

    # print(f"#### urls:{abot.urls}")
    # parse_json(result['info_compilada'])
    # Ejemplo de uso interactivo
    print("\n--- WebSearchAgent demo ---")
    print("Introduce el nombre de una empresa para analizarla (o pulsa Enter para salir):")
    while True:
        company_name = input("> ").strip()
        if not company_name:
            print("Saliendo.")
            break
        state = WebAgentState(
            company=company_name,
            extraction_schema=ESQUEMA,
            user_notes="",
            pending_sections="description,history,business,market,people,capital_allocation",
            queries=[],
            search_results=[],
            info_compilada=[],
            is_complete=False,
            iteraciones=0
        )
        final_result = None
        print(f"Analizando {company_name}...\n")
        for chunk in abot.graph.stream(state, stream_mode="custom"):
            if chunk.get("final_key", False):
                final_result = chunk
            else:
                print(chunk.get("custom_key", ""))
        if final_result:
            final_key_str = list(final_result['final_key'])[0]
            clean_response = extract_clean_text(final_key_str)
            print("\n--- Informe final ---\n")
            print(clean_response)
        print("\nIntroduce otra empresa o pulsa Enter para salir:")


"""
if __name__ == "__main__":
    company = "Apple Inc."  # Example company name
    schema = ESQUEMA  # Example schema
    state = AgentState(
        company=company,
        extraction_schema=schema,
        user_notes="",
        pending_sections="description,history,business,market,people,capital_allocation",
        queries=[],
        search_results=[],
        info_compilada=[],
        is_complete=False,
        iteraciones=0
    )

    def generate():
        final_result = None
        for chunk in agent.graph.stream(state, stream_mode="custom"):
            if chunk.get("final_key", False):
                final_result = chunk
            else:
                # print(chunk)
                formatted_chunk = {
                    "text": chunk.get("custom_key", ""),  
                    "icon": "Bot"  # icons based on the chunk type
                }
                yield f"data:{json.dumps(formatted_chunk)}\n\n"
            time.sleep(0.5)
            # if chunk.get("is_final", False): # Send a final message
        final_key_str = list(final_result['final_key'])[0]
        clean_response = extract_clean_text(final_key_str)
        yield f"data:{json.dumps({'text': clean_response, 'isFinal': True})}\n\n"

            
        
        # yield f"data:{json.dumps({'text': state['info_compilada'], 'isFinal': True})}\n\n"
    
        return Response(generate(), mimetype="text/event-stream")
"""