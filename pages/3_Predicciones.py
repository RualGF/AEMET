import streamlit as st




def main():
    st.title("Predicciones de temperatura")
    st.divider()
    st.write(st.context.cookies)
    st.write(st.context.headers)
    st.write("Por hacer")
if __name__ == "__main__":
    main()