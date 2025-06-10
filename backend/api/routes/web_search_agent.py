from flask import Blueprint, request, jsonify
from services.chat_service import ChatService

chat_service = ChatService()
web_search_routes = Blueprint('websearch', __name__)

@web_search_routes.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    
    message = data.get("message", "")
    schema = data.get("schema", "")
    if schema =="No schema provided, look for the required information":
        schema = ""
    print("----SCHEMA: ", schema)
    conversation_id = data.get("conversation_id", "1")
    if not message:
        return jsonify({"error": "Conversation id is required"}), 400
    
    if not message:
        return jsonify({"error": "Message is required"}), 400

    result = chat_service.process_query_global_agent(message, conversation_id, schema,rag_only=False, web_only=True)
    print("TODO BIEN HASTA AQUI")
    print(result)
    return jsonify(result), 200