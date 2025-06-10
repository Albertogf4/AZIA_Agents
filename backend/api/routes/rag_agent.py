from flask import Blueprint, request, jsonify
from services.chat_service import ChatService
from services.vector_db import VectorDBService
from services.file_processor import process_files

rag_routes = Blueprint('rag', __name__)
chat_service = ChatService()
vector_db_service = VectorDBService()

@rag_routes.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    
    message = data.get("message", "")
    conversation_id = data.get("conversation_id", "1")
    if not message:
        return jsonify({"error": "Conversation id is required"}), 400
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    result = chat_service.process_query_global_agent(message, conversation_id, "", rag_only=True, web_only=False)
    print("TODO BIEN HASTA AQUI")
    print(result)
    return jsonify(result), 200

@rag_routes.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('files')
    # conv = request.form.get('conversation_id')
    metadata = process_files(files)
    # @TODO: podría guardar aquí los archivos y hacer el preprocesado
    return jsonify({"status": "success", "files": metadata})

@rag_routes.route('/generate-vector-db', methods=['POST'])
def gen_db():
    data = request.json
    file_paths = data.get("file_paths")
    conversation_id    = data.get("conversation_id")
    #return jsonify({"status":"success","message":"stubbed vector DB created"}), 200
    if not file_paths or not conversation_id:
        return jsonify({
            "status": "error",
            "message": "Missing file_paths or conversation_id"
        }), 400

    try:
        result = vector_db_service.create_vector_db(file_paths, conversation_id)
        return jsonify(result), 200
    except Exception as e: # @TODO: refine exception handling, for now this will do
        return jsonify({
            "status": "error",
            "message": f"Vector DB creation failed: {str(e)}"
        }), 500