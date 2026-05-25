import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageColor
import io
import numpy as np
import easyocr

# הגדרת העמוד ומראה האפליקציה של אירבוריאן
st.set_page_config(page_title="Erborian Auto Studio · IL", layout="wide")

st.markdown("""
    <style>
    h1 { color: #C93939; font-family: 'Segoe UI', sans-serif; font-weight: 800; }
    .stButton>button { background-color: #C93939; color: white; border-radius: 8px; font-weight: 600; }
    .stButton>button:hover { background-color: #a82e2e; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("Erborian Graphic Studio · IL 🚀")
st.subheader("מערכת לוקליזציה אוטומטית עצמאית (ללא צורך בחשבונות ענן)")

# אתחול מנוע הזיהוי בזיכרון של Streamlit (רץ רק פעם אחת כדי שלא יאט את המערכת)
@st.cache_resource
def load_ocr_reader():
    return easyocr.Reader(['en'])

reader = load_ocr_reader()

# אתחול הזיכרון של האפליקציה
if "detected_blocks" not in st.session_state:
    st.session_state.detected_blocks = []
if "selected_id" not in st.session_state:
    st.session_state.selected_id = None
if "current_file" not in st.session_state:
    st.session_state.current_file = None

# פונקציה פשוטה להיפוך סדר האותיות בעברית כדי שיוצג נכון
def reverse_hebrew(text):
    return text[::-1] if any(c.isalpha() for c in text) else text

# פונקציה לדגימת צבע רקע אוטומטי מסביב לשכבה כדי למחוק את האנגלית
def sample_bg_color(img_np, x, y, w, h):
    h_img, w_img, _ = img_np.shape
    ymin, ymax = max(0, int(y - 4)), min(h_img, int(y + h + 4))
    xmin, xmax = max(0, int(x - 4)), min(w_img, int(x + w + 4))
    roi = img_np[ymin:ymax, xmin:xmax]
    if roi.size == 0: return (255, 255, 255)
    avg = roi.mean(axis=(0, 1))
    return (int(avg[0]), int(avg[1]), int(avg[2]))

# העלאת תמונת המוצר במרכז
uploaded_file = st.file_uploader("העלי את תמונת הקמפיין המקורית באנגלית (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file:
    # אם העלו תמונה חדשה לגמרי - ננקה את הזיכרון הישן
    if st.session_state.current_file != uploaded_file.name:
        st.session_state.detected_blocks = []
        st.session_state.selected_id = None
        st.session_state.current_file = uploaded_file.name

    img_orig = Image.open(uploaded_file).convert("RGB")
    img_np = np.array(img_orig)
    W_orig, H_orig = img_orig.size
    
    # אם אין עדיין בלוקים בזיכרון - נריץ זיהוי אוטומטי
    if not st.session_state.detected_blocks:
        with st.spinner("המערכת סורקת את התמונה ומעלים את האנגלית אוטומטית..."):
            file_bytes = uploaded_file.getvalue()
            # הרצת הסורק החופשי
            results = reader.readtext(file_bytes)
            
            if results:
                for idx, (bbox, text, prob) in enumerate(results):
                    # bbox מכיל 4 פינות: [top_left, top_right, bottom_right, bottom_left]
                    x_min = min([pt[0] for pt in bbox])
                    y_min = min([pt[1] for pt in bbox])
                    x_max = max([pt[0] for pt in bbox])
                    y_max = max([pt[1] for pt in bbox])
                    
                    w = x_max - x_min
                    h = y_max - y_min
                    
                    st.session_state.detected_blocks.append({
                        "id": idx + 1,
                        "eng": text,
                        "heb": "", 
                        "x": int(x_min), "y": int(y_min), "w": int(w), "h": int(h),
                        "font_size": max(14, int(h * 0.85)),
                        "color": "#000000",
                        "align": "center"
                    })
                if st.session_state.detected_blocks:
                    st.session_state.selected_id = st.session_state.detected_blocks[0]["id"]
        st.rerun()

    # חלוקת המסך לעבודה אחרי שהזיהוי הסתיים
    if st.session_state.detected_blocks:
        col_canvas, col_edit = st.columns([3, 2])
        
        with col_edit:
            st.write("### בלוקים שזוהו אוטומטית")
            
            options = {b["id"]: f"מילה {b['id']}: {b['eng'][:15]}" for b in st.session_state.detected_blocks}
            sel_id = st.selectbox("בחרי מילה/שורה לתרגום", options=list(options.keys()), format_func=lambda x: options[x], index=list(options.keys()).index(st.session_state.selected_id) if st.session_state.selected_id in options else 0)
            st.session_state.selected_id = sel_id
            
            b = next(x for x in st.session_state.detected_blocks if x["id"] == sel_id)
            
            st.text_input("טקסט מקורי באנגלית", value=b["eng"], disabled=True)
            b["heb"] = st.text_input("הקלידי תרגום בעברית", value=b["heb"])
            
            st.write("---")
            st.write("**כוונון עיצוב וגודל**")
            c1, c2, c3 = st.columns(3)
            with c1: b["font_size"] = st.number_input("גודל גופן (px)", min_value=10, value=b["font_size"])
            with c2: b["color"] = st.color_picker("צבע טקסט", value=b["color"])
            with c3: b["align"] = st.selectbox("יישור", ["center", "right", "left"])
            
            if st.button("מחק שורה זו מהתמונה"):
                st.session_state.detected_blocks = [x for x in st.session_state.detected_blocks if x["id"] != sel_id]
                if st.session_state.detected_blocks:
                    st.session_state.selected_id = st.session_state.detected_blocks[0]["id"]
                else:
                    st.session_state.selected_id = None
                st.rerun()
                
        with col_canvas:
            st.write("### תצוגה מקדימה (Live Preview)")
            img_render = img_orig.copy()
            draw = ImageDraw.Draw(img_render)
            
            for block in st.session_state.detected_blocks:
                # 1. מחיקה אוטומטית חלקה לפי צבע הרקע סביב המילה
                bg_color = sample_bg_color(img_np, block["x"], block["y"], block["w"], block["h"])
                draw.rectangle([block["x"], block["y"], block["x"] + block["w"], block["y"] + block["h"]], fill=bg_color)
                
                # 2. כתיבת העברית
                if block["heb"].strip():
                    font = ImageFont.load_default()
                    text_color = ImageColor.getrgb(block["color"])
                    rev_text = reverse_hebrew(block["heb"])
                    
                    if block["align"] == "right":
                        tx = block["x"] + block["w"]
                    elif block["align"] == "center":
                        tx = block["x"] + (block["w"] / 2)
                    else:
                        tx = block["x"]
                        
                    draw.text((tx, block["y"]), rev_text, fill=text_color, font=font, anchor="ma")
                
                if st.session_state.selected_id == block["id"]:
                    draw.rectangle([block["x"], block["y"], block["x"] + block["w"], block["y"] + block["h"]], outline="#C93939", width=3)
            
            st.image(img_render, use_container_width=True)
            
            buffer = io.BytesIO()
            img_render.save(buffer, format="PNG")
            st.download_button("↓ הורד גרפיקה מוכנה לעבודה", data=buffer.getvalue(), file_name="erborian_fixed.png", mime="image/png")
else:
    st.info("העלי את תמונת המוצר באנגלית כאן במרכז כדי להתחיל.")
