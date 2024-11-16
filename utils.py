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
    
    prompt = f"You are a data visualization assistant. Given the following user query: '{query_text}', and the columns of the dataset: '{valid_columns}'" \
         "determine the type of visualization needed. Provide the columns involved and the visualization type (like bar chart, box plot, line chart, pie chart, violin plot, area plot, scatter plot, spider chart).\n\n" \
         "Example Queries:\n" \
         "- 'How many males and females are there in the data?'\n" \
         "- 'Is gender affecting marks in exams?'\n" \
         "- 'What is the trend of sales over the years?'\n" \
         "- 'Show the distribution of exam scores.'\n" \
         "- 'What percentage of the population belongs to each age group?'\n" \
         "- 'Compare the performance of students across different subjects.'\n\n" \
         "Response format should be given as follows (please note that it shouldn't be anything other than this, the labels are as it is and the values do not include any punctuations or special characters, and the axes should use the exact column names as given in the dataframe without any modifications or changes):\n" \
         "- Visualization type: [Type of visualization]\n" \
         "- X-axis: [Exact column name (case sensitive) as in the dataframe]\n" \
         "- Y-axis: [Exact column name (case sensitive) as in the dataframe]\n" \
         "- Additional notes: [Any extra information, if applicable]"

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