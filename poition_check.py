import streamlit as st
import pandas as pd
import base64
import io
import plotly.express as px

# Set page title
st.set_page_config(page_title="File Upload Dashboard")

# Initialize global variable for data
if 'm2m' not in st.session_state:
    st.session_state.m2m = None

# Page header
st.title("File Upload Dashboard")
st.header("Upload POS File (Excel)")

# File uploader
uploaded_file = st.file_uploader("Drag and Drop or Select POS File", type=["xls", "xlsx"])

# Function to process the data
def parse_pos_contents(file):
    try:
        df = pd.read_excel(file)
        st.success(f"Successfully read POS file")
        
        # Data cleaning and processing steps for POS file
        new_data = []
        for index, row in df.iterrows():
            row_values = row.values
            if any(isinstance(val, str) and keyword in val for keyword in ['CE', 'PE', 'FX'] for val in row_values):
                new_data.append(row)
        
        new_data = pd.DataFrame(new_data)
        new_data.dropna(axis=1, inplace=True)
        new_data.reset_index(drop=True, inplace=True)

        # Calculate exposure and other sums
        exp = new_data[new_data['Unnamed: 7'] == 'FX']['Unnamed: 15'].sum()
        exp = exp/100000
        exp = round(exp)
        exposure = f'{exp} Lac'
        
        fx_sum = new_data[new_data['Unnamed: 7'] == 'FX']['Unnamed: 9'].sum()
        ce_sum = new_data[new_data['Unnamed: 7'] == 'CE']['Unnamed: 9'].sum()
        pe_sum = new_data[new_data['Unnamed: 7'] == 'PE']['Unnamed: 9'].sum()
        
        if abs(fx_sum) == abs(ce_sum) == abs(pe_sum):
            position = 'Matched'
        else:
            position = 'Not Matched'

        return new_data, exposure, fx_sum, ce_sum, pe_sum, position
    
    except Exception as e:
        st.error(f"Error parsing POS file: {e}")
        return None, None, None, None, None, None

# Process uploaded file
if uploaded_file is not None:
    pos_data, exposure, fx_sum, ce_sum, pe_sum, position = parse_pos_contents(uploaded_file)
    
    if pos_data is not None:
        # Store data in session state
        st.session_state.m2m = pos_data
        
        # Display info in expander
        with st.expander("View Summary Information", expanded=True):
            st.write(f"Total Exposure: {exposure}")
            st.write(f"Sum for FX: {fx_sum}")
            st.write(f"Sum for CE: {ce_sum}")
            st.write(f"Sum for PE: {pe_sum}")
            st.write(f"Position: {position}")
        
        # Create and display the bar chart
        filtered_data = pos_data[pos_data['Unnamed: 7'] == 'FX'].sort_values(by=['Unnamed: 17'])
        filtered_data = filtered_data[filtered_data['Unnamed: 9'] != 0]
        
        if not filtered_data.empty:
            fig = px.bar(
                filtered_data, 
                x="Unnamed: 0", 
                y="Unnamed: 17",
                labels={'Unnamed: 0': 'Stocks', 'Unnamed: 17': 'M2M'},
                title="M2M"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data available for plotting after filtering.")
        
        # Display raw data table
        with st.expander("View Raw Data", expanded=False):
            st.dataframe(pos_data)
    else:
        st.error("Error processing POS file.")
else:
    st.info("Please upload the POS Excel file.")