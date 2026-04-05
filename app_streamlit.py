import streamlit as st
import os
import uuid
import json
from PIL import Image
from gradio_client import Client, handle_file

# ------------------ Config ------------------
st.set_page_config(page_title="Virtual Wardrobe", layout="wide")

BASE_DIR = os.getcwd()
WARDROBE_DIR = os.path.join(BASE_DIR, "wardrobe")
DB_PATH = os.path.join(BASE_DIR, "wardrobe.json")

os.makedirs(WARDROBE_DIR, exist_ok=True)

# ------------------ Styles ------------------
st.markdown("""
<style>
.card {
    background-color: #ffffff;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}
.title {
    font-size: 28px;
    font-weight: 600;
    color: #1f2937;
}
.subtitle {
    font-size: 16px;
    color: #6b7280;
}
.section-title {
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ------------------ Data ------------------
def load_data():
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=4)

# ------------------ Sidebar ------------------
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Select Section", ["Home", "Wardrobe", "Try-On"])

# ------------------ HOME ------------------
if menu == "Home":
    st.markdown('<div class="title">Virtual Wardrobe</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Digital wardrobe management and AI-based try-on system</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Overview</div>', unsafe_allow_html=True)
    st.write("Upload clothing items, manage your wardrobe, and visualize outfits using AI-powered try-on technology.")
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Wardrobe Management</div>', unsafe_allow_html=True)
        st.write("Store and organize your clothing items in a structured digital format.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Virtual Try-On</div>', unsafe_allow_html=True)
        st.write("Generate realistic outfit visualizations using AI models.")
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------ WARDROBE ------------------
elif menu == "Wardrobe":
    st.markdown('<div class="title">Wardrobe</div>', unsafe_allow_html=True)

    # Upload card
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Upload Item</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Select an image", label_visibility="collapsed")

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, width=200)

        if st.button("Save Item"):
            uid = str(uuid.uuid4())
            filename = f"{uid}.jpg"
            path = os.path.join(WARDROBE_DIR, filename)

            img.convert("RGB").save(path)

            data = load_data()
            data[uid] = filename
            save_data(data)

            st.success("Item saved successfully")

    st.markdown('</div>', unsafe_allow_html=True)

    # Display wardrobe
    data = load_data()

    st.markdown('<div class="section-title">Saved Items</div>', unsafe_allow_html=True)

    cols = st.columns(4)

    for i, (k, v) in enumerate(data.items()):
        img_path = os.path.join(WARDROBE_DIR, v)

        with cols[i % 4]:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.image(img_path)

            if st.button("Delete", key=k):
                os.remove(img_path)
                data.pop(k)
                save_data(data)
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

# ------------------ TRY-ON ------------------
elif menu == "Try-On":
    st.markdown('<div class="title">Virtual Try-On</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-title">Person Image</div>', unsafe_allow_html=True)
        person = st.file_uploader("Upload person image", key="person")

    with col2:
        st.markdown('<div class="section-title">Clothing Image</div>', unsafe_allow_html=True)
        cloth = st.file_uploader("Upload clothing image", key="cloth")

    if st.button("Generate"):
        if not person or not cloth:
            st.error("Both images are required")
        else:
            try:
                person_path = "person.jpg"
                cloth_path = "cloth.jpg"

                Image.open(person).convert("RGB").save(person_path)
                Image.open(cloth).convert("RGB").save(cloth_path)

                client = Client("phitran/fashion-virtual-tryon")

                result = client.predict(
                    human_img_path=handle_file(person_path),
                    garm_img_path=handle_file(cloth_path),
                    api_name="/process_image"
                )

                output_path = result["path"]

                st.markdown('<div class="section-title">Result</div>', unsafe_allow_html=True)
                st.image(output_path)

            except Exception as e:
                st.error(f"Processing failed: {e}")

    st.markdown('</div>', unsafe_allow_html=True)