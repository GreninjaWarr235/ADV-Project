import os
from dotenv import load_dotenv
import openai
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

load_dotenv()

openai.api_key = os.getenv("COSMOSRP_API_KEY")
openai.base_url = "https://api.pawan.krd/cosmosrp/v1"

def interpret_query(df, query_text):
    valid_columns = df.columns.tolist()
    
    prompt = f"""
    You are a data visualization assistant. Given the following user query: '{query_text}', and the columns of the dataset: '{valid_columns}', please determine the type of visualization needed. You must provide the response in the following exact format:
    1. Visualization type: [Type of visualization: Bar Chart, Line Chart, Pie Chart, Boxplot, Violin Plot, Scatter Plot]
    2. X-axis: [Exact column name (case-sensitive) as in the dataset]
    3. Y-axis: [Exact column name (case-sensitive) as in the dataset]
    4. Additional notes: [Any extra information, if applicable]
    
    Important guidelines:
    - If only one column is required for the visualization (in the case of a pie chart), mention the column name for value counts in the X-axis and you can leave the Y-axis field empty (DO NOT WRITE 'Count').
    - The response should include only the specified labels, and the values must not contain any punctuation or special characters.
    - The exact column names (case-sensitive) must be used as they appear in the dataset—do not modify, alter or add any column names in any way, even if there are typos or inconsistencies in the query.
    - The response must strictly follow the format provided without any deviations.
    - You must ensure that the visualization type is appropriate for the query and the columns listed.
    
    Example Queries:
    - 'How many males and females are there in the data?'
    - 'Is gender affecting marks in exams?'
    - 'What is the trend of sales over the years?'
    - 'Show the distribution of exam scores.'
    - 'What percentage of the population belongs to each age group?'
    - 'Compare the performance of students across different subjects.'
    
    Please ensure the response matches the format given below, and avoid any other types of outputs.
    
    Response Format Example:
    - Visualization type: [Pie Chart]
    - X-axis: [Gender]
    - Y-axis: [""]
    - Additional notes: [None]
    """

    try:
        response = openai.chat.completions.create(
            model="cosmosrp",
            messages=[
                {"role": "system", "content": "You are a data visualization assistant."},
                {"role": "user", "content": prompt}
            ],
        )
        if response and hasattr(response, "choices") and len(response.choices) > 0:
            interpretation = response.choices[0].message.content
            print(f"Interpretation: {interpretation}")
            if interpretation:
                return interpretation
        else:
            print("No valid content in response.")
    except Exception as e:
        return f"Error interpreting the query: {e}"

def parse_visualization_info(interpretation):
    if not interpretation:
        return None

    info = {}
    try:
        lines = interpretation.split("\n")
        for line in lines:
            if "Visualization type:" in line:
                info["type"] = line.split(":")[1].strip()
            elif "X-axis:" in line:
                info["x_axis"] = line.split(":")[1].strip()
            elif "Y-axis:" in line:
                info["y_axis"] = line.split(":")[1].strip()
            elif "Additional notes:" in line:
                info["notes"] = line.split(":")[1].strip()
        return info
    except Exception as e:
        st.error(f"Error parsing visualization info: {e}")
        return None

def generate_visualization(df, vis_info):
    vis_type = vis_info.get("type")
    x_axis = vis_info.get("x_axis")
    y_axis = vis_info.get("y_axis")
    if not vis_type or not x_axis or (vis_type not in ["Pie Chart"] and not y_axis):
        st.error("Incomplete visualization details from response.")
        return

    plt.figure(figsize=(10, 6))
    try:
        if vis_type.lower() == "bar chart":
            sns.barplot(x=df[x_axis], y=df[y_axis])
        elif vis_type.lower() == "line chart":
            sns.lineplot(x=df[x_axis], y=df[y_axis])
        elif vis_type.lower() == "pie chart":
            df[x_axis].value_counts().plot.pie(autopct='%1.1f%%')
        elif vis_type.lower() == "boxplot" or vis_type.lower() == "box plot":
            sns.boxplot(x=df[x_axis], y=df[y_axis])
        elif vis_type.lower() == "violin plot":
            sns.violinplot(x=df[x_axis], y=df[y_axis])
        elif vis_type.lower() == "scatter plot":
            sns.scatterplot(x=df[x_axis], y=df[y_axis])
        else:
            st.error("Unsupported visualization type!")
        st.pyplot(plt)
    except Exception as e:
        st.error(f"Error generating visualization: {e}")

st.title("Interactive Data Visualization Assistant")

# Step 1: Upload Dataset
st.header("Step 1: Upload Your Dataset")
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file:
    data = pd.read_csv(uploaded_file)
    st.write("Preview of the Uploaded Dataset:")
    st.dataframe(data)

    # Step 2: Enter Query
    st.header("Step 2: Enter Your Query for Visualization")
    user_query = st.text_area("Enter your query (e.g., 'How many houses are without air conditioning?'):")

    if st.button("Generate Visualization"):
        if user_query.strip():
            st.write("Processing query...")
            
            interpretation = interpret_query(data, user_query)
            if interpretation:
                st.subheader("Suggested Interpretation:")
                st.write(interpretation)

                vis_info = parse_visualization_info(interpretation)
                if vis_info:
                    st.subheader("Visualization Details:")
                    st.json(vis_info)

                    st.header("Step 3: Visualization Result")
                    generate_visualization(data, vis_info)
                else:
                    st.error("Failed to parse visualization details.")
            else:
                st.error("Failed to interpret the query. Please try again.")
        else:
            st.warning("Please enter a query!")

else:
    st.info("Please upload a dataset to proceed.")

    
