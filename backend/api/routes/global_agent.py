from flask import Blueprint, request, jsonify
from services.chat_service import ChatService
from services.file_processor import process_files
from services.vector_db import VectorDBService


chat_service = ChatService()
global_routes = Blueprint('global', __name__)
vector_db_service = VectorDBService()


@global_routes.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    
    message = data.get("message", "")
    schema = data.get("schema", "")
    if schema =="No schema provided, look for the required information" or schema == "No schema provided, look for the information required":
        schema = ""
    print("ESQUEMA: ", schema)
    conversation_id = data.get("conversation_id", "1")
    if not message:
        return jsonify({"error": "Conversation id is required"}), 400
    
    if not message:
        return jsonify({"error": "Message is required"}), 400

    result = chat_service.process_query_global_agent(message, conversation_id, schema,rag_only=True, web_only=True)
    print("TODO BIEN HASTA AQUI")
    print(result)
    return jsonify(result), 200

@global_routes.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('files')
    # conv = request.form.get('conversation_id')
    metadata = process_files(files)
    return jsonify({"status": "success", "files": metadata})

@global_routes.route('/generate-vector-db', methods=['POST'])
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