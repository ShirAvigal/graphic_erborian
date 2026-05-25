import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageColor
import io
import numpy as np
import json
from google.cloud import vision

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
st.subheader("מערכת לוקליזציה אוטומטית מבוססת Google Vision AI")

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
    ymin, ymax = max(0, y - 4), min(h_img, y + h + 4)
    xmin, xmax = max(0, x - 4), min(w_img, x + w + 4)
    roi = img_np[ymin:ymax, xmin:xmax]
    if roi.size == 0: return (255, 255, 255)
    avg = roi.mean(axis=(0, 1))
    return (int(avg[0]), int(avg[1]), int(avg[2]))

# חיבור ל-Google Cloud Vision באמצעות העלאת קובץ ה-JSON
st.sidebar.write("### הגדרות חיבור ל-Google AI")
uploaded_json = st.sidebar.file_uploader("העלי את קובץ ה-JSON של גוגל קלאוד", type=["json"])

# העלאת תמונת המוצר במרכז
uploaded_file = st.file_uploader("העלי את תמונת הקמפיין המקורית באנגלית (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file and uploaded_json:
    # אם העלו תמונה חדשה לגמרי - ננקה את הזיכרון הישן
    if st.session_state.current_file != uploaded_file.name:
        st.session_state.detected_blocks = []
        st.session_state.selected_id = None
        st.session_state.current_file = uploaded_file.name

    # טעינת מפתחות גוגל בזיכרון
    info = json.load(uploaded_json)
    client = vision.ImageAnnotatorClient.from_service_account_info(info)
    
    img_orig = Image.open(uploaded_file).convert("RGB")
    img_np = np.array(img_orig)
    W_orig, H_orig = img_orig.size
    
    # אם אין עדיין בלוקים בזיכרון - נריץ זיהוי אוטומטי
    if not st.session_state.detected_blocks:
        with st.spinner("Google AI סורק את התמונה ומעלים את האנגלית..."):
            file_bytes = uploaded_file.getvalue()
            image = vision.Image(content=file_bytes)
            response = client.text_detection(image=image)
            texts = response.text_annotations
            
            if texts:
                for idx, text in enumerate(texts[1:]):
                    vertices = text.bounding_poly.vertices
                    xs = [v.x for v in vertices if v.x is not None]
                    ys = [v.y for v in vertices if v.y is not None]
                    
                    if xs and ys:
                        x, y = min(xs), min(ys)
                        w, h = max(xs) - x, max(ys) - y
                        
                        st.session_state.detected_blocks.append({
                            "id": idx + 1,
                            "eng": text.description,
                            "heb": "", 
                            "x": x, "y": y, "w": w, "h": h,
                            "font_size": int(h * 0.9) if h > 10 else 20,
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
                bg_color = sample_bg_color(img_np, block["x"], block["y"], block["w"], block["h"])
                draw.rectangle([block["x"], block["y"], block["x"] + block["w"], block["y"] + block["h"]], fill=bg_color)
                
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
    st.info("כדי להתחיל את הקסם: 1. העלי את קובץ ה-JSON של גוגל בסרגל הצידי -> 2. העלי את תמונת המוצר כאן במרכז.")
