# For filename checks
import os

UPLOAD_FOLDER = 'uploaded_files'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'csv', 'xlsx'}

def allowed_file(filename: str) -> bool:
    """Check file extension is in our allowed list."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Save to directory
def save_file(file) -> dict:
    """Guarda el archivo y devuelve la metadata correspondiente."""
    file_path = f"uploaded_files/{file.filename}"

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    file.save(file_path)
    return {
        "name": file.filename,
        "path": file_path,
        "size": os.path.getsize(file_path),
    }

def process_files(files) -> list[dict]:
    """
    Stubbed process_files: pretend each uploaded file becomes our dummy metadata.
    """
    return [save_file(f) for f in files if allowed_file(f.filename)]
