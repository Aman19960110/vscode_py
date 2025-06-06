import streamlit as st
import pandas as pd
import datetime
import re
from nselib import derivatives
import pandas_market_calendars as mcal

def is_trading_day(date):
    # Get NSE calendar
    nse = mcal.get_calendar('NSE')
    
    # Check if the date is a trading day
    schedule = nse.schedule(start_date=date, end_date=date)
    return not schedule.empty

def run_analysis(date_str, month, oi_threshold, atm_percentage):
    try:
        # Convert date to required format ('DD-MM-YYYY')
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%d-%m-%Y')
        
        # Load the derivatives data
        data = derivatives.fno_bhav_copy(formatted_date)
        
        # Check if data is empty
        if data.empty:
            return None, "No data available for the selected date."
        
        # Filter data for rows containing the specified month in 'FinInstrmNm'
        data = data[data['FinInstrmNm'].str.contains(month)].copy()
        
        if data.empty:
            return None, f"No contracts found for {month}."
        
        # Calculate 'open_int' column
        data['open_int'] = data['OpnIntrst'] / data['NewBrdLotQty']
        
        # Filter data for futures contracts containing the specified month followed by 'FUT'
        fut = data[data['FinInstrmNm'].str.contains(f'{month}FUT')].copy()
        FUT = fut['FinInstrmNm'].copy()
        
        # Create a mask for specific conditions
        mask = (
            ((data['StrkPric'] >= data['UndrlygPric']) & (data['OptnTp'] == 'PE')) |
            ((data['StrkPric'] <= data['UndrlygPric']) & (data['OptnTp'] == 'CE'))
        )
        
        # Apply the mask to filter data
        df = data[mask].copy()
        
        if df.empty:
            return None, "No matching data after applying filters."
        
        # Use the user-provided ATM percentage
        atm_decimal = atm_percentage / 100
        
        # Iterate over the DataFrame rows and set 'atm_con' based on conditions with user-defined percentage
        df['atm_con'] = df.apply(
            lambda row: 'True' if (
                row['StrkPric'] <= row['UndrlygPric'] - (atm_decimal * row['UndrlygPric']) or
                row['StrkPric'] >= row['UndrlygPric'] + (atm_decimal * row['UndrlygPric'])
            ) else 'False',
            axis=1
        )
        
        # Filter data based on 'atm_con' and 'open_int'
        mask01 = df[df['atm_con'] == "True"]
        mask01 = mask01[mask01['open_int'] > oi_threshold]
        mask02 = df[df['atm_con'] == "False"]
        
        # Merge the filtered data
        df1 = pd.merge(mask01, mask02, how='outer')
        
        if df1.empty:
            return None, "No data after applying OI threshold filter."
        
        # Create a DataFrame with 'FinInstrmNm' column
        df2 = pd.DataFrame(df1['FinInstrmNm'])
        
        # Create 'copy_fin' column with modified values
        df2['copy_fin'] = df2['FinInstrmNm'].str[:-2] + 'PE'
        df2['FinInstrmNm'] = df2['FinInstrmNm'].str[:-2] + 'CE'
        
        # Add 'NRML|' prefix to 'FinInstrmNm' and 'copy_fin'
        df2['FinInstrmNm'] = 'NRML|' + df2['FinInstrmNm']
        df2['copy_fin'] = 'NRML|' + df2['copy_fin']
        
        # FIX FOR FUTURES - Create a DataFrame for futures and rename the column
        if not FUT.empty:
            FUT_df = pd.DataFrame({'fut': 'NRML|' + FUT})
        else:
            FUT_df = pd.DataFrame({'fut': []})

        # Prepare final dataframes - First create separate dataframes
        ce_df = pd.DataFrame({'All Columns': df2['FinInstrmNm']})
        pe_df = pd.DataFrame({'All Columns': df2['copy_fin']})
        fut_df = pd.DataFrame({'All Columns': FUT_df['fut']})
        
        # Concatenate all into one dataframe
        df_combined = pd.concat([ce_df, pe_df, fut_df], ignore_index=True)
        
        # Filter out rows containing 'NIFTY'
        df_filtered = df_combined[~df_combined['All Columns'].str.contains('NIFTY', na=False)].copy()
        
        # Initialize a mask with False values
        mask = pd.Series(False, index=df_filtered.index)
        
        # Update the mask if '.' is found in any object type column
        for col in df_filtered.columns:
            if df_filtered[col].dtype == object:
                mask |= df_filtered[col].str.contains('\.', na=False)
        
        # Filter the DataFrame using the inverted mask
        df5 = df_filtered[~mask]
        
        # Sort the dataframe alphabetically by 'All Columns'
        df5 = df5.sort_values(by='All Columns')
        
        return df5, None
    
    except Exception as e:
        return None, f"Error: {str(e)}"

# Set up the Streamlit app
st.set_page_config(page_title="NSE Derivatives Analysis", layout="wide")

st.title("NSE Derivatives Analysis Tool")
st.write("This app analyzes NSE derivatives data based on selected parameters.")

# Create sidebar for inputs
st.sidebar.header("Input Parameters")

# Date picker (default to today)
today = datetime.date.today()
date = st.sidebar.date_input("Select Date", today)

# Month selector
months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
current_month_index = datetime.datetime.now().month - 1
selected_month = st.sidebar.selectbox("Select Month", months, index=current_month_index)

# OI threshold
oi_threshold = st.sidebar.number_input("OI Threshold", min_value=1, value=4)

# ATM percentage - NEW PARAMETER
atm_percentage = st.sidebar.slider(
    "ATM Deviation Percentage", 
    min_value=1, 
    max_value=20, 
    value=8,
    help="Strike prices beyond this percentage from the underlying price will be considered out of the money"
)

# Sort order options
sort_ascending = st.sidebar.checkbox("Sort Ascending", value=True, help="Check for ascending order, uncheck for descending")

# Run analysis button
if st.sidebar.button("Run Analysis"):
    # Check if it's a trading day
    if not is_trading_day(date):
        st.warning(f"Selected date ({date}) may not be a trading day. Results may be unavailable.")
    
    # Convert date to string
    date_str = date.strftime('%Y-%m-%d')
    
    # Display a spinner while processing
    with st.spinner("Processing data..."):
        result_df, error = run_analysis(date_str, selected_month, oi_threshold, atm_percentage)
    
    if error:
        st.error(error)
    else:
        # Apply sorting based on user preference
        result_df = result_df.sort_values(by='All Columns', ascending=sort_ascending)
        
        st.success("Analysis completed successfully!")
        
        # Count each type using regex pattern to match at the end of string
        futures_count = result_df['All Columns'].str.contains('FUT$', regex=True).sum()
        ce_count = result_df['All Columns'].str.contains('CE$', regex=True).sum()
        pe_count = result_df['All Columns'].str.contains('PE$', regex=True).sum()
        
        # Display the results
        st.subheader("Analysis Results")
        st.dataframe(result_df)
        
        # Create download section
        st.subheader("Download Options")
        
        col1, col2 = st.columns(2)
        
        # CSV download in column 1
        with col1:
            csv = result_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"nse_derivatives_{date_str}_{selected_month}_atm{atm_percentage}.csv",
                mime="text/csv"
            )
        
        # Text file download in column 2
        with col2:
            # Convert DataFrame to plain text without index
            text_content = "\n".join(result_df['All Columns'].tolist())
            text_bytes = text_content.encode('utf-8')
            
            st.download_button(
                label="Download TXT",
                data=text_bytes,
                file_name=f"nse_derivatives_{date_str}_{selected_month}_atm{atm_percentage}.txt",
                mime="text/plain"
            )
        
        # Display additional metrics
        st.subheader("Summary")
        st.write(f"Total tokens: {len(result_df)}")
        st.write(f"- Futures: {futures_count}")
        st.write(f"- Call Options (CE): {ce_count}")
        st.write(f"- Put Options (PE): {pe_count}")
        st.write(f"Analysis parameters: Date={date}, Month={selected_month}, OI Threshold={oi_threshold}, ATM Deviation={atm_percentage}%")
        st.write(f"Sorting: {'Ascending' if sort_ascending else 'Descending'} order")
        
        # Visualize distribution
        st.subheader("Distribution")
        chart_data = pd.DataFrame({
            'Type': ['Futures', 'Call Options', 'Put Options'],
            'Count': [futures_count, ce_count, pe_count]
        })
        st.bar_chart(chart_data.set_index('Type'))

# Add explanatory information
st.sidebar.markdown("---")
st.sidebar.header("About")
st.sidebar.info(f"""
This app retrieves NSE derivatives data for a selected date and applies filters based on:
- Selected month
- Open Interest threshold
- ATM conditions (user-defined deviation from underlying price)
- PE/CE conditions

The result is a list of derivative tokens for trading strategies, including futures contracts.
""")

# Add a section explaining ATM condition
st.sidebar.markdown("---")
st.sidebar.header("How ATM Deviation Works")
st.sidebar.info(f"""
The ATM (At-The-Money) deviation percentage defines how far away from the underlying price a strike can be before it's considered significantly out of the money:

- For a {atm_percentage}% setting, strikes that are more than {atm_percentage}% above or below the underlying price will be filtered differently.
- Lower percentage = stricter filtering (closer to the money)
- Higher percentage = looser filtering (includes strikes further from the money)

Example: For an underlying price of ₹1000 with {atm_percentage}% setting:
- Strikes below ₹{1000 - (atm_percentage/100 * 1000)} or above ₹{1000 + (atm_percentage/100 * 1000)} will be considered significantly OTM
""")