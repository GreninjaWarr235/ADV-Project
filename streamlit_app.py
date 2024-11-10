import streamlit as st
import pandas as pd
import pickle
import os
import matplotlib.pyplot as plt
import seaborn as sns
import requests

def load_dataframe(temp_file_path):
    if temp_file_path and os.path.exists(temp_file_path):
        with open(temp_file_path, 'rb') as f:
            df = pickle.load(f)
            return df
    return None

def load_visualization_info(vis_file_path):
    if vis_file_path and os.path.exists(vis_file_path):
        with open(vis_file_path, 'rb') as f:
            visualization_info = pickle.load(f)
            return visualization_info
    return None

# Streamlit app
st.title("Dynamic Data Visualization")

temp_file_path = os.getenv("TEMP_FILE_PATH")
df = load_dataframe(temp_file_path)

if df is not None:
    st.success("Data Loaded Successfully")
    st.dataframe(df)

    # Load visualization_info from the environment-specified file path
    vis_file_path = os.getenv("VISUALIZATION_INFO_PATH")
    visualization_info = load_visualization_info(vis_file_path)

    if visualization_info:
        # Retrieve visualization details
        vis_type = visualization_info.get("type")
        x_axis = visualization_info.get("x_axis")
        y_axis = visualization_info.get("y_axis")
        query_text = visualization_info.get("query")  

        st.subheader(f"User Query: {query_text}")
        st.subheader(f"Recommended Chart Type: {vis_type}")

        if vis_type.lower() == "bar chart" and x_axis:
            st.bar_chart(df[x_axis].value_counts())
    
        elif vis_type.lower() == "box plot" and x_axis and y_axis:
            fig, ax = plt.subplots()
            sns.boxplot(data=df, x=x_axis, y=y_axis, ax=ax)
            st.pyplot(fig)

        elif vis_type.lower() == "line chart" and x_axis and y_axis:
            st.line_chart(df.groupby(x_axis)[y_axis].mean())

        elif vis_type.lower() == "pie chart" and x_axis:
            pie_data = df[x_axis].value_counts()
            fig, ax = plt.subplots()
            pie_data.plot.pie(autopct='%1.1f%%', ax=ax)
            ax.set_ylabel("")
            plt.title(f'Pie chart of {x_axis}')
            st.pyplot(fig)

        elif vis_type.lower() == "violin plot" and x_axis and y_axis:
            fig, ax = plt.subplots()
            sns.violinplot(data=df, x=x_axis, y=y_axis, ax=ax)
            st.pyplot(fig)

        elif vis_type.lower() == "area plot" and x_axis and y_axis:
            st.area_chart(df.groupby(x_axis)[y_axis].sum())

        elif vis_type.lower() == "scatter plot" and x_axis and y_axis:
            fig, ax = plt.subplots()
            sns.scatterplot(data=df, x=x_axis, y=y_axis, ax=ax)
            st.pyplot(fig)

        # Add more visualization types as needed...
else:
    st.error("No DataFrame found. Please upload a file through the main app.")

if st.button("Clean Up"):
    cleanup_response = requests.post("http://127.0.0.1:5000/cleanup")  

    if cleanup_response.status_code == 200:
        st.success("Session closed. You may now close this tab.")
    else:
        st.error("Failed to clean up. Please try again.")
