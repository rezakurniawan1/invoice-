import streamlit as st
from PIL import Image as PILImage, ImageDraw, ImageFont
import io
import tempfile
import os

# Fungsi untuk membuat logo bulat hanya dari file lokal
def create_round_logo(fallback_path="logo.png"):
    try:
        img = PILImage.open(fallback_path).convert("RGBA")
    except:
        # Jika file lokal tidak ada, buat placeholder sederhana
        img = PILImage.new("RGBA", (200, 200), (255, 255, 255, 0))
    
    size = min(img.size)
    mask = PILImage.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    img = img.resize((size, size), PILImage.Resampling.LANCZOS)
    img.putalpha(mask)
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    img.save(temp_file.name, format='PNG')
    return temp_file.name

# Fungsi untuk generate PNG
def generate_png(data):
    # Ukuran A5 dalam piksel (asumsi 96 DPI)
    width, height = 559, 794  # A5: 148mm x 210mm = 559px x 794px pada 96 DPI
    
    # Buat kanvas putih
    image = PILImage.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    
    # Load font (gunakan font default atau spesifik jika ada)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
        font_bold = ImageFont.truetype("arialbd.ttf", 16)
        font_title = ImageFont.truetype("arialbd.ttf", 24)
    except:
        font = ImageFont.load_default()
        font_bold = ImageFont.load_default()
        font_title = ImageFont.load_default()

    # Posisi awal teks
    y_position = 20
    
    # Konten invoice
    draw.text((width // 2, y_position), "INVOICE PEMBELIAN", font=font_title, fill="black", anchor="mm")
    y_position += 40
    
    tanggal_format = f"{data['tanggal']} {data['bulan']} {data['tahun']}"
    draw.text((20, y_position), tanggal_format, font=font, fill="black")
    y_position += 20
    
    draw.text((20, y_position), "-" * 70, font=font, fill="black")
    y_position += 20
    
    draw.text((20, y_position), "TRANSFER SESUAI NOMINAL YANG TERTERA KE REKENING di bawah ini :", font=font, fill="black")
    y_position += 20
    draw.text((20, y_position), "• BCA 3130143996 a/n AGUS EKO YULIANTO", font=font_bold, fill="black")
    y_position += 30
    
    draw.text((20, y_position), f"Untuk : {data['untuk']}", font=font, fill="black")
    y_position += 20
    
    draw.text((20, y_position), f"No Hp : {data['nohp']}", font=font, fill="black")
    y_position += 20
    
    draw.text((20, y_position), f"Alamat : {data['alamat']}", font=font, fill="black")
    y_position += 30
    
    # Rincian Barang
    draw.text((20, y_position), "Rincian Barang :", font=font, fill="black")
    y_position += 20
    for item in data['items']:
        draw.text((20, y_position), f"- {item['nama']} : Rp {item['harga']:,}", font=font, fill="black")
        y_position += 20
    y_position += 10
    
    draw.text((20, y_position), f"Harga Barang : Rp {data['harga_barang']:,}", font=font, fill="black")
    y_position += 20
    
    draw.text((20, y_position), f"Biaya ongkir : Rp {data['ongkir']:,}", font=font, fill="black")
    y_position += 20
    
    draw.text((20, y_position), f"TOTAL : Rp {data['total']:,}", font=font_bold, fill="black")
    y_position += 30
    
    draw.text((20, y_position), "Mohon dengan seksama di cek kembali invoice kami yang sudah terbit,", font=font, fill="black")
    y_position += 20
    draw.text((20, y_position), "bila ada kesalahan segera infokan kembali kepada kami.", font=font, fill="black")
    y_position += 20
    draw.text((20, y_position), "Terima kasih", font=font_bold, fill="black")

    # Tambahkan watermark
    logo_path = create_round_logo(fallback_path="logo.png")
    watermark = PILImage.open(logo_path).convert("RGBA")
    watermark = watermark.resize((200, 200), PILImage.Resampling.LANCZOS)
    
    # Posisi watermark di tengah
    watermark_x = (width - 200) // 2
    watermark_y = (height - 200) // 2 + 20  # Tengah vertikal dengan offset kecil
    
    # Buat layer untuk watermark dengan transparansi
    watermark_layer = PILImage.new("RGBA", image.size, (0, 0, 0, 0))
    watermark_layer.paste(watermark, (watermark_x, watermark_y))
    image = PILImage.composite(watermark_layer, image, watermark_layer)
    
    # Simpan ke buffer sebagai PNG
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    
    # Hapus file sementara
    os.remove(logo_path)
    
    return buffer

# Aplikasi Streamlit
st.title("Generate Invoice")

bulan_indonesia = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]

with st.form(key='invoice_form'):
    tanggal = st.number_input("Tanggal", min_value=1, max_value=31, step=1)
    bulan = st.selectbox("Bulan", bulan_indonesia)
    tahun = st.number_input("Tahun", min_value=2000, max_value=9999, step=1)
    untuk = st.text_input("Untuk")
    nohp = st.text_input("No Hp")
    alamat = st.text_area("Alamat")
    
    # Input untuk multiple barang
    st.subheader("Rincian Barang")
    num_items = st.number_input("Jumlah Barang", min_value=1, max_value=10, step=1, value=1)
    items = []
    total_harga_barang = 0
    
    for i in range(num_items):
        col1, col2 = st.columns(2)
        with col1:
            nama_barang = st.text_input(f"Nama Barang {i+1}", key=f"nama_{i}")
        with col2:
            harga_barang_item = st.number_input(f"Harga Barang {i+1}", min_value=0, step=1000, key=f"harga_{i}")
            total_harga_barang += harga_barang_item
        items.append({"nama": nama_barang, "harga": harga_barang_item})
    
    ongkir = st.number_input("Biaya Ongkir", min_value=0, step=1000)
    
    # Hitung total
    total = total_harga_barang + ongkir
    
    st.write(f"Total: Rp {total:,}")
    
    submit_button = st.form_submit_button(label="Generate PNG")

if submit_button:
    data = {
        "tanggal": tanggal,
        "bulan": bulan,
        "tahun": tahun,
        "untuk": untuk,
        "nohp": nohp,
        "alamat": alamat,
        "items": items,
        "harga_barang": total_harga_barang,
        "ongkir": ongkir,
        "total": total
    }
    
    png_buffer = generate_png(data)
    st.download_button(
        label="Unduh Invoice (PNG)",
        data=png_buffer,
        file_name="invoice.png",
        mime="image/png"
    )

# Instruksi untuk menjalankan
st.write("Jalankan aplikasi dengan perintah: `streamlit run invoice.py`")