import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageColor
import io
import numpy as np
import urllib.request

# הגדרת העמוד ומראה האפליקציה של אירבוריאן
st.set_page_config(page_title="Erborian Canvas · IL", layout="wide")

st.markdown("""
    <style>
    h1 { color: #C93939; font-family: 'Segoe UI', sans-serif; font-weight: 800; }
    .stButton>button { background-color: #C93939; color: white; border-radius: 8px; font-weight: 600; padding: 10px 20px; }
    .stButton>button:hover { background-color: #a82e2e; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("Erborian Graphic Studio · IL 🎨")
st.subheader("עורך לוקליזציה מהיר ונקי בפונט המותג")

# טעינת פונט Assistant הרשמי מהשרתים של גוגל
@st.cache_resource
def get_assistant_font():
    font_url = "https://github.com/google/fonts/raw/main/ofl/assistant/Assistant%5Bwght%5D.ttf"
    font_path = "Assistant.ttf"
    try:
        urllib.request.urlretrieve(font_url, font_path)
        return font_path
    except:
        return None

font_file = get_assistant_font()

# פונקציה להיפוך טקסט עבור תמיכה מלאה בעברית (RTL)
def fix_hebrew_display(text):
    lines = text.split('\n')
    fixed_lines = []
    for line in lines:
        words = line.split(' ')
        fixed_words = []
        for word in words:
            if any(c.isalpha() for c in word):  # אם יש אותיות
                fixed_words.append(word[::-1])
            else:
                fixed_words.append(word)
        fixed_lines.append(" ".join(fixed_words[::-1]))
    return "\n".join(fixed_lines)

# העלאת תמונה
uploaded_file = st.file_uploader("העלי את תמונת הקמפיין המקורית באנגלית (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img_orig = Image.open(uploaded_file).convert("RGB")
    W_orig, H_orig = img_orig.size
    
    col_canvas, col_edit = st.columns([3, 2])
    
    with col_edit:
        st.write("### 🛠️ כלים לעריכה מהירה")
        
        st.write("**1. העלמת הטקסט האנגלי (באחוזים מגודל התמונה):**")
        c1, c2, c3, c4 = st.columns(4)
        with c1: x_pos = st.slider("מיקום משמאל", 0, 100, 60)
        with c2: y_pos = st.slider("מיקום מלמעלה", 0, 100, 10)
        with c3: width_box = st.slider("רוחב הבלוק", 1, 100, 35)
        with c4: height_box = st.slider("גובה הבלוק", 1, 100, 80)
        
        st.write("---")
        st.write("**2. כתיבת תוכן בעברית (תומך בכמה שורות):**")
        heb_text = st.text_area("הקלידי את הסטטוס/התרגום המלא בעברית:", value="97% אמרו שזה עובד\nמפחית אדמומיות\nבמראה טבעי", height=120)
        
        st.write("---")
        st.write("**3. עיצוב הטקסט:**")
        cc1, cc2, cc3 = st.columns(3)
        with cc1: font_size = st.number_input("גודל גופן (px)", min_value=10, max_value=200, value=40)
        with cc2: text_color_hex = st.color_picker("צבע טקסט", value="#C93939")
        with cc3: line_spacing = st.number_input("מרווח שורות", min_value=1, max_value=50, value=15)
        
    with col_canvas:
        st.write("### 👁️ תצוגה מקדימה")
        
        img_render = img_orig.copy()
        draw = ImageDraw.Draw(img_render)
        
        bx = int((x_pos / 100) * W_orig)
        by = int((y_pos / 100) * H_orig)
        bw = int((width_box / 100) * W_orig)
        bh = int((height_box / 100) * H_orig)
        
        img_np = np.array(img_orig)
        sample_y = min(H_orig - 1, by + int(bh / 2))
        sample_x = min(W_orig - 1, bx + int(bw / 2))
        bg_color = tuple(img_np[sample_y, sample_x])
        
        draw.rectangle([bx, by, bx + bw, by + bh], fill=bg_color)
        
        if heb_text.strip():
            try:
                font = ImageFont.truetype(font_file, font_size) if font_file else ImageFont.load_default()
            except:
                font = ImageFont.load_default()
            
            text_color = ImageColor.getrgb(text_color_hex)
            ready_text = fix_hebrew_display(heb_text)
            
            current_y = by + 20
            for line in ready_text.split('\n'):
                tx = bx + (bw / 2)
                draw.text((tx, current_y), line, fill=text_color, font=font, anchor="ma")
                current_y += font_size + line_spacing
        
        st.image(img_render, use_container_width=True)
        
        buffer = io.BytesIO()
        img_render.save(buffer, format="PNG")
        st.download_button("↓ הורד גרפיקה מוכנה (PNG ברזולוציה מלאה)", data=buffer.getvalue(), file_name="erborian_clean_il.png", mime="image/png")
else:
    st.info("העלי את תמונת הקמפיין המקורית באנגלית כדי להתחיל.")
