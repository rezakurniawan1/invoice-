import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
import io
import requests
from PIL import Image as PILImage, ImageDraw
import tempfile
import os

# Fungsi untuk mengunduh dan membuat logo bulat dengan saturasi rendah
def create_round_logo(url):
    response = requests.get(url)
    img = PILImage.open(io.BytesIO(response.content)).convert("RGBA")
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
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Konten invoice
    story.append(Paragraph(" INVOICE PEMBELIAN ", styles['Heading2']))
    tanggal_format = f"{data['tanggal']} {data['bulan']} {data['tahun']}"
    story.append(Paragraph(tanggal_format, styles['Normal']))
    story.append(Paragraph(".............................................................................................................................", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Teks dibuat bold
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

    # Total dihitung dari harga_barang + ongkir
    story.append(Paragraph(f"TOTAL : Rp {data['total']:,}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Mohon dengan seksama di cek kembali invoice kami yang sudah terbit, bila ada kesalahan segera infokan kembali kepada kami. ", styles['Normal']))
    story.append(Paragraph("<b> Terima kasih </b>", styles['Normal']))

    # Fungsi untuk menambahkan watermark
    def add_watermark(canvas, doc):
        canvas.saveState()
        logo_url = "https://p16-sign-va.tiktokcdn.com/tos-maliva-avt-0068/e57060a342b741fd0a7c488797159363~tplv-tiktokx-cropcenter:1080:1080.jpeg?dr=14579&nonce=53406&refresh_token=b5ab12a14055351a33df4b3d43b67108&x-expires=1740837600&x-signature=Kr%2FjmoP6VwXNNR%2Bc0cFdbeQCvBM%3D&idc=my&ps=13740610&shcp=81f88b70&shp=a5d48078&t=4d5b0474"
        logo_path = create_round_logo(logo_url)
        
        # Atur posisi watermark di tengah halaman
        watermark_width = 300
        watermark_height = 300
        x = (A4[0] - watermark_width) / 2
        y = (A4[1] - watermark_height) / 2 + 200
        
        # Atur transparansi rendah
        canvas.setFillAlpha(0.1)
        canvas.drawImage(logo_path, x, y, width=watermark_width, height=watermark_height, mask='auto')
        
        canvas.restoreState()
        os.remove(logo_path)

    # Build PDF dengan watermark
    doc.build(story, onFirstPage=add_watermark, onLaterPages=add_watermark)
    
    buffer.seek(0)
    return buffer

# Aplikasi Streamlit
st.title("Generate Invoice")

# Daftar bulan dalam bahasa Indonesia
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
    
    # Hitung total otomatis
    total = harga_barang + ongkir
    
    # Tampilkan total sebagai informasi (tidak bisa diedit)
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
        "total": total  # Total sudah dihitung
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