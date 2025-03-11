import streamlit as st
from reportlab.lib.pagesizes import A5
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
import io
import requests
from PIL import Image as PILImage, ImageDraw
import tempfile
import os

# Fungsi untuk membuat logo bulat dengan URL atau fallback lokal
def create_round_logo(url=None, fallback_path="logo.png"):
    try:
        if url:
            response = requests.get(url, timeout=5)
            response.raise_for_status()  # Periksa jika request gagal
            img = PILImage.open(io.BytesIO(response.content)).convert("RGBA")
        else:
            raise ValueError("No URL provided, using fallback")
    except (requests.RequestException, ValueError, PILImage.UnidentifiedImageError):
        # Jika gagal, gunakan logo lokal sebagai fallback
        try:
            img = PILImage.open(fallback_path).convert("RGBA")
        except:
            # Jika fallback juga gagal, buat placeholder sederhana
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

# Fungsi untuk generate PDF
def generate_pdf(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A5)
    styles = getSampleStyleSheet()
    story = []

    # Konten invoice
    story.append(Paragraph(" INVOICE PEMBELIAN ", styles['Heading2']))
    tanggal_format = f"{data['tanggal']} {data['bulan']} {data['tahun']}"
    story.append(Paragraph(tanggal_format, styles['Normal']))
    story.append(Paragraph("...................................................................................", styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("TRANSFER SESUAI NOMINAL YANG TERTERA KE REKENING di bawah ini :", styles['Normal']))
    story.append(Paragraph("<b>• BCA 3130143996 a/n AGUS EKO YULIANTO </b>", styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph(f"Untuk : {data['untuk']}", styles['Normal']))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"No Hp : {data['nohp']}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph(f"Alamat : {data['alamat']}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Rincian Barang dari list barang
    story.append(Paragraph("Rincian Barang :", styles['Normal']))
    for item in data['items']:
        story.append(Paragraph(f"- {item['nama']} : Rp {item['harga']:,}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph(f"Harga Barang : Rp {data['harga_barang']:,}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph(f"Biaya ongkir : Rp {data['ongkir']:,}", styles['Normal']))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"<b> TOTAL : Rp {data['total']:,} </b>", styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Mohon dengan seksama di cek kembali invoice kami yang sudah terbit, bila ada kesalahan segera infokan kembali kepada kami. ", styles['Normal']))
    story.append(Paragraph("<b> Terima kasih </b>", styles['Normal']))

    # Fungsi untuk menambahkan watermark di tengah
    def add_watermark(canvas, doc):
        canvas.saveState()
        logo_url = "https://p16-sign-va.tiktokcdn.com/tos-maliva-avt-0068/e57060a342b741fd0a7c488797159363~tplv-tiktokx-cropcenter:1080:1080.jpeg?dr=14579&refresh_token=8a46dcd8&x-expires=1741874400&x-signature=5rjAsXYrKU4dzONcLgk7qO2Go1w%3D&t=4d5b0474&ps=13740610&shp=a5d48078&shcp=81f88b70&idc=my"
        logo_path = create_round_logo(logo_url, fallback_path="logo.png")
        
        watermark_width = 200
        watermark_height = 200
        x = (A5[0] - watermark_width) / 2  # Tengah horizontal
        y = (A5[1] - watermark_height) / 2  # Tengah vertikal, tanpa offset
        
        canvas.setFillAlpha(0.1)
        canvas.drawImage(logo_path, x, y, width=watermark_width, height=watermark_height, mask='auto')
        
        canvas.restoreState()
        os.remove(logo_path)

    doc.build(story, onFirstPage=add_watermark, onLaterPages=add_watermark)
    
    buffer.seek(0)
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
    
    submit_button = st.form_submit_button(label="Generate PDF")

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
    
    pdf_buffer = generate_pdf(data)
    st.download_button(
        label="Unduh Invoice",
        data=pdf_buffer,
        file_name="invoice.pdf",
        mime="application/pdf"
    )

# Instruksi untuk menjalankan
st.write("Jalankan aplikasi dengan perintah: `streamlit run invoice.py`")