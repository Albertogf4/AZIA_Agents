from typing import Annotated, TypedDict, List, cast
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
import asyncio
import os

from langgraph.types import StreamWriter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from services.agents.asyncwebsearch import WebAgentState, WebSearchAgent
from services.agents.web_search_agent_utils import extract_clean_text, ESQUEMA, ESQUEMA_MD
from services.agents.rag_agents import AgentState, RagAgent
from services.agents.global_agent_utils import prompt_plan, prompt_final, plan_prompt_rag, plan_prompt_web

# -------------------------------
# 0. Schema de salida para el plan #@TODO: Quitar defaults
# -------------------------------
class HandOff(BaseModel):
    LocalAgent: bool = Field(description="Whether to use the RAG agent")
    WebAgent: bool = Field(description="Whether to use the Web Search agent")
    response: str = Field(default="",description="Response from the agent to the user's question if no handoff is needed (LocalAgent=False, WebAgent=False)")
    instructions_rag : str = Field(default="",description="Instructions that the RAG agent should follow")
    instructions_web : str = Field(default="",description="Instructions that the Web Search agent should follow")
    company: str = Field(default="",description="Company name to be used in the web search")

class HandOffRAG(BaseModel):
    LocalAgent: bool = Field(description="Whether to use the RAG agent")
    instructions_rag : str = Field(default="",description="Instructions that the RAG agent should follow")
    response: str = Field(default="",description="Response from the agent to the user's question if no handoff is needed (LocalAgent=False)")
    company: str = Field(default="",description="Company name to be used in the web search")

class HandOffWeb(BaseModel):
    WebAgent: bool = Field(description="Whether to use the Web Search agent or respond directly")
    instructions_web : str = Field(default="",description="Instructions that the Web Search agent should follow")
    response: str = Field(default="",description="Response from the agent to the user's question if no handoff is needed (WebAgent=False)")
    company: str = Field(default="",description="Company name to be used in the web search")
    
# -------------------------------
# 1. Definición del estado del agente
# -------------------------------
class GlobalAgentState(TypedDict):
    # Historial de mensajes (HumanMessage y AIMessage)
    messages: Annotated[List[BaseMessage], add_messages]
    # ambos: bool 
    web: bool 
    rag: bool
    response: str
    instructions_rag: str 
    instructions_web: str 
    conversation_id: str 
    schema: str
    company: str



# -------------------------------
# 3. Clase del agente con memoria
# -------------------------------
class GlobalAgent:
    def __init__(
        self,
        model: ChatOpenAI,
        reasoning_model: ChatOpenAI,
    ): 
        self.MAX_ITERACIONES = 2
        self.MAX_ITERACIONES_RETRIEVAL = 2
        self.model = model
        self.reasoning_model = reasoning_model
        self.memory = MemorySaver()

        self.plan_prompt = prompt_plan
        self.final_prompt = prompt_final
        self.plan_prompt_rag = plan_prompt_rag
        self.plan_prompt_web = plan_prompt_web

        # base_dir = os.path.dirname(os.path.abspath(__file__))
        # persist_dir = os.path.join(base_dir, "vectorstore_chromadb_automatic")
        # os.makedirs(persist_dir, exist_ok=True)

        embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"), model="text-embedding-3-small")
        vectorstore = Chroma(persist_directory="./services/agents/vectorstore_chromadb_automatic", embedding_function=embeddings)
        # llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
        self.rag_agent = RagAgent(self.model, vectorstore, max_iteraciones=self.MAX_ITERACIONES, max_iteraciones_retrieval=self.MAX_ITERACIONES_RETRIEVAL)

        # Construcción del grafo de estados
        graph = StateGraph(GlobalAgentState)
        graph.add_node("plan", self.plan)
        graph.add_node("chat", self.chat)
        graph.add_edge("plan", "chat")
        graph.add_edge("chat", END)
        graph.set_entry_point("plan")

        # Compilar grafo con memoria persistente
        self.graph = graph.compile(checkpointer=self.memory)

    def plan(self, state: GlobalAgentState, writer) -> dict:
        ultimo = state["messages"][-1].content
        historial: List[BaseMessage] = state.get("messages", [])
        # vemos si se llama al agente de rag, web o ambos
        web = state["web"]
        rag = state["rag"]
        instructions_rag = ""
        instructions_web = ""
               
        if not web:
            prompt = self.plan_prompt_rag.format(
                query=ultimo,
                history=historial,
            )
            llm = self.model.with_structured_output(HandOffRAG, method="function_calling")
            result = llm.invoke(prompt)
            handoff = cast(HandOffRAG, result)
            # Se añaden los campos para que tenga el mismo formato que HandOff
            web = False
            rag = handoff.LocalAgent
            instructions_web = ""
            instructions_rag = handoff.instructions_rag
        elif not rag:
            prompt = self.plan_prompt_web.format(
                query=ultimo,
                history=historial,
                schema=state["schema"]
            )
            llm = self.model.with_structured_output(HandOffWeb, method="function_calling")
            result = llm.invoke(prompt)
            handoff = cast(HandOffWeb, result)
            instructions_rag = ""
            instructions_web = handoff.instructions_web
            web = handoff.WebAgent
            rag = False

        else:
            prompt = self.plan_prompt.format(
                query=ultimo,
                history=historial,
            )
            # Utilizaremos un modelo razonador para esta primera fase.
            llm = self.reasoning_model.with_structured_output(HandOff, method="function_calling")
            result = llm.invoke(prompt)
            # Reasoning tokens
            handoff = cast(HandOff, result)
            web = handoff.WebAgent
            rag = handoff.LocalAgent
            instructions_rag = handoff.instructions_rag
            instructions_web = handoff.instructions_web


        writer({"plan_key": f"{web}|||{rag}|||{handoff.response}"})
        print("Intructions RAG:", instructions_rag)
        print("Intructions Web:", instructions_web)
        return {
            #"ambos":            handoff.Both,
            "web":              web,
            "rag":              rag,
            "response":         handoff.response,
            "instructions_rag":  instructions_rag,
            "instructions_web":  instructions_web,
            "company":          handoff.company,
        }

    async def chat(self, state: GlobalAgentState, writer) -> dict:
        """
        Nodo principal: recibe el historial, llama al LLM y añade la respuesta al estado.
        """     
        ultimo_mensaje = state["messages"][-1].content
        historial: List[BaseMessage] = state.get("messages", [])

        writer({"custom_key": f"último mensaje: {ultimo_mensaje}"})
        writer({"custom_key": f"historial: {historial}"})
        
        #ambos = state["ambos"]
        web =  state["web"]
        rag =  state["rag"]
        instructions_rag =  state["instructions_rag"]
        instructions_web = state["instructions_web"]
        response = state["response"]
        company = state["company"]
        schema = state["schema"]
        if web and rag:
            writer({"custom_key": "Lanzando ambos agentes en paralelo..."})

            # 1) Define la coroutine para Web Search
            async def run_web() -> str:
                web_agent = WebSearchAgent(self.model)
                sections = "description,history,business,market,people,capital_allocation" if schema else ""
                state_web = WebAgentState(
                    company=company,
                    extraction_schema=schema,
                    user_notes=instructions_web,
                    pending_sections=sections,
                    queries=[],
                    search_results=[],
                    info_compilada=[],
                    is_complete=False,
                    iteraciones=0
                )
                final_web = None
                async for chunk in web_agent.graph.astream(state_web, stream_mode="custom"):
                    if "final_key" in chunk:
                        final_web = chunk["final_key"]
                        final_web = extract_clean_text(list(final_web)[0])
                return final_web

            # 2) Define la coroutine para RAG
            async def run_rag() -> str:
                state_rag: AgentState = {
                    "user_question": instructions_rag,
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
                final_rag = None
                async for chunk in self.rag_agent.graph.astream(state_rag, {}, stream_mode="custom"):
                    if chunk.get("final_key"):
                        final_rag = chunk["final_key"]
                # final_rag ya es un string con la respuesta del RAG
                return final_rag or "No se obtuvo respuesta del agente RAG"

            # 3) Ejecuta ambas en paralelo
            res_web, res_rag = await asyncio.gather(
                run_web(),
                run_rag(),
            )
            print("🌐res_web:", res_web)
            print("🔍res_rag:", res_rag)
            # 4) Combina las dos salidas en un único AIMessage
            combinado = AIMessage(
                content=(
                    f"🔍 Local database Agent (RAG):\n{res_rag}\n\n"
                    f"🌐 Web search Agent:\n{res_web}"
                )
            )
            if combinado is None:
                combinado = AIMessage(content="No se obtuvo respuesta de los agentes.")
            elif not isinstance(combinado, BaseMessage):
                combinado = AIMessage(content=str(combinado))
            # Devuelves el mensaje combinado al grafo
            return {"messages":  [combinado]}
        elif web:

            writer({"custom_key": "Lanzando Web Search agent..."})
            
            writer({"custom_key": f"--- Mensajes hasta el momento : {state['messages']}"})
            async def main(llm, company: str = "Apple", schema: str = ESQUEMA_MD, instructions: str = "") -> str:
                web_agent = WebSearchAgent(llm)

                state = WebAgentState(
                    company=company,
                    extraction_schema=schema,
                    user_notes=instructions,
                    pending_sections="description,history,business,market,people,capital_allocation",
                    queries=[],
                    search_results=[],
                    info_compilada=[],
                    is_complete=False,
                    iteraciones=0
                )

                final_chunk = None
                async for chunk in web_agent.graph.astream(state, stream_mode="custom"):
                    if "final_key" in chunk:
                        final_chunk = chunk
                    # else:
                        # print(chunk)

                #final_chunk = list(final_chunk['final_key'])[0]
                #final_chunk = extract_clean_text(final_chunk)
                #print("\n=== RESULT ===\n")
                #print(final_chunk)                
                return final_chunk
            res_web = await main(self.model, company, schema, instructions_web)
            if res_web is None:
                res_web = AIMessage(content="No se obtuvo respuesta del agente Web.")
            elif not isinstance(res_web, BaseMessage):
                res_web = AIMessage(content=str(res_web))
            return {"messages": [res_web]}
            #res_web = "Respuesta de la búsqueda web"
            #combinado = AIMessage(content=f"🌐 Web:\n{res_web}")
            #return {"messages": combinado}
        elif rag:
            writer({"custom_key": "Lanzando RAG agent..."})
            writer({"custom_key": f"--- Mensajes hasta el momento : {state['messages']}"})
            #res_rag = await self.rag_chain.arun({"messages": historial})
            print(f"instrucciones rag: {instructions_rag}")
            #res_rag = await self.rag_agent.run(instructions_rag)
            res_rag = "No se obtuvo respuesta del agente RAG"

            embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"), model="text-embedding-3-small")
            vectorstore = Chroma(persist_directory="services/agents/vectorstore_chromadb_automatic", embedding_function=embeddings)

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
            res_rag = await run(instructions_rag, self.model, vectorstore, max_iteraciones=self.MAX_ITERACIONES, max_iteraciones_retrieval=self.MAX_ITERACIONES_RETRIEVAL)
            res_rag = AIMessage(content=res_rag)  
            if res_rag is None:
                res_rag = AIMessage(content="No se obtuvo respuesta del agente RAG.")
            elif not isinstance(res_rag, BaseMessage):
                res_rag = AIMessage(content=str(res_rag))
            print("🔍res_rag obtained inside chat():", res_rag)    
            return {"messages": [res_rag]}
        else:
            print("No se necesita acudir a ningún otro agente.")
            writer({"custom_key": "No se necesita acudir a ningún otro agente."})
            writer({"custom_key": f"--- Mensajes hasta el momento : {state['messages']}"})
            writer({"final_key": f"{response}"})
            combinado = AIMessage(content=response)
            if res_rag is None:
                res_rag = AIMessage(content="No se obtuvo respuesta del agente RAG.")
            elif not isinstance(res_rag, BaseMessage):
                res_rag = AIMessage(content=str(res_rag))
            return {"messages": [combinado]}

        # historial.append(combinado)
        
    
    async def run(self, question: str, config: dict, schema: str, rag_only=False, web_only=False) -> str:
        # Estado inicial
        state: GlobalAgentState = {
            "messages": [ HumanMessage(content=question) ],
            "web": web_only,
            "rag": rag_only,
            "response": "",
            "instructions_rag": "",
            "instructions_web": "",
            "conversation_id": "",
            "schema": schema,
            "company":"",
        }
        rag_chunk = ""
        web_chunk = ""
        async for chunk in self.graph.astream(state, config, stream_mode="custom"):
            print("🔍 CHUNK in global:", chunk)

            if chunk.get("plan_key"):
                print("🔍 PLAN KEY OBTAINED IN Global agent")
                plan = chunk["plan_key"]
                web, rag, response = plan.split("|||")
                web = web == "True"
                rag = rag == "True"

            if web and rag:
                print("🔍 BOTH AGENTS SELECTED")
                if chunk.get("web_key"):
                    web_chunk = chunk["web_key"]
                    # Detectar si hace falta usar extract_clean_text() por el formato
                    if web_chunk.startswith("```") or "<schema_to_complete>" in web_chunk:
                        web_chunk = extract_clean_text(web_chunk)
                if chunk.get("rag_key"):
                    rag_chunk = chunk["rag_key"]
                
                if rag_chunk != "" and web_chunk != "":
                    print(
                        f"🔍 Local database Agent (RAG):\n{rag_chunk}\n\n"
                        f"🌐 Web search Agent:\n{web_chunk}"
                )
                    response_final = f"🔍 Local database Agent (RAG):\n{rag_chunk}\n\n 🌐 Web search Agent:\n{web_chunk}"

                    prompt_res = self.final_prompt.format(
                        query=question,
                        rag_chunk=rag_chunk,
                        web_chunk=web_chunk,
                    )
                    result = self.model.invoke(prompt_res)
                    if isinstance(result, AIMessage):
                        final_result = result.content
                    else:
                        final_result = result
                    if final_result.startswith("```") or "<schema_to_complete>" in final_result:
                        final_result = extract_clean_text(final_result)
                    print("🔍🌐 FINAL RESULT:", final_result)
                    self.graph.update_state(config, {"messages": [AIMessage(content=final_result)]})
                    if final_result is None:
                        final_result = "No se obtuvo respuesta final."
                    return final_result

            elif web:
                print("🔍 WEB AGENT SELECTED")
                if chunk.get("web_key"):
                    final_chunk = chunk["web_key"]
                    if final_chunk.startswith("```") or "<schema_to_complete>" in final_chunk:
                        final_chunk = extract_clean_text(final_chunk)
                    if final_chunk is None:
                        final_chunk = "No se obtuvo respuesta del agente Web."
                    self.graph.update_state(config, {"messages": [AIMessage(content=final_chunk)]})
                    return final_chunk
            elif rag:
                print("🔍 RAG AGENT SELECTED")
                if chunk.get("rag_key"):
                    final_chunk = chunk["rag_key"]
                    if final_chunk.startswith("```") or "<schema_to_complete>" in final_chunk:
                        final_chunk = extract_clean_text(final_chunk)
                    # Detectar si hace falta usar extract_clean_text() por el formato
                    print("🔍 FINAL KEY CHUNK:", final_chunk)
                    if final_chunk is None:
                        final_chunk = "No se obtuvo respuesta del agente RAG."
                    self.graph.update_state(config, {"messages": [AIMessage(content=final_chunk)]})
                    return final_chunk
            else:
                print("🔍 NO AGENT SELECTED")
                if response is None:
                    response = "No se obtuvo respuesta."
                self.graph.update_state(config, {"messages": [AIMessage(content=response)]})
                return response
        """
        async for chunk in self.graph.astream(state, config, stream_mode="custom"):
            print("🔍 CHUNK in global:", chunk)
            # print(chunk)
            res= "No obtuve respuesta."
            if chunk.get("final_key"):
                print("🔍 FINAL KEY OBTAINED IN Global agent")
                final_chunk = chunk["final_key"]
                # Detectar si hace falta usar extract_clean_text() por el formato
                if final_chunk.startswith("```") or "<schema_to_complete>" in final_chunk:
                    final_chunk = extract_clean_text(final_chunk)

                print("🔍 FINAL KEY CHUNK:", final_chunk)
                
                self.graph.update_state(config, {"messages": [AIMessage(content=final_chunk)]})
                return final_chunk
        #return state["response"]
        
        return res
        """
if __name__ == "__main__":
    import os
    openai_api_key = os.getenv("OPENAI_API_KEY")
    agent = GlobalAgent(model = ChatOpenAI(model="gpt-4.1-mini-2025-04-14", api_key=openai_api_key, temperature=0, max_tokens=3000) )
    thread_id = "usuario123"
    # Primer input
    state = {"messages": [HumanMessage(content="Hello! I'm Álvaro, search for information about Logista's performance in 2023 in the local database.")]}
    config = {"configurable": {"thread_id": thread_id}}


    async def main():
        async for chunk in agent.graph.astream(state, config, stream_mode="custom"):
            print(chunk)

    asyncio.run(main())