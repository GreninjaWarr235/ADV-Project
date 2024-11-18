import pandas as pd
import openai
import os
from dotenv import load_dotenv

load_dotenv()

import openai

openai.api_key = os.getenv("COSMOSRP_API_KEY")
openai.base_url = "https://api.pawan.krd/cosmosrp/v1"

def interpret_query(df, query_text):
    valid_columns = df.columns.tolist()
    
    prompt = f"""
    You are a data visualization assistant. Given the following user query: '{query_text}', and the columns of the dataset: '{valid_columns}', please determine the type of visualization needed. You must provide the response in the following exact format:
    1. Visualization type: [Type of visualization]
    2. X-axis: [Exact column name (case-sensitive) as in the dataset]
    3. Y-axis: [Exact column name (case-sensitive) as in the dataset]
    4. Additional notes: [Any extra information, if applicable]
    
    Important guidelines:
    - The response should include only the specified labels, and the values must not contain any punctuation or special characters.
    - The exact column names (case-sensitive) must be used as they appear in the dataset—do not modify or alter the column names in any way, even if there are typos or inconsistencies in the query.
    - The response must strictly follow the format provided without any deviations.
    - You must ensure that the visualization type is appropriate for the query and the columns listed.
    
    Example Queries:
    - 'How many males and females are there in the data?'
    - 'Is gender affecting marks in exams?'
    - 'What is the trend of sales over the years?'
    - 'Show the distribution of exam scores.'
    - 'What percentage of the population belongs to each age group?'
    - 'Compare the performance of students across different subjects.'
    
    Please ensure the response matches the format given below, and avoid any other types of outputs.\n
    
    Response Format Example:
    - Visualization type: [Bar chart]
    - X-axis: [Gender]
    - Y-axis: [Count]
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
        print(f"Error interpreting query: {e}")
        return "Error interpreting the query."

    # Extracting the response content from the API response
    interpretation = response.choices[0].message['content'].strip()
    return interpretation

def parse_visualization_info(interpretation, query_text):
    if not interpretation:
        print("Interpretation is None or empty.")
        return None
    else:
        print(f"Interpretation: {interpretation}")

    try:
        lines = interpretation.split("\n")
        info = {}
        info["query"] = query_text
        for line in lines:
            if "Visualization type:" in line or "Visualization Type:" in line or "visualization type:" in line:
                info["type"] = line.split(":")[1].strip()
            elif "X-axis:" in line:
                info["x_axis"] = line.split(":")[1].strip()
            elif "Y-axis:" in line:
                info["y_axis"] = line.split(":")[1].strip()
        if info:
            print(f"this is info: {info}")
            return info
        else:
            print("No valid visualization info parsed.")
            return None
    except Exception as e:
        print(f"Error parsing visualization info: {e}")
        return None

def load_dataframe_from_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == '.csv':
        return pd.read_csv(file_path)
    elif file_extension in ['.xls', '.xlsx']:
        return pd.read_excel(file_path)
    elif file_extension == '.json':
        return pd.read_json(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {file_extension}. Supported formats are CSV, Excel, and JSON.")

def detect_column_types(df):
    column_types = {}
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            column_types[col] = 'numeric'
        elif pd.api.types.is_categorical_dtype(df[col]) or df[col].nunique() < 10:
            column_types[col] = 'categorical'
        else:
            column_types[col] = 'text'
    return column_types