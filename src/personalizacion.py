import streamlit as st
import os
import base64

# Función para cargar y aplicar el CSS
def load_css(file_name):
    try:
        with open(file_name, "r") as f:
            css_content = f.read()

        background_img_path = os.path.join("images", "background.jpg")
        aemet_logo_path = os.path.join("images", "aemet.png")
        bg_b64 = get_base64_image(background_img_path)
        if bg_b64:
            # Asegúrate de usar el tipo MIME correcto (jpeg, png, etc.)
            css_content = css_content.replace('url("/images/background.jpg")', f"url('data:image/jpeg;base64,{bg_b64}')")
        else:
            css_content = css_content.replace('url("/images/background.jpg")', 'none') # O un color de respaldo si no carga
        st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)

        if aemet_logo_path:
            aemet_b64 = get_base64_image(aemet_logo_path)
            if aemet_b64:
                 st.markdown(
                    f'<img src="data:image/png;base64,{aemet_b64}" class="aemet-logo">',
                    unsafe_allow_html=True)
            else:
                st.image("https://www.aemet.es/imagenes_en/cabecera/logo_aemet_128.png", 
                         caption="Logo AEMET", width=200)

    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo CSS en la ruta: {file_name}")
    except Exception as e:
        st.error(f"Error inesperado al cargar el CSS: {e}")

def get_base64_image(image_path):
    try:
        # Abre el archivo de imagen en modo binario
        with open(image_path, "rb") as img_file:
            # Lee el contenido y lo codifica a Base64
            encoded_string = base64.b64encode(img_file.read()).decode()
            return encoded_string
    except FileNotFoundError:
        st.error(f"Error: La imagen no se encuentra en la ruta: {image_path}")
        return None
    except Exception as e:
        st.error(f"Error al procesar la imagen {image_path}: {e}")
        return None