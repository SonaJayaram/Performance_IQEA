import streamlit as st
import pandas as pd
import pyodbc
import os
import re
from langchain_core.messages import HumanMessage
from langchain_openai import AzureChatOpenAI
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

def main():
    st.title("Upload Excel File and Generate Queries")

    # File uploader to select Excel file
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])

    database_names = get_database_name_dropdown()
    print(database_names)
    selected_database = st.multiselect("Select a database", database_names)

    # Button to generate and validate queries
    if st.button("Generate and Validate Queries"):
        if uploaded_file is not None:
            get_queries_from_ai(uploaded_file,selected_database)
            html=QueryValidationAndReport()
            st.markdown(html, unsafe_allow_html=True)  # Display HTML content

            st.write("Query Generated and results are validated")

        else:
            st.error("Please upload an Excel file.")


# Main Streamlit app code)
    Prompt = st.text_input('Enter the prompt to generate sql query', '')

    if st.button("Generate sql query and validate"):
        html=get_queries_from_ai_prompt(Prompt,selected_database)
        st.markdown(html, unsafe_allow_html=True)  # Display HTML content
        st.write("Query Generated and results are validated")


def get_database_name_dropdown():
    conn = pyodbc.connect('Driver={SQL Server};'
                          'Server=qe-vm1;'
                          f'Database=Employee;'
                          'Trusted_Connection=yes;')

    cursor = conn.cursor()

    cursor.execute("SELECT name FROM master.sys.databases WHERE database_id > 4;")
    table_names = cursor.fetchall()

    return [row[0] for row in table_names]

def get_table_header(selected_database):
    #val =['Employee']
    val = selected_database
    tables = {}
    for val1 in val:
        conn = pyodbc.connect('Driver={SQL Server};'
                              'Server=qe-vm1;'
                              f'Database={val1};'
                              'Trusted_Connection=yes;')
        print(conn)
        # Create a cursor
        cursor = conn.cursor()


        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE';")
        table_names = cursor.fetchall()

        for table_name in table_names:
            table_name = table_name[0]

            cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='{table_name}';")
            columns = cursor.fetchall()
            tables[val1+'.dbo.'+table_name] = [column[0] for column in columns]

    cursor.close()
    return tables


def get_table_dataframes(selected_database):
    tables = get_table_header(selected_database)
    print(tables)
    conn = pyodbc.connect('Driver={SQL Server};'
                          'Server=qe-vm1;'
                          f'Database=Employee;'
                          'Trusted_Connection=yes;')
    dfs = {}
    for keys in tables:
        print(keys)
        df_name = f"df_{keys}"
        df = pd.read_sql_query("select * from " + keys + "", conn)
        dfs[df_name] = df  # Adding DataFrame to the dictionary with the constructed name
    print(dfs)
    return dfs


def get_queries_from_ai(uploaded_file,selected_database):
    # Access the variables
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

    # Set the environment variables explicitly if needed
    os.environ["AZURE_OPENAI_API_KEY"] = api_key
    os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint

    df=pd.read_excel(uploaded_file)
    tableHeader = get_table_header(selected_database)
    dfs = get_table_dataframes(selected_database)
    print(df)
    # Loop over the values in the DataFrame
    for index, row in df.iterrows():
        value1 = row['Queries']
        print(value1)
        val2 = "The response should be Just the sql query of microsoft sql server with double quotes for the following questions without any text to the front:"+value1 + " Get the query with the given table headers" + str(tableHeader)
        print(val2)

        if value1 == 'can you demonstrate a usage of regexp_substr on the employee table ':
            val2 = "The response should be Just the sql query of microsoft sql server with double quotes for the following questions without any text to the front:"+value1 + "with table names " + str(tableHeader) + "with the dataframe values to be compared" + str(dfs)
        model = AzureChatOpenAI(
            openai_api_version="2023-05-15",
            azure_deployment="qepracticekey",
        )
        message = HumanMessage(
            content=val2
        )
        output_value=model([message])
        print(model([message]))

        def extract_values(input_string):
            # Remove newline characters (\n)
            input_string = input_string.replace('\n', ' ').strip()
            # Extract values within quotes using regular expression
            values = re.findall(r'"([^"]*)', input_string)
            print(values)
            stringnew = values[0].replace('`', '').replace('sql', '').splitlines()
            newstring1 = stringnew[0].replace('\\n', ' ')
            newstring = re.sub(r'\\', '', newstring1)
            return newstring

        val3 = extract_values(str(output_value))
        print(val3)
        # Paste the output value in another column
        df.at[index, 'OutputColumn'] = val3

    df.to_excel('Output.xlsx', index=False)

    def get_prompt_desc():
        # Access the variables
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

        # Set the environment variables explicitly if needed
        os.environ["AZURE_OPENAI_API_KEY"] = api_key
        os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint
        df1 = pd.read_excel('output.xlsx')
        print(df1)
        # Loop over the values in the DataFrame
        for index, row in df1.iterrows():
            value1 = row['Queries']
            print(value1)
            val2 = "Can you give a one line explanation for all the prompts in the sheet and not give a query"+value1
            print(val2)

            model = AzureChatOpenAI(
                openai_api_version="2023-05-15",
                azure_deployment="qepracticekey",
            )
            message = HumanMessage(
                content=val2
            )
            output_value = model([message])
            print(model([message]))
            df1.at[index, 'Prompt'] = str(output_value)

        df1.to_excel('Output.xlsx', index=False)

    get_prompt_desc()

def get_queries_from_ai_prompt(prompt,selected_database):
    # Access the variables
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

    # Set the environment variables explicitly if needed
    os.environ["AZURE_OPENAI_API_KEY"] = api_key
    os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint

    tableHeader = get_table_header(selected_database)
    # Loop over the values in the DataFrame

    value1 = prompt
    print(value1)
    val2 = "The response should be Just the sql query of microsoft sql server with double quotes for the following questions without any text to the front:" + value1 + " Get the query with the given table headers" + str(
        tableHeader)
    print(val2)

    model = AzureChatOpenAI(
        openai_api_version="2023-05-15",
        azure_deployment="qepracticekey",
    )
    message = HumanMessage(
        content=val2
    )
    output_value = model([message])
    print(model([message]))

    def extract_values(input_string):
        # Remove newline characters (\n)
        input_string = input_string.replace('\n', ' ').strip()
        # Extract values within quotes using regular expression
        values = re.findall(r'"([^"]*)', input_string)
        print(values)
        stringnew = values[0].replace('`', '').replace('sql', '').splitlines()
        newstring1 = stringnew[0].replace('\\n', ' ')
        newstring = re.sub(r'\\', '', newstring1)
        return newstring

    val3 = extract_values(str(output_value))
    print(val3)
    # Paste the output value in another column
    valprompt = "The response should be Just the explanation of the prompt with double quotes within 20 words and not the query itself without any text to the front:" + value1


    message1 = HumanMessage(
        content=valprompt
    )
    output_valuenew = extract_values(str(model([message1])))
    print(model([message1]))
    conn = pyodbc.connect('Driver={SQL Server};'
                          'Server=qe-vm1;'
                          f'Database=Employee;'
                          'Trusted_Connection=yes;')
    try:
        cursor = conn.cursor()
        cursor.execute(val3)
        valresult = cursor.fetchall()

        if not valresult:
            print("No result from the db")
        else:
            # Limiting to first 5 results
            valresult = valresult[:5]
    except Exception as e:
        print("Error executing query:", e)
        valresult = ["Error executing query"]

    tables={}
    key = prompt, val3, output_valuenew
    if valresult==["validate the query"]:
        tables[key]=valresult
    else:
        tables[key] = [valresult[0] for vals in valresult]
    # Step 2: Process Data
    # Manipulate and process data as needed
    # Initialize the HTML content with the header
    html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Tiger ETL Tool Report</title>
            <style>
                /* Add CSS styles here */
                table {
                    border-collapse: collapse;
                    width: 100%;
                }
                th, td {
                    padding: 8px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }
                th {
                    background-color: #f2f2f2;
                }
                /* Adjust the width and enable wrapping for the results column */
                .results {
                width: 30%;
                word-wrap: break-word;
                }
            </style>
        </head>
        <body>
            <h1>Tiger ETL Tool Report</h1>
        """

    # Add Run Summary and Run Date
    run_summary = "Run Summary"
    run_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    function_name = "QueryValidationAndReport"
    function_value = "Validating the query generated from AI against DB and retrieving only the first 5 rows"

    html_content += f"<h2>{run_summary}</h2>"
    html_content += f"<p><strong>Run Date:</strong> {run_date}</p>"
    html_content += f"<p><strong>Function Name:</strong> {function_name}</p>"
    html_content += f"<p><strong>Function Value:</strong> {function_value}</p>"
    html_content += f"<h2>Results</h2>"

    # Create the table header
    html_content += "<table>"
    html_content += "<tr><th>No.</th><th>Prompt</th><th>SQL Query</th><th>Explanation</th><th>Results</th></tr>"

    # Counter for numbering prompts
    prompt_counter = 1

    # Iterate over each key-value pair in the dictionary
    for key, value in tables.items():
        # Extracting elements from the key
        prompt, sql_query, explanation = key

        # Add row for each key-value pair
        html_content += "<tr>"
        html_content += f"<td>{prompt_counter}</td>"
        html_content += f"<td>{prompt}</td>"
        html_content += f"<td>{sql_query}</td>"
        html_content += f"<td>{explanation}</td>"

        # Add results if available
        if value:
            html_content += "<td class='results'>"
            html_content += "<ul>"
            for result in value:
                html_content += f"<li>{result}</li>"
            html_content += "</ul>"
            html_content += "</td>"
        else:
            html_content += "<td>No results</td>"

        html_content += "</tr>"

        # Increment prompt counter
        prompt_counter += 1

    # Close the table and HTML content
    html_content += "</table>"
    html_content += """
        </body>
        </html>
        """

    # Step 4: Save HTML
    with open('reportcheck.html', 'w') as f:
        f.write(html_content)


    return html_content


def QueryValidationAndReport():
    # Step 1: Extract Data
    # Extract data from Excel sheets
    excel_file = 'test_data_sql_Business_Rules_New.xlsx'
    excel_data = pd.read_excel(excel_file)

    # Extract data from database
    conn = pyodbc.connect('Driver={SQL Server};'
                                  'Server=qe-vm1;'
                                  f'Database=Employee;'
                                  'Trusted_Connection=yes;')
    tables={}
    cursor = conn.cursor()
    for index, row in excel_data.iterrows():
        value1 = row['OutputColumn']
        value2=row['Queries']
        value3=row['Prompt']
        print(value1)
        cursor.execute(value1)
        val=cursor.fetchmany(5)
        key=value2,value1,value3
        tables[key]=[val[0] for vals in val]

    # Manipulate and process data as needed
    # Initialize the HTML content with the header
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tiger ETL Tool Report</title>
        <style>
            /* Add CSS styles here */
            table {
                border-collapse: collapse;
                width: 100%;
            }
            th, td {
                padding: 8px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #f2f2f2;
            }
            /* Adjust the width and enable wrapping for the results column */
            .results {
            width: 30%;
            word-wrap: break-word;
            }
        </style>
    </head>
    <body>
        <h1>Tiger ETL Tool Report</h1>
    """

    # Add Run Summary and Run Date
    run_summary = "Run Summary"
    run_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    function_name = "QueryValidationAndReport"
    function_value = "Validating the query generated from AI against DB and retrieving only the first 5 rows"

    html_content += f"<h2>{run_summary}</h2>"
    html_content += f"<p><strong>Run Date:</strong> {run_date}</p>"
    html_content += f"<p><strong>Function Name:</strong> {function_name}</p>"
    html_content += f"<p><strong>Function Value:</strong> {function_value}</p>"
    html_content += f"<h2>Results</h2>"

    # Create the table header
    html_content += "<table>"
    html_content += "<tr><th>No.</th><th>Prompt</th><th>SQL Query</th><th>Explanation</th><th>Results</th></tr>"

    # Counter for numbering prompts
    prompt_counter = 1

    # Iterate over each key-value pair in the dictionary
    for key, value in tables.items():
        # Extracting elements from the key
        prompt, sql_query, explanation = key

        # Add row for each key-value pair
        html_content += "<tr>"
        html_content += f"<td>{prompt_counter}</td>"
        html_content += f"<td>{prompt}</td>"
        html_content += f"<td>{sql_query}</td>"
        html_content += f"<td>{explanation}</td>"

        # Add results if available
        if value:
            html_content += "<td class='results'>"
            html_content += "<ul>"
            for result in value:
                html_content += f"<li>{result}</li>"
            html_content += "</ul>"
            html_content += "</td>"
        else:
            html_content += "<td>No results</td>"

        html_content += "</tr>"

        # Increment prompt counter
        prompt_counter += 1

    # Close the table and HTML content
    html_content += "</table>"
    html_content += """
    </body>
    </html>
    """

    # Step 4: Save HTML
    with open('report.html', 'w') as f:
        f.write(html_content)

    return html_content



if __name__ == "__main__":
    main()
