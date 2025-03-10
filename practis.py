 # Find the correct column names dynamically
            # This is more robust than hardcoding 'Unnamed: 7', etc.
            instrument_column = None
            qty_column = None
            exposure_column = None
            m2m_column = None
            stock_column = None
            
            # Try to find the column containing 'FX', 'CE', 'PE' values
            for col in new_data.columns:
                unique_vals = new_data[col].dropna().unique()
                unique_vals_str = [str(val).upper() for val in unique_vals if isinstance(val, (str, int, float))]
                if any(val in ['FX', 'CE', 'PE'] for val in unique_vals_str):
                    instrument_column = col
                    st.info(f"Identified instrument column: {col}")
                    break
            
            if instrument_column is None:
                st.error("Could not identify column containing 'FX', 'CE', 'PE' values")
                return None, None, None, None, None, None
            
            # Try to find the quantity column (typically numeric and next to instrument column)
            cols = new_data.columns.tolist()
            try:
                idx = cols.index(instrument_column)
                potential_qty_cols = cols[idx+1:idx+3]  # Check the next couple columns
                
                for col in potential_qty_cols:
                    if pd.api.types.is_numeric_dtype(new_data[col]):
                        qty_column = col
                        st.info(f"Identified quantity column: {col}")
                        break
            except:
                pass
            
            # If we couldn't find qty_column, look for a numeric column
            if qty_column is None:
                for col in new_data.columns:
                    if pd.api.types.is_numeric_dtype(new_data[col]):
                        qty_column = col
                        st.info(f"Using numeric column for quantity: {col}")
                        break
            
            # Try to find the M2M column (typically one of the last numeric columns)
            numeric_cols = [col for col in new_data.columns if pd.api.types.is_numeric_dtype(new_data[col])]
            if numeric_cols:
                m2m_column = numeric_cols[-1]  # Assume last numeric column is M2M
                st.info(f"Using last numeric column for M2M: {m2m_column}")
                
                # Exposure is often the second-to-last numeric column
                if len(numeric_cols) > 1:
                    exposure_column = numeric_cols[-2]
                    st.info(f"Using second-to-last numeric column for exposure: {exposure_column}")
                else:
                    exposure_column = m2m_column  # Fallback
            
            # Try to find the stock name column (typically one of the first columns)
            for col in new_data.columns[:3]:  # Check first 3 columns
                if pd.api.types.is_string_dtype(new_data[col]) or new_data[col].dtype == object:
                    stock_column = col
                    st.info(f"Using column for stock names: {stock_column}")
                    break
            
            if not all([instrument_column, qty_column, m2m_column]):
                st.error("Could not identify all required columns. Please check your file format.")
                return None, None, None, None, None, None
            
            # Calculate exposure and other sums using identified columns
            try:
                fx_data = new_data[new_data[instrument_column] == 'FX']
                if exposure_column:
                    exp = fx_data[exposure_column].sum() / 100000
                    exp = round(exp)
                    exposure = f'{exp} Lac'
                else:
                    exposure = "N/A"
                
                fx_sum = new_data[new_data[instrument_column] == 'FX'][qty_column].sum()
                ce_sum = new_data[new_data[instrument_column] == 'CE'][qty_column].sum()
                pe_sum = new_data[new_data[instrument_column] == 'PE'][qty_column].sum()
                
                if abs(fx_sum) == abs(ce_sum) == abs(pe_sum):
                    position = 'Matched'
                else:
                    position = 'Not Matched'
                
                # Store the identified columns for visualization
                new_data['_instrument'] = new_data[instrument_column]
                new_data['_quantity'] = new_data[qty_column]
                new_data['_m2m'] = new_data[m2m_column]
                if stock_column:
                    new_data['_stock'] = new_data[stock_column]
                
                return new_data, exposure, fx_sum, ce_sum, pe_sum, position, stock_column, m2m_column
            
            except Exception as e:
                st.error(f"Error in calculations: {str(e)}")
                return None, None, None, None, None, None, None, None
        
        except Exception as e:
            st.error(f"Error parsing POS file: {str(e)}")
            return None, None, None, None, None, None, None, None