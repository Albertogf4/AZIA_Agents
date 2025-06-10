from pydantic import BaseModel, Field
class Queries(BaseModel): # Para la salida del nodo de query_expansion
    """Query para la búsqueda de información"""
    queries: list[str] = Field(description="List of queries to be used for information retrieval")
    #thoughts: str = Field(description="Thoughts about the queries created and what are you targetting with them")

class ReflectionDocs(BaseModel):  # Para la salida del nodo de reflection_docs
    """Reflexión sobre los documentos recuperados"""
    id_relevant_docs: list[int] = Field(description="List of ids only from the relevant documents extracted from the retrieved documents")
    thoughts: str = Field(default="", description="Thoughts about the missing information in the report and suggestions to improve it")

class ReflectionCompleteness(BaseModel): # Para la salida del nodo de reflection_docs
    """Reflexión sobre la completitud de la respuesta generada"""
    is_complete: bool = Field(description="Indicates if the generated report is complete and answers the question or not, True if it is complete, False otherwise")
    thoughts: str = Field(default="",description="Thoughts about the missing information in the report and suggestions to improve it")



import re

def id_agregator(documentos,  id_inicial=1):
    # Aplanar la lista, hay sublistas por el query expansion
    documentos_planos = []
    for item in documentos:
        if isinstance(item, list):
            documentos_planos.extend(item)
        else:
            documentos_planos.append(item)
    
    # Asignar ids 
    for indice, documento in enumerate(documentos_planos, start=id_inicial):
        documento.metadata['id'] = indice
    
    return documentos_planos

def filtrar_documentos_por_ids(lista_ids, lista_documentos):
    # Se filtran los documentos cuyo metadata 'id' se encuentra en la lista_ids
    return [doc for doc in lista_documentos if doc.metadata.get('id') in lista_ids]

def get_icon(chunk):
    txt = chunk.get("custom_key", "")
    if txt.startswith("Generating") or txt.startswith("Let's"):
        return "Bot"
    elif txt.startswith("Retrieved") or txt.startswith("Reflection") or txt.startswith("Retrieval"):
        return "Done"
    elif txt.startswith("Report"):
        return "SuperDone"
    elif txt.startswith("Retrieving") :
        return "Search"
    elif txt.startswith("Planning") or txt.startswith("Reflecting"):
        return "Brain"

def results_to_string(retrieved_results):
    return "\n\n".join([f"Retrieved chunk: {result.page_content}" for result in retrieved_results])

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

QUERY_EXPANSION_PROMPT = """
You are a company information research assistant.  \
your task is to formulate queries that will be used to retrieve relevant \
information from a text knowledge base. Your queries should be specific and focused on the information \
that is needed.  \
Enhance this queries knowing they will be used to retrieve relevant information \
directly with RAG on a vectordatabase, \
create the queries in order to maximize relevant information to answer the query. \
Do not repeat queries by changing words but generate different queries that look for different approaches to answer the question \
The knowledge base is a collection of documents that contain information about the company, \
its products, services, and other relevant topics. 
When requested to compare multiple years, query for each year separately the information needed. 
Do not generate more than 2 queries per year. 

Example: 
user request example: "What was the company's revenue from 2022 to 2024? Look in the local files"
generated queries example: ["2022 revenue", "2022 sales figures",  "2023 revenue", "2023 sales figures", "2024 revenue", "2024 sales figures"]

The user request is: {question}
Create a list of queries, each one has to be different enough to complement each other and make use of keywords in the queries. \
"""
QUERY_EXPANSION_PROMPT_2 = """
You are a company information research assistant. Formulate queries that will be used to retrieve relevant \
information from a text knowledge base. Your queries should be specific and focused on the information \
that is needed. 
Enhance this queries knowing they will be used to retrieve relevant information \
with the use of RAG and a vectordatabase, \
create the queries in order to maximize relevant information to answer the query. \
The knowledge base is a collection of documents that contain information about the company, \
its products, services, and other relevant topics.
When requested to compare multiple years, query for each year separately the information needed.
Do not generate more than 2 queries per year. 

The user request is: {question}
Consider not repeating the previous queries, assume you have the knowledge about them: {previous_queries}
Also, consider the following thoughts for the query generation: {thoughts}
Create a list of queries ranged between 2 and 5, each one has to be different enough to compliment each other and make use of keywords in the queries. \
"""

REFLECTION_DOCS_PROMPT ="""
You are an expert financial analysis assistant. 
You are provided with a user input and a list of retrieved documents containing financial reports.\
Your job is to act purely as a filter: \
carefully review the retrieved documents and return only the ids of the documents that directly address or \
provide relevant context to the user's input. 

User Input: {user_input}

Retrieved Documents: {retrieved_documents}

Return only those ids which provide clear and directly applicable financial insights, metrics, or analysis that are relevant to the user's query.
"""


REPORT_GENERATION_PROMPT = """
You are a seasoned financial analyst with deep expertise in evaluating company performance. \
Your task is to generate a comprehensive and evidence-based response to the user's inquiry, using exclusively the information extracted from the retrieved documents provided below.

User Question: {user_input}

Retrieved Documents: {retrieved_documents}

Using advanced analysis, synthesize the key financial insights, metrics, and contextual details from these documents. Ensure that your response:
- Directly addresses the user's query with clear, actionable insights.
- Integrates evidence from the retrieved documents without introducing external information.
- Is well-structured, thorough, and precise.

Generate your answer in a manner that reflects expert financial reasoning and rigorous analysis, include comparative tables when posible. Output a markdown-formatted report.
"""


REFLECTION_COMPLETENESS_PROMPT = """
You are a seasoned financial analysis expert. Given the user's question: 
"{user_input}" and the generated report: 

{generated_report}

Your task is to evaluate whether the report fully answers the user's query. Consider the following:

- Relevance: Does the report provide key financial insights and data relevant to the question?
- Completeness: Are all aspects of the query addressed with sufficient detail?
- Accuracy: Are any financial metrics or analysis logical and consistent with industry practices?

Return a concise judgment: "True" if the report fully satisfies the query, or "False" if significant elements are missing, alongside comments for a follow-up research if needed.
"""
