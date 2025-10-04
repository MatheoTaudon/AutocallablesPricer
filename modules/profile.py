import streamlit as st
import os
import base64

BLOOMBERG_BG = "#000000"
BLOOMBERG_ORANGE = "#FFA500"
BLOOMBERG_BLUE = "#1F77B4"    
BLOOMBERG_YELLOW = "#FFD700"
BLOOMBERG_TEXT = "#FFFFFF"
BORDER_COLOR = "#808080"
BORDER_COLOR2 = "#303030" 

def apply_custom_styles():
    st.markdown(
        f"""
        <style>
            /* --- Arrière-plan général --- */
            body {{
                background-color: {BLOOMBERG_BG};
                color: {BLOOMBERG_TEXT};
            }}
            div.block-container {{
                padding-top: 20px;
            }}

            .title {{
                font-size: 40px;
                font-weight: bold;
                text-align: center;
                color: {BLOOMBERG_ORANGE};
                margin-top: 20px;
                margin-bottom: 20px;
            }}
            
            /* Style pour les conteneurs d'icônes */
            .icon-container {{
                display: flex;
                align-items: center;
                margin-bottom: 15px;
            }}
            
            .icon-container img {{
                width: 24px;
                height: 24px;
                margin-right: 10px;
            }}
        </style>
        """,
        unsafe_allow_html=True
    )

def get_binary_file_downloader_html(file_path, file_label):
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{os.path.basename(file_path)}" style="color:#D9D9D9; text-decoration:none;">{file_label}</a>'
    return href

def tab():
    col1, col2, col3 = st.columns([4, 5, 1])
    
    with col2:
        # LinkedIn
        st.markdown(
            """
            <div class="icon-container">
                <img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" alt="LinkedIn Icon"> 
                <a href="https://www.linkedin.com/in/mathéo-taudon-36aa92250/" target="_blank" style="color:#D9D9D9; text-decoration:none;">
                    LinkedIn - Mathéo Taudon
                </a>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)

        # Email
        st.markdown(
            """
            <div class="icon-container">
                <img src="https://cdn-icons-png.flaticon.com/512/732/732200.png" alt="Mail Icon"> 
                <span style="color:#D9D9D9;">matheo.taudon@ieseg.fr</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
        st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
        

        # CV 
        file_path = "CV/Resume_Matheo.pdf"
        
        if os.path.exists(file_path):
            cv_link = get_binary_file_downloader_html(file_path, "CV available here")
            st.markdown(
                f"""
                <div class="icon-container" style="display: flex; align-items: center;">
                    <img src="https://cdn-icons-png.flaticon.com/512/337/337946.png" alt="CV Icon" width="30" height="30" style="margin-right: 10px;"> 
                    {cv_link}
                </div>
                """, 
                unsafe_allow_html=True
            )
        else:
            st.warning("⚠️ Fichier CV introuvable")
            st.write("Contenu du dossier : ", os.listdir("src/pages/files"))  # Debugging

def main():
    apply_custom_styles()   

    # Afficher le titre
    st.markdown('<div class="title">Profile</div>', unsafe_allow_html=True)
    st.markdown("<div style='height: 90px;'></div>", unsafe_allow_html=True)

    # Afficher le tableau de contacts
    tab()

if __name__ == "__main__":
    main()


