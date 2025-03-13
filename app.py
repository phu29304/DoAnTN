import os
import base64
import pandas as pd
from PIL import Image
from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import pytesseract
from pdf2image import convert_from_path
import traceback
import os

# Đặt biến môi trường TESSDATA_PREFIX trỏ về đúng thư mục cha của tessdata
os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR'

import pytesseract

# Đặt đúng đường dẫn tới file tesseract.exe
pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"

print("TESSDATA_PREFIX =", os.environ.get("TESSDATA_PREFIX"))




# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")

# Upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_image(image_path):
    try:
        # Ensure Tesseract is installed and the path is correct
        tesseract_cmd = os.getenv("TESSERACT_PATH")
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        # Use Tesseract to extract text
        return pytesseract.image_to_string(Image.open(image_path), lang="eng")
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return None

def extract_text_from_image(image_path):
    try:
        pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"
        os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR"

        print(f"[DEBUG] TESSDATA_PREFIX = {os.environ.get('TESSDATA_PREFIX')}")

        img = Image.open(image_path)
        print("[DEBUG] Image loaded, running OCR...")

        config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(img, lang='vie', config=config)

        if not text.strip():
            print("[DEBUG] OCR tiếng Việt rỗng, thử lại với tiếng Anh...")
            text = pytesseract.image_to_string(img, lang='eng', config=config)

        print(f"[DEBUG] OCR done ✅")
        return text

    except Exception as e:
        print(f"[ERROR] OCR thất bại: {e}")
        return ""



def extract_text_from_pdf(pdf_path):
    try:
        print(f"[DEBUG] Converting PDF to image: {pdf_path}")
        images = convert_from_path(pdf_path)
        if images:
            img = images[0]  # chỉ xử lý trang đầu tiên
            text = pytesseract.image_to_string(img, lang='vie')
            print(f"[DEBUG] Raw OCR text:\n{text}")

            return text
        return ""
    except Exception as e:
        print(f"[ERROR] PDF to image failed: {e}")
        return ""


def process_menu_text(text):
    menu_items = []
    lines = text.split('\n')
    current_item = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        has_price = any(char.isdigit() for char in line)

        if has_price and current_item:
            price = ''.join(char for char in line if char.isdigit() or char in ',.₫đVND')
            current_item['price'] = price.strip()
            menu_items.append(current_item)
            current_item = None
        elif not current_item:
            current_item = {'name': line, 'description': '', 'price': ''}
        else:
            current_item['description'] += ' ' + line if current_item['description'] else line

    if current_item:
        menu_items.append(current_item)

    return menu_items

def save_to_excel(menu_items, output_path):
    df = pd.DataFrame(menu_items)
    df.to_excel(output_path, index=False)

@app.route('/')
def index():
    return render_template('menu.html')

import traceback  # THÊM DÒNG NÀY Ở ĐẦU FILE

@app.route("/process_menu", methods=["POST"])
def process_menu():
    try:
        if 'menu_image' not in request.files:
            return jsonify({"success": False, "error": "Không tìm thấy ảnh thực đơn"}), 400

        file = request.files['menu_image']
        if file.filename == '':
            return jsonify({"success": False, "error": "Chưa chọn tệp"}), 400

        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Định dạng tệp không hợp lệ'}), 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        print(f"[DEBUG] File saved to: {file_path}")
        print(f"[DEBUG] File exists? {os.path.exists(file_path)}")

        ext = filename.rsplit('.', 1)[1].lower()
        print(f"[DEBUG] File extension: {ext}")

        if ext == 'pdf':
         print("[DEBUG] Extracting text from PDF...")
         text = extract_text_from_pdf(file_path)  # ✅ SỬA CHỖ NÀY
        else:
         print("[DEBUG] Extracting text from image...")
         text = extract_text_from_image(file_path)


        print(f"[DEBUG] Extracted text:\n{text[:500]}")  # In 500 ký tự đầu để kiểm tra

        if not text:
            return jsonify({"success": False, "error": "Không trích xuất được nội dung từ ảnh"}), 500

        print("[DEBUG] Processing extracted text into structured data...")
        menu_items = process_menu_text(text)
        print(f"[DEBUG] Menu items: {menu_items}")

        excel_filename = filename.rsplit('.', 1)[0] + '.xlsx'
        excel_path = os.path.join(app.config['UPLOAD_FOLDER'], excel_filename)
        print(f"[DEBUG] Saving to Excel: {excel_path}")
        save_to_excel(menu_items, excel_path)

        return jsonify({
            "success": True,
            "menu_items": menu_items,
            "excel_file": url_for('download_file', filename=excel_filename)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"Lỗi server: {str(e)}"}), 500


@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

