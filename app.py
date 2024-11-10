import os
import pickle
import subprocess
from flask import Flask, request, jsonify, render_template, redirect, url_for
from utils import load_dataframe_from_file, detect_column_types, interpret_query, parse_visualization_info
from tempfile import NamedTemporaryFile

app = Flask(__name__)
app.secret_key = 'verysecretkey'

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

temp_file_path_global = None
uploaded_file_path_global = None  
vis_file_path_global = None  

@app.route('/upload', methods=['POST'])
def upload_file():
    global uploaded_file_path_global
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request."}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file."}), 400

    # Save the uploaded file
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    uploaded_file_path_global = file_path

    try:
        df = load_dataframe_from_file(file_path)
        column_types = detect_column_types(df)

        # Save the DataFrame to a temporary file
        with NamedTemporaryFile(delete=False, suffix='.pkl') as temp_file:
            pickle.dump(df, temp_file)
            temp_file_path = temp_file.name

        return jsonify({
            "message": "File uploaded successfully, now enter your query.",
            "temp_file": temp_file_path,
            "columns": list(df.columns),
            "column_types": column_types
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def query():
    global temp_file_path_global, vis_file_path_global
    if request.content_type != 'application/json':
        return jsonify({"error": "Unsupported Media Type. Please send JSON data."}), 415

    try:
        data = request.json
        if data is None:
            return jsonify({"error": "Invalid JSON format."}), 400

        query_text = data.get("query")
        temp_file_path = data.get("temp_file")
        temp_file_path_global = temp_file_path

        with open(temp_file_path, 'rb') as f:
            df = pickle.load(f)

        # Interpret the user's query
        interpretation = interpret_query(df, query_text)
        if interpretation is None:
            return jsonify({"error": "Failed to interpret query."}), 500

        # Parse visualization information
        visualization_info = parse_visualization_info(interpretation, query_text)
        if visualization_info is None:
            return jsonify({"error": "Failed to parse visualization information."}), 500

        # Save visualization_info to a temporary file
        with NamedTemporaryFile(delete=False, suffix='.pkl') as vis_file:
            pickle.dump(visualization_info, vis_file)
            vis_file_path = vis_file.name
            vis_file_path_global = vis_file_path 

        os.environ["TEMP_FILE_PATH"] = temp_file_path
        os.environ["VISUALIZATION_INFO_PATH"] = vis_file_path

        subprocess.Popen(["streamlit", "run", "streamlit_app.py"])

        return jsonify({
            "message": "Query processed successfully, now showing your visualization...",
            "visualization_info": visualization_info
        })
    
    except Exception as e:
        print(f"Error processing query: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/cleanup', methods=['POST'])
def cleanup():
    global temp_file_path_global, uploaded_file_path_global, vis_file_path_global

    # Delete temporary DataFrame file
    if temp_file_path_global and os.path.exists(temp_file_path_global):
        os.remove(temp_file_path_global)
        print(f"Temporary DataFrame file {temp_file_path_global} deleted successfully.")
        temp_file_path_global = None

    # Delete uploaded file
    if uploaded_file_path_global and os.path.exists(uploaded_file_path_global):
        os.remove(uploaded_file_path_global)
        print(f"Uploaded file {uploaded_file_path_global} deleted successfully.")
        uploaded_file_path_global = None

    # Delete visualization info file
    if vis_file_path_global and os.path.exists(vis_file_path_global):
        os.remove(vis_file_path_global)
        print(f"Visualization info file {vis_file_path_global} deleted successfully.")
        vis_file_path_global = None

    return jsonify({"message": "Temporary and uploaded files cleaned up successfully."})

if __name__ == '__main__':
    app.run(debug=True)