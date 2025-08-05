import logging
import os
import json
from pathlib import Path
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from flask import Flask, request, jsonify

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from vi_search.ask import RetrieveThenReadVectorApproach
from vi_search.prepare_db import prepare_db
from vi_search.constants import BASE_DIR, DATA_DIR


search_db = os.environ.get("PROMPT_CONTENT_DB", "azure_search")
if search_db == "chromadb":
    from vi_search.prompt_content_db.chroma_db import ChromaDB
    prompt_content_db = ChromaDB()
elif search_db == "azure_search":
    from vi_search.prompt_content_db.azure_search import AzureVectorSearch
    prompt_content_db = AzureVectorSearch()
else:
    raise ValueError(f"Unknown search_db: {search_db}")

lang_model = os.environ.get("LANGUAGE_MODEL", "openai")
if lang_model == "openai":
    from vi_search.language_models.azure_openai import OpenAI
    language_models = OpenAI()
elif lang_model == "dummy":
    from vi_search.language_models.dummy_lm import DummyLanguageModels
    language_models = DummyLanguageModels()
else:
    raise ValueError(f"Unknown language model: {lang_model}")


ask_approaches = {
    "rrrv": RetrieveThenReadVectorApproach(prompt_content_db=prompt_content_db, language_models=language_models)
}

app = Flask(__name__)

# The limiter is used to prevent abuse of the API, you can adjust the limits as needed
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["300000 per day", "20000 per hour"],
    storage_uri="memory://",
)
ASK_RATE_LIMIT_PER_DAY = 1000
ASK_RATE_LIMIT_PER_MIN = 50


@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def static_file(path):
    return app.send_static_file(path)


@app.route("/ask", methods=["POST"])
@limiter.limit(f"{ASK_RATE_LIMIT_PER_DAY}/day;{ASK_RATE_LIMIT_PER_MIN}/minute", override_defaults=True)
def ask():
    if not request.json:
        return jsonify({"error": "Invalid JSON"}), 400
        
    approach = request.json.get("approach")
    if not approach:
        return jsonify({"error": "Approach is required"}), 400
        
    try:
        impl = ask_approaches.get(approach)
        if impl is None:
            return jsonify({"error": "unknown approach"}), 400

        # print(f"question: {request.json['question']}")
        r = impl.run(request.json.get("question", ""), request.json.get("overrides") or {})
        print(f"response: {r['answer']}\n\n")
        # print(f"response: {r}\n\n")
        return jsonify(r)

    except Exception as e:
        logging.exception("Exception in /ask")
        return jsonify({"error": str(e)}), 500


@app.route("/indexes", methods=["GET"])
def get_indexes():
    indexes = prompt_content_db.get_available_dbs()
    return jsonify(indexes)


@app.route("/libraries", methods=["POST"])
def create_library():
    """Create a new video library (database)"""
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({"error": "Library name is required"}), 400
        
        library_name = data['name']
        
        # Validate library name format
        if not library_name.startswith('vi-') or not library_name.endswith('-index'):
            return jsonify({"error": "Library name must start with 'vi-' and end with '-index'"}), 400
        
        # Create empty database
        embeddings_size = language_models.get_embeddings_size()
        prompt_content_db.create_db(library_name, vector_search_dimensions=embeddings_size)
        
        return jsonify({"message": f"Library '{library_name}' created successfully"}), 201
        
    except Exception as e:
        logging.exception("Exception in /libraries POST")
        return jsonify({"error": str(e)}), 500


@app.route("/libraries/<library_name>", methods=["DELETE"]) 
def delete_library(library_name):
    """Delete a video library (database)"""
    try:
        # Check if library exists
        available_dbs = prompt_content_db.get_available_dbs()
        if library_name not in available_dbs:
            return jsonify({"error": "Library not found"}), 404
        
        # Delete the database
        prompt_content_db.remove_db(library_name)
        
        return jsonify({"message": f"Library '{library_name}' deleted successfully"}), 200
        
    except Exception as e:
        logging.exception("Exception in /libraries DELETE")
        return jsonify({"error": str(e)}), 500


@app.route("/upload", methods=["POST"])
def upload_video():
    """Upload video to a specific library"""
    try:
        if 'video' not in request.files:
            return jsonify({"error": "No video file provided"}), 400
            
        if 'library' not in request.form:
            return jsonify({"error": "Library name is required"}), 400
            
        video_file = request.files['video']
        library_name = request.form['library']
        
        if video_file.filename == '' or video_file.filename is None:
            return jsonify({"error": "No video file selected"}), 400
        
        # Check if library exists
        available_dbs = prompt_content_db.get_available_dbs()
        if library_name not in available_dbs:
            return jsonify({"error": "Library not found"}), 404
        
        # Save uploaded file
        filename = secure_filename(video_file.filename)
        upload_path = DATA_DIR / filename
        video_file.save(upload_path)
        
        # Process single video file with existing prepare_db logic
        # This processes the specific uploaded file
        try:
            prepare_db(library_name, DATA_DIR, language_models, prompt_content_db, 
                      use_videos_ids_cache=False, verbose=True, single_video_file=upload_path)
        except Exception as prep_error:
            logging.exception("Exception in prepare_db during upload")
            return jsonify({"error": f"Video processing failed: {str(prep_error)}"}), 500
        
        return jsonify({"message": f"Video '{filename}' uploaded and processed successfully"}), 200
        
    except Exception as e:
        logging.exception("Exception in /upload")
        return jsonify({"error": str(e)}), 500


@app.route("/settings/<library_name>", methods=["GET"])
def get_library_settings(library_name):
    """Get settings for a specific library"""
    try:
        # For now, return default settings
        # You can extend this to store actual settings in a database
        default_settings = {
            "promptTemplate": "You are an AI assistant that answers questions about videos.\n\nContext: {context}\nQuestion: {question}\n\nAnswer:",
            "semanticRanker": True,
            "temperature": 0.7,
            "maxTokens": 800
        }
        return jsonify(default_settings), 200
        
    except Exception as e:
        logging.exception("Exception in /settings GET")
        return jsonify({"error": str(e)}), 500


@app.route("/settings/<library_name>", methods=["POST"])
def save_library_settings(library_name):
    """Save settings for a specific library"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Settings data is required"}), 400
        
        # For now, just acknowledge the save
        # You can extend this to actually store settings in a database
        return jsonify({"message": f"Settings for '{library_name}' saved successfully"}), 200
        
    except Exception as e:
        logging.exception("Exception in /settings POST")
        return jsonify({"error": str(e)}), 500

# Handle the rate limit exceeded exception
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Rate limit: Exceeded the number of asks per day", "message": e.description}), 429


if __name__ == "__main__":
    # 檢查是否在容器環境中
    is_docker = os.path.exists('/.dockerenv')
    is_development = os.environ.get('FLASK_ENV') == 'development'
    
    if is_docker:
        # Docker 環境設定
        app.run(
            host='0.0.0.0',  # 容器內必須綁定到 0.0.0.0
            port=5000,
            debug=is_development,
            threaded=True
        )
    else:
        # 本機開發設定
        app.run(
            host='0.0.0.0',  # 允許外部連接
            port=5000,
            debug=True,      # 啟用除錯模式
            threaded=True    # 支援多執行緒
        )
