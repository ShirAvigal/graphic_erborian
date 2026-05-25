import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageColor
import io
import numpy as np
import urllib.request

st.set_page_config(page_title="Erborian Studio IL", layout="wide")

# טעינת פונט Assistant
@st.cache_resource
def get_font():
    url = "https://github.com/google/fonts/raw/main/ofl/assistant/Assistant%5Bwght%5D.ttf"
    path = "Assistant.ttf"
    try: urllib.request.urlretrieve(url, path); return path
    except: return None

font_path = get_font()

def fix_hebrew(text):
    return "\n".join([line[::-1] if any(c.isalpha() for c in line) else line for line in text.split('\n')])

st.title("Erborian Localization Studio IL 🎨")
uploaded = st.file_uploader("העלי תמונה", type=["jpg", "png"])

if uploaded:
    img = Image.open(uploaded).convert("RGB")
    W, H = img.size
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.write("### הגדרות")
        x = st.slider("X", 0, 100, 65)
        y = st.slider("Y", 0, 100, 15)
        w_box = st.slider("רוחב", 1, 100, 30)
        h_box = st.slider("גובה", 1, 100, 75)
        txt = st.text_area("טקסט בעברית", "הסוד הקוריאני\nלמראה עור אחיד וזוהר")
        f_size = st.number_input("גודל פונט", 10, 200, 45)
        
    with col1:
        draw = ImageDraw.Draw(img)
        bx, by = int(x/100*W), int(y/100*H)
        bw, bh = int(w_box/100*W), int(h_box/100*H)
        
        # מחיקה חלקה מבוססת דגימת צבע
        pix = np.array(img)
        bg = tuple(pix[min(H-1, by+10), min(W-1, bx+10)])
        draw.rectangle([bx, by, bx+bw, by+bh], fill=bg)
        
        if txt:
            try: font = ImageFont.truetype(font_path, f_size)
            except: font = ImageFont.load_default()
            for i, line in enumerate(fix_hebrew(txt).split('\n')):
                draw.text((bx+bw/2, by+20+i*(f_size+10)), line, fill="#C93939", font=font, anchor="ma")
        
        st.image(img, use_container_width=True)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        st.download_button("הורד תמונה מוכנה", buf.getvalue(), "erborian_il.png")
