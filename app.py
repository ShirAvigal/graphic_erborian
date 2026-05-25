import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageColor
import io
import numpy as np

# הגדרת העמוד ומראה האפליקציה של אירבוריאן
st.set_page_config(page_title="Erborian Studio · IL", layout="wide")

st.markdown("""
    <style>
    h1 { color: #C93939; font-family: 'Segoe UI', sans-serif; font-weight: 800; }
    .stButton>button { background-color: #C93939; color: white; border-radius: 8px; font-weight: 600; }
    .stButton>button:hover { background-color: #a82e2e; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("Erborian Graphic Studio · IL")
st.subheader("עורך לוקליזציה מהיר ונקי להשקות קמפיינים")

# אתחול הזיכרון של האפליקציה
if "layers" not in st.session_state:
    st.session_state.layers = []
if "selected_id" not in st.session_state:
    st.session_state.selected_id = None

# פונקציה לדגימת צבע רקע אוטומטי מסביב לשכבה כדי למחוק את האנגלית
def sample_bg_color(img_np, x_pct, y_pct, w_pct, h_pct):
    h_img, w_img, _ = img_np.shape
    x = int((x_pct / 100) * w_img)
    y = int((y_pct / 100) * h_img)
    w = int((w_pct / 100) * w_img)
    h = int((h_pct / 100) * h_img)
    
    ymin, ymax = max(0, y - 6), min(h_img, y + h + 6)
    xmin, xmax = max(0, x - 6), min(w_img, x + w + 6)
    
    roi = img_np[ymin:ymax, xmin:xmax]
    if roi.size == 0:
        return (255, 255, 255)
    avg = roi.mean(axis=(0, 1))
    return (int(avg[0]), int(avg[1]), int(avg[2]))

# פונקציה פשוטה להיפוך סדר האותיות בעברית כדי שיוצג נכון בלי שגיאות מערכת
def reverse_hebrew(text):
    return text Gold[::-1] if any(c.isalpha() for c in text) else text

# העלאת תמונה
uploaded_file = st.file_uploader("העלי את תמונת הקמפיין המקורית באנגלית (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img_orig = Image.open(uploaded_file).convert("RGB")
    img_np = np.array(img_orig)
    W_orig, H_orig = img_orig.size
    
    col_canvas, col_edit = st.columns([3, 2])
    
    with col_edit:
        st.write("### ניהול שכבות ותרגום")
        
        if st.button("+ הוסף שכבת תרגום / מחיקה חדשה"):
            new_id = len(st.session_state.layers) + 1
            st.session_state.layers.append({
                "id": new_id, "label": f"שכבה {new_id}", "heb": "טקסט חדש בעברית",
                "x": 20.0, "y": 30.0, "w": 60.0, "h": 12.0,
                "font_size": 45, "color": "#C93939", "font_name": "Assistant", "align": "center"
            })
            st.session_state.selected_id = new_id
            st.rerun()

        if st.session_state.layers:
            options = {l["id"]: l["label"] for l in st.session_state.layers}
            sel_id = st.selectbox("בחרי שכבה לעריכה ועיצוב", options=list(options.keys()), format_func=lambda x: options[x], index=list(options.keys()).index(st.session_state.selected_id) if st.session_state.selected_id in options else 0)
            st.session_state.selected_id = sel_id
            
            lay = next(x for x in st.session_state.layers if x["id"] == sel_id)
            lay["heb"] = st.text_area("הקלידי את התרגום בעברית", value=lay["heb"])
            
            st.write("---")
            st.write("**מיקום וגודל הריבוע המוחק (%)**")
            c1, c2, c3, c4 = st.columns(4)
            with c1: lay["x"] = st.number_input("שמאל (X)", min_value=0.0, max_value=100.0, value=lay["x"], step=1.0)
            with c2: lay["y"] = st.number_input("למעלה (Y)", min_value=0.0, max_value=100.0, value=lay["y"], step=1.0)
            with c3: lay["w"] = st.number_input("רוחב (W)", min_value=1.0, max_value=100.0, value=lay["w"], step=1.0)
            with c4: lay["h"] = st.number_input("גובה (H)", min_value=1.0, max_value=100.0, value=lay["h"], step=1.0)
            
            st.write("---")
            st.write("**עיצוב הגופן**")
            cc1, cc2 = st.columns(2)
            with cc1:
                lay["font_name"] = st.selectbox("גופן מותג", ["Arial", "Assistant", "Heebo", "Rubik"], index=0)
                lay["color"] = st.color_picker("צבע טקסט", value=lay["color"])
            with cc2:
                lay["font_size"] = st.number_input("גודל גופן (px)", min_value=10, max_value=300, value=lay["font_size"])
                lay["align"] = st.selectbox("יישור שורות", ["center", "right", "left"], index=["center", "right", "left"].index(lay["align"]))
                
            if st.button("מחק שכבה זו"):
                st.session_state.layers = [x for x in st.session_state.layers if x["id"] != sel_id]
                st.session_state.selected_id = None
                st.rerun()
        else:
            st.info("לחצי על הכפתור למעלה כדי להוסיף שכבה ראשונה.")

    with col_canvas:
        st.write("### תצוגה מקדימה (Live Preview)")
        
        img_render = img_orig.copy()
        draw = ImageDraw.Draw(img_render)
        
        for l in st.session_state.layers:
            bx = int((l["x"] / 100) * W_orig)
            by = int((l["y"] / 100) * H_orig)
            bw = int((l["w"] / 100) * W_orig)
            bh = int((l["h"] / 100) * H_orig)
            
            # 1. העלמת האנגלית בצורה חלקה
            bg_color = sample_bg_color(img_np, l["x"], l["y"], l["w"], l["h"])
            draw.rectangle([bx, by, bx + bw, by + bh], fill=bg_color)
            
            # 2. כתיבת העברית
            if l["heb"].strip():
                font = ImageFont.load_default()
                text_color = ImageColor.getrgb(l["color"])
                
                # היפוך הטקסט לתצוגה נכונה בעברית
                rev_text = reverse_hebrew(l["heb"])
                
                if l["align"] == "right":
                    tx = bx + bw - 10
                    anchor = "ra"
                elif l["align"] == "center":
                    tx = bx + (bw / 2)
                    anchor = "ma"
                else:
                    tx = bx + 10
                    anchor = "la"
                
                draw.text((tx, by + (bh/4)), rev_text, fill=text_color, font=font, anchor=anchor)
            
            if st.session_state.selected_id == l["id"]:
                draw.rectangle([bx, by, bx + bw, by + bh], outline="#C93939", width=6)
                
        st.image(img_render, use_container_width=True)
        
        buffer = io.BytesIO()
        img_render.save(buffer, format="PNG")
        st.download_button("↓ הורד גרפיקה מוכנה (PNG ברזולוציה מלאה)", data=buffer.getvalue(), file_name="erborian_final_il.png", mime="image/png")
