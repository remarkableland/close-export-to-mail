import streamlit as st
import pandas as pd
import zipfile
import io
import os

st.set_page_config(page_title="Lead CSV Processor", page_icon="📋", layout="wide")

st.title("📋 Automated Lead CSV Processor")
st.markdown("Upload your leads CSV files for automatic processing")

# Define columns to delete
COLUMNS_TO_DELETE = [
    # Basic Lead Info
    'description', 'url', 'status_id', 'status_label',

    # Primary Contact Info
    'primary_contact_title', 'primary_contact_primary_phone',
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

# File upload - multiple files
uploaded_files = st.file_uploader(
    "Choose your leads CSV file(s)",
    type="csv",
    accept_multiple_files=True,
    help="Upload one or more CSV files to combine and process"
)

if uploaded_files:
    st.subheader("📁 Uploaded Files")
    for i, file in enumerate(uploaded_files, 1):
        st.write(f"{i}. {file.name}")

    # Process button
    if st.button("🚀 Process Files", type="primary"):
        try:
            with st.spinner("Processing..."):
                # Step 1: Load and combine all files
                st.write("**Step 1:** Loading and combining files...")

                all_dataframes = []
                total_rows = 0

                for uploaded_file in uploaded_files:
                    df = pd.read_csv(uploaded_file)
                    all_dataframes.append(df)
                    total_rows += len(df)

                # Combine all dataframes
                if len(all_dataframes) > 1:
                    combined_df = pd.concat(all_dataframes, ignore_index=True)
                    st.success(f"✅ Combined {len(uploaded_files)} files → {len(combined_df):,} total rows")
                else:
                    combined_df = all_dataframes[0]
                    st.success(f"✅ Loaded single file → {len(combined_df):,} rows")

                st.write(f"**Original columns:** {len(combined_df.columns):,}")

                # Step 2: Get dynamic columns to delete
                st.write("**Step 2:** Identifying columns to delete...")
                opportunity_cols = get_opportunity_columns(combined_df)
                activity_cols = get_activity_columns(combined_df)

                # Combine all columns to delete
                all_columns_to_delete = COLUMNS_TO_DELETE + opportunity_cols + activity_cols

                # Only delete columns that actually exist in the dataframe
                existing_columns_to_delete = [col for col in all_columns_to_delete if col in combined_df.columns]

                st.success(f"✅ Found {len(existing_columns_to_delete):,} columns to delete")

                # Step 3: Delete columns
                st.write("**Step 3:** Deleting columns...")
                working_df = combined_df.drop(columns=existing_columns_to_delete, errors='ignore')
                st.success(f"✅ Remaining columns: {len(working_df.columns):,}")

                # Step 4: Sort by custom.Mail_CallRail
                sort_column = 'custom.Mail_CallRail'
                if sort_column in working_df.columns:
                    st.write("**Step 4:** Sorting and splitting by Mail_CallRail...")
                    working_df = working_df.sort_values(by=sort_column, ascending=True)

                    # Get unique values in the sort column
                    unique_values = working_df[sort_column].unique()

                    # Handle NaN values
                    unique_values_clean = [val for val in unique_values if pd.notna(val)]
                    has_nan = any(pd.isna(val) for val in unique_values)

                    st.success(f"✅ Found {len(unique_values_clean) + (1 if has_nan else 0)} unique Mail_CallRail values")

                    # Show breakdown
                    st.subheader("📊 Mail_CallRail Breakdown")
                    if unique_values_clean:
                        for val in unique_values_clean:
                            count = len(working_df[working_df[sort_column] == val])
                            st.write(f"  • {val}: {count:,} records")

                    if has_nan:
                        nan_count = len(working_df[working_df[sort_column].isna()])
                        st.write(f"  • Empty/Missing values: {nan_count:,} records")

                    # Step 5: Create files for each unique value
                    st.write("**Step 5:** Creating output files...")
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

                    st.success(f"✅ Created {len(files_created)} output file(s)")

                    # Store in session state
                    st.session_state['files_created'] = files_created
                    st.session_state['working_df'] = working_df
                    st.session_state['processing_complete'] = True
                    st.session_state['stats'] = {
                        'original_files': len(uploaded_files),
                        'original_rows': total_rows,
                        'combined_rows': len(combined_df),
                        'columns_deleted': len(existing_columns_to_delete),
                        'final_columns': len(working_df.columns),
                        'output_files': len(files_created)
                    }

                else:
                    st.error(f"Column '{sort_column}' not found in the uploaded file(s)!")
                    st.write("Available columns:", list(working_df.columns))

        except Exception as e:
            st.error(f"Error processing files: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# Download section
if st.session_state.get('processing_complete', False):
    files_created = st.session_state['files_created']
    working_df = st.session_state['working_df']
    stats = st.session_state['stats']

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
    st.write(f"• **Files uploaded:** {stats['original_files']}")
    st.write(f"• **Total rows combined:** {stats['combined_rows']:,}")
    st.write(f"• **Columns deleted:** {stats['columns_deleted']:,}")
    st.write(f"• **Final columns per file:** {stats['final_columns']:,}")
    st.write(f"• **Output files created:** {stats['output_files']}")

elif not uploaded_files:
    st.info("👆 Please upload your leads CSV file(s) to start processing")

    # Instructions
    st.markdown("### 🔧 What this app does automatically:")
    st.markdown("""
    1. **Combines** multiple CSV files into one dataset
    2. **Deletes** all unnecessary columns (200+ columns removed)
    3. **Sorts** data by `custom.Mail_CallRail` column
    4. **Splits** into separate files based on each unique Mail_CallRail value
    5. **Creates** a ZIP file if multiple output files are generated

    **Just upload your files, click Process, and download!**
    """)
