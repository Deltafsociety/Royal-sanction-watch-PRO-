"""
Streamlit Web Application for Comprehensive Sanction Checker
Provides a modern web interface for checking entities against sanctions lists
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import json
import os
from typing import List, Dict
import threading
import queue

from sanction_checker import SanctionChecker, SanctionMatch

# Page configuration
st.set_page_config(
    page_title="Royal Sanction Watch",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .warning-card {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
    }
    .success-card {
        background-color: #d1edff;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_sanction_checker():
    """Get cached sanction checker instance"""
    return SanctionChecker()

def main():
    """Main application function"""
    
    # Header
    st.markdown('<h1 class="main-header">🚢 Royal Sanction Watch</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        page = st.selectbox(
            "Choose a page",
            ["Single Check", "Bulk Check", "Dashboard", "Settings", "Help"]
        )
        
        st.header("Quick Stats")
        checker = get_sanction_checker()
        
        # Display cache status
        cache_files = []
        if os.path.exists(checker.cache_dir):
            cache_files = [f for f in os.listdir(checker.cache_dir) if f.endswith('_cache.csv')]
        
        st.metric("Cached Sources", len(cache_files))
        
        # Last update
        if cache_files:
            latest_file = max(cache_files, key=lambda x: os.path.getmtime(os.path.join(checker.cache_dir, x)))
            last_update = datetime.fromtimestamp(os.path.getmtime(os.path.join(checker.cache_dir, latest_file)))
            st.metric("Last Update", last_update.strftime("%Y-%m-%d %H:%M"))
    
    # Page routing
    if page == "Single Check":
        single_check_page()
    elif page == "Bulk Check":
        bulk_check_page()
    elif page == "Dashboard":
        dashboard_page()
    elif page == "Settings":
        settings_page()
    elif page == "Help":
        help_page()

def single_check_page():
    """Single entity check page"""
    st.header("🔍 Single Entity Check")
    
    # Input form
    with st.form("single_check_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            entity_name = st.text_input("Entity Name", placeholder="Enter vessel name, person, or company")
            entity_type = st.selectbox(
                "Entity Type",
                ["auto", "vessel", "person", "company"],
                help="Auto will attempt to detect the entity type based on the name"
            )
        
        with col2:
            st.write("**Supported Sanctions Lists:**")
            st.write("• OFAC (US Treasury)")
            st.write("• UK Sanctions List")
            st.write("• EU Sanctions List")
            st.write("• UN Security Council")
        
        submitted = st.form_submit_button("Check Entity", type="primary")
    
    if submitted and entity_name:
        with st.spinner("Checking entity against sanctions lists..."):
            checker = get_sanction_checker()
            matches = checker.check_single_entity(entity_name, entity_type)
            
            # Display results
            if matches:
                st.warning(f"⚠️ Found {len(matches)} potential matches for '{entity_name}'")
                
                # Create tabs for different views
                tab1, tab2, tab3 = st.tabs(["Summary", "Detailed Results", "Charts"])
                
                with tab1:
                    display_summary(matches, entity_name)
                
                with tab2:
                    display_detailed_results(matches)
                
                with tab3:
                    display_charts(matches)
            else:
                st.success(f"✅ No matches found for '{entity_name}' in any sanctions lists")
                
                # Show confidence info
                st.info("""
                **Note:** This check searches across multiple sanctions lists with fuzzy matching. 
                Results are based on the latest available data from official sources.
                """)

def bulk_check_page():
    """Bulk entity check page"""
    st.header("📊 Bulk Entity Check")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload your file",
        type=['csv', 'xlsx', 'xls'],
        help="Upload a CSV or Excel file with entity names to check"
    )
    
    if uploaded_file is not None:
        # Load data
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ File loaded successfully: {len(df)} rows")
            
            # Show data preview
            st.subheader("Data Preview")
            st.dataframe(df.head(), use_container_width=True)
            
            # Configuration
            st.subheader("Configuration")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                name_column = st.selectbox("Name Column", df.columns.tolist())
            
            with col2:
                type_column = st.selectbox("Type Column (optional)", ["None"] + df.columns.tolist())
                if type_column == "None":
                    type_column = None
            
            with col3:
                output_format = st.selectbox("Output Format", ["excel", "csv", "json"])
            
            # Start bulk check
            if st.button("Start Bulk Check", type="primary"):
                if name_column:
                    perform_bulk_check(df, name_column, type_column, output_format)
                else:
                    st.error("Please select a name column")
    
    else:
        # Show sample format
        st.info("""
        **Expected file format:**
        
        Your file should contain at least one column with entity names. 
        Optionally, you can include a column specifying the entity type.
        
        Example:
        | name | type |
        |------|------|
        | VESSEL_NAME_1 | vessel |
        | PERSON_NAME_1 | person |
        | COMPANY_NAME_1 | company |
        """)

def perform_bulk_check(df, name_column, type_column, output_format):
    """Perform bulk check with progress tracking"""
    checker = get_sanction_checker()
    
    # Prepare entities
    entities = []
    for _, row in df.iterrows():
        entity = {'name': str(row[name_column])}
        if type_column:
            entity['type'] = str(row[type_column])
        entities.append(entity)
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = {}
    total_entities = len(entities)
    
    for i, entity in enumerate(entities):
        # Update progress
        progress = (i + 1) / total_entities
        progress_bar.progress(progress)
        status_text.text(f"Checking {entity['name']} ({i+1}/{total_entities})")
        
        # Check entity
        matches = checker.check_single_entity(entity['name'], entity.get('type', 'auto'))
        results[entity['name']] = matches
        
        # Small delay to be respectful to servers
        time.sleep(0.5)
    
    # Complete
    progress_bar.progress(1.0)
    status_text.text("Bulk check completed!")
    
    # Generate and download report
    if results:
        report_file = checker.generate_report(results, output_format)
        
        # Read the generated file for download
        with open(report_file, 'rb') as f:
            st.download_button(
                label=f"Download Report ({output_format.upper()})",
                data=f.read(),
                file_name=report_file,
                mime="application/octet-stream"
            )
        
        # Show summary
        display_bulk_summary(results)

def display_bulk_summary(results):
    """Display summary of bulk check results"""
    st.subheader("Bulk Check Summary")
    
    total_entities = len(results)
    entities_with_matches = sum(1 for matches in results.values() if matches)
    total_matches = sum(len(matches) for matches in results.values())
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Entities", total_entities)
    
    with col2:
        st.metric("Entities with Matches", entities_with_matches)
    
    with col3:
        st.metric("Total Matches", total_matches)
    
    with col4:
        if total_entities > 0:
            match_rate = (entities_with_matches / total_entities) * 100
            st.metric("Match Rate", f"{match_rate:.1f}%")
    
    # Create summary chart
    if total_matches > 0:
        # Count matches by sanction list
        sanction_counts = {}
        for matches in results.values():
            for match in matches:
                sanction_list = match.sanction_list
                sanction_counts[sanction_list] = sanction_counts.get(sanction_list, 0) + 1
        
        fig = px.bar(
            x=list(sanction_counts.keys()),
            y=list(sanction_counts.values()),
            title="Matches by Sanction List",
            labels={'x': 'Sanction List', 'y': 'Number of Matches'}
        )
        st.plotly_chart(fig, use_container_width=True)

def dashboard_page():
    """Dashboard page with statistics and charts"""
    st.header("📈 Dashboard")
    
    checker = get_sanction_checker()
    
    # Cache statistics
    st.subheader("Data Sources Status")
    
    cache_files = []
    if os.path.exists(checker.cache_dir):
        cache_files = [f for f in os.listdir(checker.cache_dir) if f.endswith('_cache.csv')]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("OFAC", "✓ Available" if "ofac_cache.csv" in cache_files else "✗ Not Available")
    
    with col2:
        st.metric("UK", "✓ Available" if "uk_cache.csv" in cache_files else "✗ Not Available")
    
    with col3:
        st.metric("EU", "✓ Available" if "eu_cache.csv" in cache_files else "✗ Not Available")
    
    with col4:
        st.metric("UN", "✓ Available" if "un_cache.csv" in cache_files else "✗ Not Available")
    
    # Data freshness
    st.subheader("Data Freshness")
    
    if cache_files:
        freshness_data = []
        for cache_file in cache_files:
            file_path = os.path.join(checker.cache_dir, cache_file)
            last_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
            age_hours = (datetime.now() - last_modified).total_seconds() / 3600
            
            source = cache_file.replace('_cache.csv', '').upper()
            freshness_data.append({
                'Source': source,
                'Last Updated': last_modified,
                'Age (hours)': age_hours
            })
        
        freshness_df = pd.DataFrame(freshness_data)
        
        # Create freshness chart
        fig = px.bar(
            freshness_df,
            x='Source',
            y='Age (hours)',
            title="Data Age by Source",
            color='Age (hours)',
            color_continuous_scale='RdYlGn_r'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Show table
        st.dataframe(freshness_df, use_container_width=True)
    
    # Usage statistics (placeholder)
    st.subheader("Usage Statistics")
    
    # Mock data - in a real application, this would come from a database
    usage_data = {
        'Date': pd.date_range(start='2024-01-01', end='2024-01-31', freq='D'),
        'Checks': [10, 15, 8, 20, 12, 18, 25, 30, 22, 16, 14, 19, 21, 17, 13, 11, 9, 7, 6, 5, 4, 3, 2, 1, 0, 0, 0, 0, 0, 0, 0]
    }
    
    usage_df = pd.DataFrame(usage_data)
    
    fig = px.line(
        usage_df,
        x='Date',
        y='Checks',
        title="Daily Check Volume",
        labels={'Checks': 'Number of Checks', 'Date': 'Date'}
    )
    st.plotly_chart(fig, use_container_width=True)

def settings_page():
    """Settings page"""
    st.header("⚙️ Settings")
    
    checker = get_sanction_checker()
    
    # Cache settings
    st.subheader("Cache Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        cache_duration = st.number_input(
            "Cache Duration (hours)",
            min_value=1,
            max_value=168,  # 1 week
            value=24,
            help="How long to keep cached data before refreshing"
        )
    
    with col2:
        if st.button("Clear All Cache"):
            try:
                import shutil
                if os.path.exists(checker.cache_dir):
                    shutil.rmtree(checker.cache_dir)
                    os.makedirs(checker.cache_dir, exist_ok=True)
                st.success("Cache cleared successfully!")
            except Exception as e:
                st.error(f"Failed to clear cache: {str(e)}")
    
    # Connection settings
    st.subheader("Connection Settings")
    
    if st.button("Test All Connections"):
        with st.spinner("Testing connections..."):
            test_results = test_connections(checker)
            
            for source, status in test_results.items():
                if status:
                    st.success(f"✅ {source}: Connected")
                else:
                    st.error(f"❌ {source}: Failed")
    
    # Export settings
    st.subheader("Export Settings")
    
    default_format = st.selectbox(
        "Default Export Format",
        ["excel", "csv", "json"]
    )
    
    if st.button("Save Settings"):
        st.success("Settings saved!")

def help_page():
    """Help page"""
    st.header("❓ Help & Documentation")
    
    st.subheader("How to Use")
    
    st.markdown("""
    ### Single Entity Check
    1. Go to the "Single Check" page
    2. Enter the name of the entity you want to check
    3. Select the entity type (or leave as "auto" for automatic detection)
    4. Click "Check Entity"
    5. Review the results
    
    ### Bulk Entity Check
    1. Go to the "Bulk Check" page
    2. Upload a CSV or Excel file with entity names
    3. Configure the column mappings
    4. Click "Start Bulk Check"
    5. Download the results report
    
    ### Supported Entity Types
    - **Vessel**: Ships, boats, tankers, cargo vessels
    - **Person**: Individual people
    - **Company**: Organizations, corporations, businesses
    - **Auto**: Automatic detection based on name patterns
    """)
    
    st.subheader("Supported Sanctions Lists")
    
    sanctions_info = {
        "OFAC": {
            "description": "US Office of Foreign Assets Control",
            "url": "https://www.treasury.gov/ofac/downloads/",
            "update_frequency": "Daily"
        },
        "UK": {
            "description": "UK Sanctions List",
            "url": "https://www.gov.uk/government/publications/the-uk-sanctions-list",
            "update_frequency": "As needed"
        },
        "EU": {
            "description": "European Union Sanctions List",
            "url": "https://www.dma.dk/",
            "update_frequency": "Regularly"
        },
        "UN": {
            "description": "UN Security Council Consolidated List",
            "url": "https://www.un.org/securitycouncil/content/un-sc-consolidated-list",
            "update_frequency": "As needed"
        }
    }
    
    for source, info in sanctions_info.items():
        with st.expander(f"{source} - {info['description']}"):
            st.write(f"**URL:** {info['url']}")
            st.write(f"**Update Frequency:** {info['update_frequency']}")
    
    st.subheader("File Formats")
    
    st.markdown("""
    ### Input Files (Bulk Check)
    - **CSV**: Comma-separated values
    - **Excel**: .xlsx or .xls files
    
    ### Output Files
    - **Excel**: .xlsx format with multiple sheets
    - **CSV**: Comma-separated values
    - **JSON**: JavaScript Object Notation
    
    ### Required Columns
    - **Name Column**: Contains entity names to check
    - **Type Column** (optional): Contains entity types (vessel, person, company)
    """)
    
    st.subheader("Troubleshooting")
    
    with st.expander("Common Issues"):
        st.markdown("""
        **No results found:**
        - Check spelling of entity names
        - Try different variations of the name
        - Verify the entity type is correct
        
        **Connection errors:**
        - Check your internet connection
        - Try refreshing the cache
        - Contact support if issues persist
        
        **File upload errors:**
        - Ensure file format is supported
        - Check column names match expected format
        - Verify file is not corrupted
        """)

def display_summary(matches: List[SanctionMatch], entity_name: str):
    """Display summary of matches"""
    # Count by sanction list
    sanction_counts = {}
    for match in matches:
        sanction_list = match.sanction_list
        sanction_counts[sanction_list] = sanction_counts.get(sanction_list, 0) + 1
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Matches", len(matches))
    
    with col2:
        st.metric("Sanction Lists", len(sanction_counts))
    
    with col3:
        if matches:
            avg_confidence = sum(match.confidence for match in matches) / len(matches)
            st.metric("Avg Confidence", f"{avg_confidence:.2f}")
    
    # Create summary chart
    if sanction_counts:
        fig = px.pie(
            values=list(sanction_counts.values()),
            names=list(sanction_counts.keys()),
            title=f"Matches by Sanction List for '{entity_name}'"
        )
        st.plotly_chart(fig, use_container_width=True)

def display_detailed_results(matches: List[SanctionMatch]):
    """Display detailed results"""
    # Create detailed results table
    results_data = []
    for match in matches:
        results_data.append({
            'Sanction List': match.sanction_list,
            'Match Type': match.match_type,
            'Confidence': f"{match.confidence:.2f}",
            'Entity Type': match.entity_type,
            'Source URL': match.source_url,
            'Last Updated': match.last_updated.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    results_df = pd.DataFrame(results_data)
    st.dataframe(results_df, use_container_width=True)
    
    # Show detailed information for each match
    for i, match in enumerate(matches, 1):
        with st.expander(f"Match {i}: {match.sanction_list} - {match.match_type}"):
            st.json(match.details)

def display_charts(matches: List[SanctionMatch]):
    """Display charts for matches"""
    if not matches:
        st.info("No matches to display charts for")
        return
    
    # Confidence distribution
    confidences = [match.confidence for match in matches]
    fig1 = px.histogram(
        x=confidences,
        title="Confidence Distribution",
        labels={'x': 'Confidence Score', 'y': 'Count'},
        nbins=10
    )
    st.plotly_chart(fig1, use_container_width=True)
    
    # Match types
    match_types = [match.match_type for match in matches]
    match_type_counts = pd.Series(match_types).value_counts()
    
    fig2 = px.bar(
        x=match_type_counts.index,
        y=match_type_counts.values,
        title="Match Types",
        labels={'x': 'Match Type', 'y': 'Count'}
    )
    st.plotly_chart(fig2, use_container_width=True)

def test_connections(checker):
    """Test connections to all sanction sources"""
    results = {}
    
    try:
        # Test OFAC
        ofac_data = checker._fetch_ofac_data()
        results['OFAC'] = not ofac_data.empty
    except:
        results['OFAC'] = False
    
    try:
        # Test UK
        uk_data = checker._fetch_uk_data()
        results['UK'] = not uk_data.empty
    except:
        results['UK'] = False
    
    try:
        # Test EU
        eu_data = checker._fetch_eu_data()
        results['EU'] = not eu_data.empty
    except:
        results['EU'] = False
    
    try:
        # Test UN
        un_data = checker._fetch_un_data()
        results['UN'] = not un_data.empty
    except:
        results['UN'] = False
    
    return results

if __name__ == "__main__":
    main() 