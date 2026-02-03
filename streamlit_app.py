import streamlit as st
import pandas as pd
import zipfile
import io
import os

st.set_page_config(page_title="Lead CSV Processor", page_icon="📋", layout="wide")

st.title("📋 Automated Lead CSV Processor")
st.markdown("Upload your leads CSV file for automatic processing")

# Define columns to delete
COLUMNS_TO_DELETE = [
    # Basic Lead Info
    'display_name', 'description', 'url', 'status_id', 'status_label',
    
    # Primary Contact Info
    'primary_contact_name', 'primary_contact_title', 'primary_contact_primary_phone', 
    'primary_contact_primary_phone_type', 'primary_contact_other_phones', 
    'primary_contact_primary_email', 'primary_contact_primary_email_type', 
    'primary_contact_other_emails', 'primary_contact_primary_url', 'primary_contact_other_urls',
    
    # Custom Property Fields
    'custom.Aggr_Lot_Count', 'custom.Aggregate Discount', 'custom.Alternate_APN',
    'custom.Building_Sqft', 'custom.Census_Tract', 
    'custom.County_Assessed_Value', 'custom.County_Market_Value', 'custom.Date_Transfer',
    'custom.Evaluation', 'custom.Evaluation_Checklist_Completed', 'custom.Improvement_%',
    'custom.Land_ID_URL', 'custom.Last_Loan_Date_Recording', 'custom.Last_Loan_Due_Date',
    'custom.Last_Loan_Value', 'custom.Latitude', 'custom.Lead_Type', 'custom.LMS_Sale_Date',
    'custom.LMS_Sale_Doc', 'custom.LMS_Sale_Price', 'custom.Longitude', 'custom.Mail_Drop_Date',
    'custom.Mail_Type', 'custom.Market_Price', 'custom.Offer_Percent', 'custom.Offer_Price',
    'custom.Owner_Name_2', 'custom.Prop_Address', 'custom.Prop_City', 'custom.Prop_Zip',
    'custom.Property_Address_Full', 'custom.Property_Land_Use', 'custom.Property_Subdivision',
    'custom.Property_Tax', 'custom.Range', 'custom.Range_Offer_Amount', 'custom.Response_Method',
    'custom.Salutation', 'custom.Section', 'custom.Seller_Name', 'custom.Seller_Provided_Price',
    'custom.Township', 'custom.Use_Code_Std_Ctgr_Desc', 'custom.Use_Code_Std_Desc',
    'custom.Val_Market', 'custom.Val_Transfer', 'custom.Yr_Blt', 'custom.Zoning',
    
    # System Fields
    'created_by', 'created_by_name', 'updated_by', 'updated_by_name', 'date_created', 
    'date_updated', 'html_url',
    
    # Address Fields (2-5)
    'address_2_address_1', 'address_2_address_2', 'address_2_city', 'address_2_state', 
    'address_2_zip', 'address_2_country', 'address_3_address_1', 'address_3_address_2', 
    'address_3_city', 'address_3_state', 'address_3_zip', 'address_3_country',
    'address_4_address_1', 'address_4_address_2', 'address_4_city', 'address_4_state', 
    'address_4_zip', 'address_4_country', 'address_5_address_1', 'address_5_address_2', 
    'address_5_city', 'address_5_state', 'address_5_zip', 'address_5_country'
]

# Function to get all opportunity value columns dynamically
def get_opportunity_columns(df):
    opportunity_cols = []
    patterns = [
        'avg_annual_', 'avg_monthly_', 'avg_annualized_', 'avg_one_time_',
        'max_annual_', 'max_monthly_', 'max_annualized_', 'max_one_time_',
        'min_annual_', 'min_monthly_', 'min_annualized_', 'min_one_time_',
        'total_annual_', 'total_monthly_', 'total_annualized_', 'total_one_time_'
    ]
    
    for col in df.columns:
        if any(pattern in col for pattern in patterns):
            opportunity_cols.append(col)
        elif col in ['active_opportunity_value_summary', 'lost_opportunity_value_summary', 
                     'won_opportunity_value_summary', 'total_opportunity_value_summary']:
            opportunity_cols.append(col)
    
    return opportunity_cols

# Function to get activity/communication columns dynamically
def get_activity_columns(df):
    activity_cols = []
    patterns = [
        'email_last_', 'first_call_', 'first_communication_', 'first_completed_',
        'first_received_', 'first_sent_', 'first_sms_', 'last_activity_',
        'last_call_', 'last_communication_', 'last_completed_', 'last_email_',
        'last_incoming_', 'last_lead_', 'last_note_', 'last_opportunity_',
        'last_outgoing_', 'last_received_', 'last_sent_', 'last_sms_',
        'last_voicemail_', 'next_task_', 'num_', 'primary_opportunity_'
    ]
    
    for col in df.columns:
        if any(pattern in col for pattern in patterns):
            activity_cols.append(col)
    
    return activity_cols

# File upload
uploaded_file = st.file_uploader("Choose your leads CSV file", type="csv")

if uploaded_file is not None:
    try:
        # Read the CSV file
        df = pd.read_csv(uploaded_file)
        
        st.subheader("📊 Original Data Info")
        st.write(f"**Total rows:** {len(df):,}")
        st.write(f"**Total columns:** {len(df.columns):,}")
        
        # Get dynamic columns to delete
        opportunity_cols = get_opportunity_columns(df)
        activity_cols = get_activity_columns(df)
        
        # Combine all columns to delete
        all_columns_to_delete = COLUMNS_TO_DELETE + opportunity_cols + activity_cols
        
        # Only delete columns that actually exist in the dataframe
        existing_columns_to_delete = [col for col in all_columns_to_delete if col in df.columns]
        
        st.write(f"**Columns to delete:** {len(existing_columns_to_delete):,}")
        
        # Delete columns
        working_df = df.drop(columns=existing_columns_to_delete, errors='ignore')
        
        st.write(f"**Remaining columns:** {len(working_df.columns):,}")
        
        # Sort by custom.Mail_CallRail
        sort_column = 'custom.Mail_CallRail'
        if sort_column in working_df.columns:
            working_df = working_df.sort_values(by=sort_column, ascending=True)
            
            # Get unique values in the sort column
            unique_values = working_df[sort_column].unique()
            
            # Handle NaN values
            unique_values_clean = [val for val in unique_values if pd.notna(val)]
            has_nan = any(pd.isna(val) for val in unique_values)
            
            st.subheader("🔄 Processing Results")
            st.write(f"**Sorted by:** {sort_column}")
            st.write(f"**Unique values found:** {len(unique_values_clean) + (1 if has_nan else 0)}")
            
            if unique_values_clean:
                for val in unique_values_clean:
                    count = len(working_df[working_df[sort_column] == val])
                    st.write(f"  • {val}: {count:,} records")
            
            if has_nan:
                nan_count = len(working_df[working_df[sort_column].isna()])
                st.write(f"  • Empty/Missing values: {nan_count:,} records")
            
            # Create files for each unique value
            files_created = {}
            
            # Process each unique value
            for val in unique_values_clean:
                subset_df = working_df[working_df[sort_column] == val]
                filename = f"leads_{str(val).replace('/', '_').replace(' ', '_')}.csv"
                csv_data = subset_df.to_csv(index=False)
                files_created[filename] = csv_data
            
            # Handle NaN/empty values if they exist
            if has_nan:
                subset_df = working_df[working_df[sort_column].isna()]
                filename = "leads_empty_mail_callrail.csv"
                csv_data = subset_df.to_csv(index=False)
                files_created[filename] = csv_data
            
            # Show remaining columns for reference
            with st.expander("📋 View Remaining Columns"):
                st.write("**Columns kept in the output files:**")
                for i, col in enumerate(sorted(working_df.columns), 1):
                    st.write(f"{i}. {col}")
            
            # Download section
            st.subheader("📥 Download Processed Files")
            
            if len(files_created) == 1:
                # Single file download
                filename, csv_data = list(files_created.items())[0]
                st.download_button(
                    label=f"📄 Download {filename}",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv"
                )
            else:
                # Multiple files - create a zip
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for filename, csv_data in files_created.items():
                        zip_file.writestr(filename, csv_data)
                
                zip_buffer.seek(0)
                
                st.download_button(
                    label=f"📦 Download All Files ({len(files_created)} files in ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name="processed_leads_files.zip",
                    mime="application/zip"
                )
                
                # Individual file downloads
                st.write("**Or download individual files:**")
                cols = st.columns(min(3, len(files_created)))
                for i, (filename, csv_data) in enumerate(files_created.items()):
                    with cols[i % 3]:
                        st.download_button(
                            label=f"📄 {filename}",
                            data=csv_data,
                            file_name=filename,
                            mime="text/csv",
                            key=f"download_{i}"
                        )
            
            # Summary
            st.subheader("✅ Processing Summary")
            st.write(f"• **Original file:** {len(df):,} rows, {len(df.columns):,} columns")
            st.write(f"• **Deleted:** {len(existing_columns_to_delete):,} columns")
            st.write(f"• **Sorted by:** {sort_column}")
            st.write(f"• **Created:** {len(files_created)} output file(s)")
            
        else:
            st.error(f"Column '{sort_column}' not found in the uploaded file!")
            st.write("Available columns:", list(working_df.columns))
            
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        st.write("Please make sure you've uploaded a valid CSV file.")

else:
    st.info("👆 Please upload your leads CSV file to start processing")
    
    # Instructions
    st.markdown("### 🔧 What this app does automatically:")
    st.markdown("""
    1. **Deletes** all unnecessary columns (200+ columns removed)
    2. **Sorts** data by `custom.Mail_CallRail` column
    3. **Splits** into separate files based on each unique Mail_CallRail value
    4. **Handles** any number of different Mail_CallRail values dynamically
    5. **Creates** a ZIP file if multiple output files are generated
    
    **No configuration needed** - just upload and download!
    """)