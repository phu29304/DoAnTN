import pytesseract
from pdf2image import convert_from_path
import pandas as pd
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from openpyxl import Workbook
from openpyxl.drawing.image import Image as ExcelImage

# Cấu hình đường dẫn đến tesseract.exe
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Hàm chuyển đổi PDF sang danh sách các ảnh
def pdf_to_images(pdf_path):
    images = convert_from_path(pdf_path)
    return images

# Hàm nhận diện ký tự từ ảnh
def image_to_text(image):
    text = pytesseract.image_to_string(image)
    return text

# Hàm chuyển đổi văn bản thành bảng dữ liệu
def text_to_dataframe(text):
    rows = text.split('\n')
    data = [row.split() for row in rows if row.strip() != '']
    df = pd.DataFrame(data)
    return df

# Hàm lưu bảng dữ liệu và hình ảnh vào tệp Excel
def save_to_excel_with_image(df, image_path, excel_path):
    wb = Workbook()
    ws = wb.active

    # Ghi bảng dữ liệu vào Excel
    for r_idx, row in df.iterrows():
        for c_idx, value in enumerate(row):
            ws.cell(row=r_idx + 1, column=c_idx + 1, value=value)

    # Chèn hình ảnh vào Excel
    img = ExcelImage(image_path)
    ws.add_image(img, 'A10')  # Bạn có thể thay đổi vị trí chèn hình ảnh

    wb.save(excel_path)

# Hàm chính để chuyển đổi thực đơn từ PDF hoặc ảnh sang Excel
def convert_menu_to_excel(file_path, excel_path):
    _, file_extension = os.path.splitext(file_path)
    all_text = ''
    if file_extension.lower() == '.pdf':
        images = pdf_to_images(file_path)
        for image in images:
            text = image_to_text(image)
            all_text += text + '\n'
        image_path = 'temp_image.jpg'
        images[0].save(image_path)  # Lưu ảnh đầu tiên để chèn vào Excel
    else:
        image = Image.open(file_path)
        text = image_to_text(image)
        all_text += text + '\n'
        image_path = file_path  # Sử dụng ảnh gốc để chèn vào Excel
    
    df = text_to_dataframe(all_text)
    save_to_excel_with_image(df, image_path, excel_path)
    messagebox.showinfo("Thông báo", f"Chuyển đổi hoàn tất! Tệp Excel đã được lưu tại {os.path.abspath(excel_path)}")

# Hàm mở hộp thoại chọn tệp
def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("PDF và Ảnh files", "*.pdf;*.jpg;*.jpeg;*.png")])
    if file_path:
        entry_file_path.delete(0, tk.END)
        entry_file_path.insert(0, file_path)

# Hàm xử lý khi nhấn nút chuyển đổi
def on_convert():
    file_path = entry_file_path.get()
    if not file_path:
        messagebox.showwarning("Cảnh báo", "Vui lòng chọn tệp trước khi chuyển đổi!")
        return
    
    excel_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
    if not excel_path:
        return

    convert_menu_to_excel(file_path, excel_path)

# Tạo giao diện người dùng
root = tk.Tk()
root.title("Chuyển Thực Đơn Thành Excel")

# Tạo khung nhập và nút chọn tệp
frame = tk.Frame(root, padx=10, pady=10)
frame.pack(padx=10, pady=10)

label_file_path = tk.Label(frame, text="Chọn tệp (PDF hoặc Ảnh):")
label_file_path.grid(row=0, column=0, sticky="w")

entry_file_path = tk.Entry(frame, width=40)
entry_file_path.grid(row=1, column=0, pady=5)

button_browse = tk.Button(frame, text="Chọn hình ảnh", command=select_file)
button_browse.grid(row=1, column=1, padx=5)

button_convert = tk.Button(root, text="Chuyển Đổi", command=on_convert, bg="lightblue")
button_convert.pack(pady=10)

# Chạy ứng dụng
root.mainloop()
