import json
import os
from langchain.schema import Document
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
import nest_asyncio
from llama_parse import LlamaParse
from dotenv import load_dotenv
import re

# Api keys
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Función para dividir el texto en chunks, con opción de solape entre chunks
def chunk_text(text, chunk_size=1000, overlap=0):
    if overlap >= chunk_size:
        raise ValueError("El solape no puede ser mayor o igual al tamaño del chunk.")
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap 
    return chunks
## Custom Chunking:
"""
Divide el documento en secciones (buscando líneas que empiezan con #).

Dentro de cada sección, detecta primero los bloques de tabla (líneas que comienzan con |) y los mantiene completos, y luego agrupa los párrafos (texto separado por líneas vacías).

Construye cada chunk intentando acercarse a 1000 caracteres (tolerancia ±150). Para ello:

Añade bloque a bloque (párrafo o tabla) mientras no supere los 1150 caracteres.

Si al llegar al siguiente bloque estamos por debajo de 850 caracteres, lo incluye de todas formas (para no dejar chunks demasiado pequeños).

Si no, cierra el chunk actual y arranca uno nuevo.
"""


def split_sections(text):
    """
    Divide the text into sections based on Markdown headings (#).
    """
    lines = text.splitlines()
    sections = []
    current = []
    
    for line in lines:
        if re.match(r'#{1,6}\s', line):  # Si la línea es un encabezado Markdown (# ...).
            if current:
                sections.append('\n'.join(current).strip())
            current = [line]
        else:
            current.append(line)
    
    if current:
        sections.append('\n'.join(current).strip())
    
    return sections

def split_paragraphs_and_tables(section):
    """
    Dentro de cada sección, divide en "bloques": 
    - Tablas: líneas consecutivas que empiezan con '|'
    - Párrafos: bloques de texto separados por línea en blanco
    """
    lines = section.split('\n')
    blocks = []
    i = 0
    n = len(lines)
    
    while i < n:
        # Si la línea inicia con '|', agrupa todas las líneas de tabla consecutivas
        if lines[i].startswith('|'):
            tbl_lines = []
            while i < n and lines[i].startswith('|'):
                tbl_lines.append(lines[i])
                i += 1
            blocks.append('\n'.join(tbl_lines).strip())
        
        else:
            # Agrupa todas las líneas hasta un salto de línea (línea vacía) o inicio de tabla
            para_lines = []
            while i < n and lines[i].strip() != '' and not lines[i].startswith('|'):
                para_lines.append(lines[i])
                i += 1
            blocks.append('\n'.join(para_lines).strip())
            # Saltar líneas vacías
            while i < n and lines[i].strip() == '':
                i += 1
    
    # Filtrar bloques vacíos
    return [b for b in blocks if b.strip()]

def split_chunks(sections, target=1000, tol=150):
    """
    Crea chunks que intentan tener cerca de `target` caracteres, 
    permitiendo una tolerancia de +/- `tol`, 
    sin cortar párrafos ni tablas.
    """
    lower = target - tol
    upper = target + tol
    chunks = []
    
    for sec in sections:
        blocks = split_paragraphs_and_tables(sec)
        current = ""
        
        for b in blocks:
            if not current:
                current = b
            else:
                candidate_length = len(current) + 2 + len(b)  # +2 para "\n\n"
                # Si al añadir el bloque no excede el límite superior
                if candidate_length <= upper:
                    current = current + "\n\n" + b
                else:
                    # Si el tamaño actual está por debajo del umbral inferior, 
                    # agrégalo de todas formas para acercarnos al objetivo
                    if len(current) < lower:
                        current = current + "\n\n" + b
                    else:
                        # Termina el chunk actual y empieza uno nuevo
                        chunks.append(current.strip())
                        current = b
        
        if current:
            chunks.append(current.strip())
    
    return chunks


###
# LLAMPARSE PREPROCESSING
###
def process_pdf(uploaded_dir, processed_dir, pdf_name):
    """Process a PDF file with LlamaParse and stores a markdown file in stated directory."""
    nest_asyncio.apply()

    # Set up parser
    parser = LlamaParse(
        result_type="markdown",  # "markdown" and "text" are available
        # premium_mode=False,
        # auto_mode=True,
        auto_mode_trigger_on_table_in_page=True
    )
    file_name = f"{uploaded_dir}/{pdf_name}"
    document = parser.load_data(file_name)

    # Create the md file
    md_name = pdf_name.replace(".pdf", ".md")
    file_name_md = f"./{processed_dir}/{md_name}"
    with open(file_name_md, "w", encoding="utf-8") as f:
        for i in range(len(document)):
            f.write(document[i].text)
    
def process_md(pdf_name):
    """Process a markdown file and creates a vectorstore."""
    # Read the markdown file
    # replace the .pdf with .md in the file name
    md_name = pdf_name.replace(".pdf", ".md")
    file_name_md = f"./processed_docs/{md_name}"

    # extracción del año (segun el titulo)
    match = re.search(r'\b(19|20)\d{2}\b', md_name)
    year = match.group(0) if match else None

    with open(file_name_md, "r", encoding="utf-8") as f:
        content = f.read()
        #chunks = chunk_text(content, chunk_size=1000)
        sections = split_sections(content)
        chunks = split_chunks(sections, target=1000, tol=150)

    documents = []
    # Crear un objeto Document para cada chunk, manteniendo los metadatos
    for chunk in chunks:
        if year:
            doc = Document(page_content=chunk, metadata={"year": year})
        else:
            doc = Document(page_content=chunk)
        print(f"Chunk's first 100 characters: {chunk[:100]}")
        documents.append(doc)

    # Configurar embeddings
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key, model="text-embedding-3-small")

    # Directorio de persistencia
    # persist_dir = os.path.join(os.path.dirname(__file__), "vectorstore_chromadb")
    #os.makedirs(persist_dir, exist_ok=True)

    # Crear el vectorstore en Chroma
    vectorstore = Chroma.from_documents(
        documents=documents, 
        embedding=embeddings, 
        persist_directory="./services/agents/vectorstore_chromadb_automatic"
)

    # Persistir la base de datos
    vectorstore.persist()

def process_md_dir(dir_name):
    """Process all markdown files in a directory."""
    # List all files in the directory
    files = os.listdir(dir_name)
    documents = []
    for file in files:
        if file.endswith(".md"):
            # extracción del año (segun el titulo)
            match = re.search(r'\b(19|20)\d{2}\b', file)
            year = match.group(0) if match else None

            file_path = os.path.join(dir_name, file)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                #chunks = chunk_text(content, chunk_size=1000)
                sections = split_sections(content)
                chunks = split_chunks(sections, target=1000, tol=150)
            
            
            # Crear un objeto Document para cada chunk, manteniendo los metadatos
            for chunk in chunks:
                if year:
                    doc = Document(page_content=chunk, metadata={"year": year})
                    print(f"Agregado chunk de '{file}' (year={year}): {chunk[:80]}...")
                else:
                    doc = Document(page_content=chunk)
                
                documents.append(doc)

    # Configurar embeddings
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key, model="text-embedding-3-small") # TRy the voyager embeddings model

    # Crear el vectorstore en Chroma
    persist_dir = r"C:\Users\alber_7dxjh2i\OneDrive\Documentos\alberto\AI Agents\Code\global_agent\api\services\agents\vectorstore_chromadb_automatic"
    #os.makedirs(persist_dir, exist_ok=True)
    #if not os.path.exists(persist_dir):
    #    os.makedirs(persist_dir)
    vectorstore = Chroma.from_documents(documents=documents, embedding=embeddings, persist_directory=persist_dir)

"""
if __name__ == "__main__":
    
    # Process the PDF file
    pdf_name = "2024-11-15 ESP Perfil biografico Consejeros.pdf"
    process_pdf(pdf_name)

    # Process the markdown file
    md_name = "2024-11-15 ESP Perfil biografico Consejeros.md"
    process_md(pdf_name)
    
    process_md_dir("./processed_docs")
    print("Vectorstore created and persisted successfully.")
"""