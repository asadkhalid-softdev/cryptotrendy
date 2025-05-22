import os
import pandas as pd
from datetime import datetime
import json

class ExcelExporter:
    def __init__(self, output_file='cryptos.xlsx'):
        self.output_file = output_file
        
    def save_analysis(self, analysis_result, raw_data=None):
        """Save analysis results and raw data to Excel file."""
        if not analysis_result or 'analysis' not in analysis_result:
            print("Excel Exporter: No analysis data provided.")
            return False

        analysis_list = analysis_result.get('analysis', [])
        if not analysis_list:
            print("Excel Exporter: Analysis list is empty.")
            # Optionally save raw data even if analysis is empty
            # return False # Or proceed to save raw data if needed

        try:
            # --- Prepare Analysis Sheet Data ---
            analysis_df = pd.DataFrame(analysis_list)

            # Check if formatted data (which includes RSI) is available in raw_data
            formatted_list = raw_data.get('formatted_for_gpt') if raw_data else None

            if formatted_list:
                formatted_df = pd.DataFrame(formatted_list)
                # Ensure 'symbol' column exists for merging
                if 'symbol' in formatted_df.columns and 'coin_symbol' in analysis_df.columns:
                    # Merge analysis score/reason with the input data used for analysis
                    merged_df = pd.merge(formatted_df, analysis_df, left_on='symbol', right_on='coin_symbol', how='left')
                    # Select and order columns for the final sheet
                    # Define desired columns, including RSI if present
                    desired_columns = [
                        'symbol', 'name', 'breakout_score', 'reason',
                        'price', 'market_cap_rank', 'market_cap', 'volume_24h',
                        'price_change_24h', 'price_change_7d', 'is_trending'
                    ]
                    # Add RSI columns if they exist in the merged dataframe
                    if 'rsi_1d' in merged_df.columns:
                        desired_columns.append('rsi_1d')
                    if 'rsi_7d' in merged_df.columns:
                        desired_columns.append('rsi_7d')

                    # Filter out columns not present in the merged_df to avoid errors
                    final_columns = [col for col in desired_columns if col in merged_df.columns]
                    final_df = merged_df[final_columns]

                    # Sort by breakout score (descending), handling potential N/A or string scores
                    final_df['breakout_score_numeric'] = pd.to_numeric(final_df['breakout_score'], errors='coerce')
                    final_df = final_df.sort_values(by='breakout_score_numeric', ascending=False, na_position='last')
                    final_df = final_df.drop(columns=['breakout_score_numeric']) # Drop helper column

                else:
                    print("Excel Exporter: Missing 'symbol' or 'coin_symbol' column for merging analysis data.")
                    # Fallback to using only the analysis results
                    final_df = analysis_df
            else:
                 # Fallback to using only the analysis results if formatted data isn't available
                 final_df = analysis_df
                 # Sort by score if possible
                 if 'breakout_score' in final_df.columns:
                    final_df['breakout_score_numeric'] = pd.to_numeric(final_df['breakout_score'], errors='coerce')
                    final_df = final_df.sort_values(by='breakout_score_numeric', ascending=False, na_position='last')
                    final_df = final_df.drop(columns=['breakout_score_numeric'])


            # --- Prepare Raw Data Sheet Data ---
            raw_data_df = None
            if raw_data:
                # Convert complex data structures (like lists/dicts within raw_data values) to JSON strings
                serializable_raw_data = {}
                for key, value in raw_data.items():
                    try:
                        # Attempt to serialize complex types, keep others as is
                        if isinstance(value, (dict, list)):
                             serializable_raw_data[key] = json.dumps(value, default=str) # Use default=str for non-serializable items like datetime
                        else:
                             serializable_raw_data[key] = value
                    except Exception as json_e:
                         print(f"Excel Exporter: Could not serialize raw data key '{key}'. Error: {json_e}")
                         serializable_raw_data[key] = f"Error serializing data: {json_e}"

                # Create DataFrame from the single dictionary entry
                try:
                    # Wrap the dictionary in a list to create a single-row DataFrame
                    raw_data_df = pd.DataFrame([serializable_raw_data])
                except Exception as df_e:
                    print(f"Excel Exporter: Error creating DataFrame for raw data. Error: {df_e}")
                    raw_data_df = pd.DataFrame([{"error": f"Could not create raw data DataFrame: {df_e}"}])


            # --- Save to Excel ---
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            analysis_sheet_name = f'Analysis_{timestamp_str}'
            raw_data_sheet_name = f'RawData_{timestamp_str}'

            # Check if file exists to append sheets or create new file
            if os.path.exists(self.output_file):
                mode = 'a'
                if_sheet_exists = 'replace' # Or 'new' if you want unique timestamped sheets always
            else:
                mode = 'w'
                if_sheet_exists = None # Not needed for write mode

            try:
                with pd.ExcelWriter(self.output_file, mode=mode, engine='openpyxl', if_sheet_exists=if_sheet_exists) as writer:
                    if not final_df.empty:
                        final_df.to_excel(writer, sheet_name=analysis_sheet_name, index=False)
                        print(f"  - Analysis data saved to sheet: {analysis_sheet_name}")
                    else:
                        print(f"  - Analysis data frame was empty, sheet '{analysis_sheet_name}' not created.")

                    # Save raw data if available
                    if raw_data_df is not None and not raw_data_df.empty:
                        raw_data_df.to_excel(writer, sheet_name=raw_data_sheet_name, index=False)
                        print(f"  - Raw data saved to sheet: {raw_data_sheet_name}")

                print(f"Excel Exporter: Data saved successfully to {self.output_file}")
                return True

            except Exception as e:
                 # Handle potential errors during Excel writing (e.g., file locked)
                 print(f"  ❌ Error saving to Excel file '{self.output_file}': {e}")
                 # Try saving with a fallback name if it's a permission issue maybe?
                 try:
                     fallback_file = f"cryptos_fallback_{timestamp_str}.xlsx"
                     with pd.ExcelWriter(fallback_file, engine='openpyxl') as writer:
                         if not final_df.empty: final_df.to_excel(writer, sheet_name=analysis_sheet_name, index=False)
                         if raw_data_df is not None: raw_data_df.to_excel(writer, sheet_name=raw_data_sheet_name, index=False)
                     print(f"  ℹ️ Data saved to fallback file: {fallback_file}")
                     return True
                 except Exception as fallback_e:
                     print(f"  ❌ Error saving to fallback Excel file: {fallback_e}")
                     return False


        except Exception as e:
            print(f"  ❌ Error preparing data for Excel export: {e}")
            import traceback
            traceback.print_exc() # Print stack trace for debugging
            return False 