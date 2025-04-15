import os
import pandas as pd
from datetime import datetime
import json

class ExcelExporter:
    def __init__(self, output_file='cryptos.xlsx'):
        self.output_file = output_file
        
    def save_analysis(self, analysis_result, raw_data=None):
        """Save analysis results to Excel file"""
        if not analysis_result:
            print("No analysis data to export")
            return False
            
        try:
            # Extract analysis data
            if 'analysis' in analysis_result:
                analysis_data = analysis_result['analysis']
            else:
                print("Analysis results not found in the provided data")
                return False
                
            # Convert to dataframe
            if isinstance(analysis_data, list):
                df = pd.DataFrame(analysis_data)
            else:
                # If single object, convert to list first
                df = pd.DataFrame([analysis_data])
                
            # Add timestamp column if not present
            if 'timestamp' not in df.columns and 'timestamp' in analysis_result:
                df['timestamp'] = analysis_result['timestamp']
                
            # Format the timestamp as human-readable date
            if 'timestamp' in df.columns:
                try:
                    df['date'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d')
                except:
                    df['date'] = datetime.now().strftime('%Y-%m-%d')
                    
            # Check if file exists to append or create
            if os.path.exists(self.output_file):
                # Load existing file
                with pd.ExcelWriter(self.output_file, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
                    df.to_excel(writer, sheet_name=f'Analysis_{datetime.now().strftime("%Y%m%d")}', index=False)
                    
                    # If raw data provided, save to different sheet
                    if raw_data:
                        # Convert complex data structures to JSON strings
                        raw_df = pd.DataFrame([{k: json.dumps(v) if isinstance(v, (dict, list)) else v 
                                               for k, v in raw_data.items()}])
                        raw_df.to_excel(writer, sheet_name=f'RawData_{datetime.now().strftime("%Y%m%d")}', index=False)
            else:
                # Create new file
                with pd.ExcelWriter(self.output_file, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name=f'Analysis_{datetime.now().strftime("%Y%m%d")}', index=False)
                    
                    # If raw data provided, save to different sheet
                    if raw_data:
                        # Convert complex data structures to JSON strings
                        raw_df = pd.DataFrame([{k: json.dumps(v) if isinstance(v, (dict, list)) else v 
                                               for k, v in raw_data.items()}])
                        raw_df.to_excel(writer, sheet_name=f'RawData_{datetime.now().strftime("%Y%m%d")}', index=False)
                        
            print(f"Analysis saved to {self.output_file}")
            return True
            
        except Exception as e:
            print(f"Error saving analysis to Excel: {e}")
            return False 