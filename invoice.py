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

# Fungsi untuk mengunduh dan membuat logo bulat dengan saturasi rendah
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
    
    # Simpan sementara ke file untuk digunakan oleh ReportLab
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    img.save(temp_file.name, format='PNG')
    return temp_file.name

# Fungsi untuk generate PDF dengan logo sebagai watermark
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

    story.append(Paragraph(f"Alamat : {data['alamat']}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Rincian Barang :", styles['Normal']))
    story.append(Paragraph(data['rincian'].replace('\n', '<br/>'), styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph(f"Harga Barang : Rp {data['harga_barang']:,}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph(f"Biaya ongkir : Rp {data['ongkir']:,}", styles['Normal']))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"<b> TOTAL : Rp {data['total']:,} </b>", styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Mohon dengan seksama di cek kembali invoice kami yang sudah terbit, bila ada kesalahan segera infokan kembali kepada kami. ", styles['Normal']))
    story.append(Paragraph("<b> Terima kasih </b>", styles['Normal']))

    # Fungsi untuk menambahkan watermark
    def add_watermark(canvas, doc):
        canvas.saveState()
        logo_url = "https://p16-sign-va.tiktokcdn.com/tos-maliva-avt-0068/e57060a342b741fd0a7c488797159363~tplv-tiktokx-cropcenter:1080:1080.jpeg?dr=14579&nonce=53406&refresh_token=b5ab12a14055351a33df4b3d43b67108&x-expires=1740837600&x-signature=Kr%2FjmoP6VwXNNR%2Bc0cFdbeQCvBM%3D&idc=my&ps=13740610&shcp=81f88b70&shp=a5d48078&t=4d5b0474"
        logo_path = create_round_logo(logo_url, fallback_path="logo.png")
        
        watermark_width = 200
        watermark_height = 200
        x = (A5[0] - watermark_width) / 2
        y = (A5[1] - watermark_height) / 2 + 50
        
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
    alamat = st.text_area("Alamat")
    rincian = st.text_area("Rincian Barang")
    harga_barang = st.number_input("Harga Barang", min_value=0, step=1000)
    ongkir = st.number_input("Biaya Ongkir", min_value=0, step=1000)
    
    total = harga_barang + ongkir
    
    st.write(f"Total: Rp {total:,}")
    
    submit_button = st.form_submit_button(label="Generate PDF")

if submit_button:
    data = {
        "tanggal": tanggal,
        "bulan": bulan,
        "tahun": tahun,
        "untuk": untuk,
        "alamat": alamat,
        "rincian": rincian,
        "harga_barang": harga_barang,
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