from flask import Flask, request, render_template, redirect, url_for
import os
import uuid
import shutil
import json
from gradio_client import Client, file 
from PIL import Image

# --- Flask Configuration ---
app = Flask(__name__)

# The final working Gradio Space ID
HUGGINGFACE_SPACE_ID = "phitran/fashion-virtual-tryon" 

# Define folder paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, 'temp_uploads')
WARDROBE_DIR = os.path.join(BASE_DIR, 'static', 'wardrobe_uploads')
WARDROBE_DB = os.path.join(BASE_DIR, 'wardrobe_data.json')

# Create necessary directories
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(WARDROBE_DIR, exist_ok=True)


# --- Wardrobe Data Persistence (Simulated Database) ---
def load_wardrobe():
    if not os.path.exists(WARDROBE_DB):
        return {}
    with open(WARDROBE_DB, 'r') as f:
        return json.load(f)

def save_wardrobe(data):
    with open(WARDROBE_DB, 'w') as f:
        json.dump(data, f, indent=4)
        
# --- General Routes ---

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

# --- Wardrobe Management ---
@app.route('/test')
def test():
    return "App is running!"

@app.route('/wardrobe', methods=['GET'])
def wardrobe():
    wardrobe_items = load_wardrobe()
    # Convert dictionary to list for easier template looping (preserving item_id)
    items_list = [{'id': k, 'path': v} for k, v in wardrobe_items.items()]
    return render_template('wardrobe.html', items=items_list)

from werkzeug.utils import secure_filename

@app.route('/wardrobe/upload', methods=['POST'])
def wardrobe_upload():
    if 'clothing_item' not in request.files:
        return redirect(url_for('wardrobe'))
    
    file_upload = request.files['clothing_item']
    if file_upload.filename == '':
        return redirect(url_for('wardrobe'))

    try:
        unique_id = str(uuid.uuid4())
        filename = f"wardrobe_{unique_id}.jpg"
        secure_name = secure_filename(filename)
        file_path = os.path.join(WARDROBE_DIR, secure_name)

        # Save the uploaded file as JPEG
        Image.open(file_upload.stream).convert('RGB').save(file_path, format='JPEG')

        # ✅ Save only the filename (no folder path)
        wardrobe = load_wardrobe()
        wardrobe[unique_id] = secure_name
        save_wardrobe(wardrobe)

    except Exception as e:
        print(f"Error saving wardrobe item: {e}")
        return f"Error saving file: {e}", 500

    return redirect(url_for('wardrobe'))

@app.route('/wardrobe/delete/<item_id>', methods=['POST'])
def wardrobe_delete(item_id):
    wardrobe = load_wardrobe()
    if item_id in wardrobe:
        relative_path = wardrobe[item_id]
        full_path = os.path.join(WARDROBE_DIR, relative_path)
        if os.path.exists(full_path):
            os.remove(full_path)
        del wardrobe[item_id]
        save_wardrobe(wardrobe)
    return redirect(url_for('wardrobe'))
# --- Virtual Try-On Logic ---

# @app.route('/static/<filename>')
# def serve_static_image(filename):
#     # This route is standard for static files; ensure the file exists.
#     file_path = os.path.join(app.root_path, 'static', filename)
#     if os.path.exists(file_path):
#         # We serve the file with its correct MIME type based on the extension
#         mime_type = 'image/webp' if filename.endswith('.webp') else 'image/png'
#         return send_file(file_path, mimetype=mime_type)
#     return "Image not found.", 404

@app.route('/tryon', methods=['GET', 'POST'])
def gradio_try_on():
    if request.method == 'GET':
        return render_template('tryon.html') 

    if request.method == 'POST':
        person_file = request.files.get('person_photo')
        garment_file = request.files.get('clothing_image')

        if not person_file or not garment_file:
            return "Please upload both images.", 400

        # 1. Save input files temporarily
        unique_id = str(uuid.uuid4())
        person_path = os.path.join(TEMP_DIR, f'person_input_{unique_id}.jpg')
        garment_path = os.path.join(TEMP_DIR, f'garment_input_{unique_id}.jpg')
        
        try:
            # Use PIL to ensure clean JPEG saving
            Image.open(person_file.stream).convert('RGB').save(person_path, format='JPEG')
            Image.open(garment_file.stream).convert('RGB').save(garment_path, format='JPEG')
        except Exception as e:
            return f"Error processing input image file: {e}", 500

        # 2. Initialize and Call Gradio Client
        client = Client("phitran/fashion-virtual-tryon")
        try:
            result_output = client.predict(
                human_img_path=file(person_path),
                garm_img_path=file(garment_path),
                api_name="/process_image"
            )

            # ✅ dict handling instead of tuple
            if not isinstance(result_output, dict) or "path" not in result_output:
                raise Exception("Invalid response from API")

            result_file_path = result_output["path"]

            if not isinstance(result_file_path, str) or not os.path.exists(result_file_path):
                 error_response = result_output[1] if len(result_output) > 1 and isinstance(result_output[1], str) else "Unknown generation failure."
                 raise Exception(f"Image generation failed, path not found. Server Response: {error_response}")

            # 4. Move the downloaded file to your static folder

            # ✅ Ensure static folder exists
            STATIC_DIR = os.path.join(BASE_DIR, 'static')
            os.makedirs(STATIC_DIR, exist_ok=True)

            # Generate filename
            _, ext = os.path.splitext(result_file_path)
            final_image_filename = f'result_{uuid.uuid4()}{ext}'

            # Final path
            final_image_fs_path = os.path.join(STATIC_DIR, final_image_filename)

            # Move file
            shutil.move(result_file_path, final_image_fs_path)
            # 5. Clean up input files
            os.remove(person_path)
            os.remove(garment_path)

            # 6. Pass the relative path to the template
            return render_template('result.html', tryon_image=url_for('static', filename=final_image_filename))

        except Exception as e:
            # Final cleanup on failure
            if os.path.exists(person_path): os.remove(person_path)
            if os.path.exists(garment_path): os.remove(garment_path)
            
            return f"Try-On API call failed. Error: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)