import time

from services.vector_db_utils import process_md_dir, process_pdf
from services.file_processor import UPLOAD_FOLDER
from dotenv import load_dotenv

PROCESSED_FOLDER = 'processed_files'

# Creates a vector database from the provided file paths and conversation ID
class VectorDBService:
    def create_vector_db(self, file_names, conversation_id):
        print(file_names)
        if isinstance(file_names[0], dict):
            file_names = [f["name"] for f in file_names]
        print(file_names)
        # time.sleep(2)
        folder_to_process = UPLOAD_FOLDER
        processed_folder = PROCESSED_FOLDER
        # Process the files from raw pdf to md
        for file_name in file_names:
            process_pdf(folder_to_process, processed_folder, file_name)
        # Process the files from md to vectorstore
        print("Preprocessing complete.")
        process_md_dir(processed_folder)
        print("Vectordatabase created.")


        return { "status":"success", "message":"Vector—DB created" }

