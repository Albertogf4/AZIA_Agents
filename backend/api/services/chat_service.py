from .agents.web_search_agent_utils import extract_clean_text
from .agents.global_agents     import GlobalAgent

from langchain_openai import ChatOpenAI
import os
import asyncio
from langchain.schema import HumanMessage, AIMessage

class ChatService:
    def __init__(self):
        # 1) Configuramos el LLM
        openai_key = os.getenv("OPENAI_API_KEY", "")
        # Características del razonamiento
        reasoning = {
            "effort": "low",  # 'low', 'medium', or 'high'
            "summary": "auto",  # 'detailed', 'auto', or None
        }
        self.llm = ChatOpenAI(
            model_name="gpt-4.1-mini-2025-04-14",
            api_key=openai_key,
            temperature=0.1,
            max_tokens=5000,
        )
        self.llm_reasoning = ChatOpenAI(
            model_name="o4-mini-2025-04-16",
            use_responses_api=True,
            model_kwargs={"reasoning": reasoning},
            api_key=openai_key,
            max_tokens=25000,
        )
        # 2) Instanciamos nuestro agente global
        self.global_agent = GlobalAgent(model=self.llm, reasoning_model=self.llm_reasoning)


    def process_query(self, message):
        return {
            "status": "success",
            "response": f"Received: {message}"
        }

    def process_query_with_schema(self, message, schema):
        return {
            "status": "success",
            "response": f"Received: {message} with schema: {schema}"
        }
    
    def process_query_global_agent(self, message, conversation_id, schema=None, rag_only=False, web_only=False):
        # 3) Preparamos el estado inicial y la config del grafo
        state = {
            "messages": [ HumanMessage(content=message) ],
            "conversation_id": conversation_id
        }
        # 
        config = {
            "configurable": {
                "thread_id": conversation_id
            }
        }
        """
        async def _run():
            last_resp = "Lo siento, no obtuve respuesta."
            # 4) Iteramos por todos los chunks del stream
            async for chunk in self.global_agent.graph.astream(
                state,
                config,
                stream_mode="custom"
            ):
                print("🔍 CHUNK:", chunk)
                # el grafo va emitiendo dicts; el chunk final contiene "messages"
                if chunk.get("final_key"):
                    print("🔍 FINAL KEY OBTAINED")
                    # Necesitamos actualizar el estado del grafo con el mensaje final para futuros mensajes
                    # Ahora mismo se está guardando: 🔍 Local database:\\n
                    
                    last_resp = chunk["final_key"]
                    # self.global_agent.graph.update_state(config, {"messages": [AIMessage(content=last_resp)]})
               
            return last_resp
        """
        async def _run_2(rag_only=False, web_only=False):
            last_resp = "Lo siento, no obtuve respuesta."
            # 4) Iteramos por todos los chunks del stream
           
            last_resp = await self.global_agent.run(message, config, schema, rag_only, web_only) 
            #if last_resp.startswith("```") or "<schema_to_complete>" in last_resp:
            #            last_resp = extract_clean_text(last_resp)    
            return last_resp
        # 5) Ejecutamos el coroutine y devolvemos el resultado
        respuesta = asyncio.run(_run_2(rag_only, web_only))
        print("🔍 RESPUESTA ENVIADA:", respuesta)
        return {
            "status": "success",
            "response": respuesta
        }
    
