import streamlit as st
import yaml
import json
import pandas as pd
from pathlib import Path
import os
from dotenv import load_dotenv
from main import SEMKeywordPipeline
import zipfile
import io
from datetime import datetime

# Load environment variables at the top
load_dotenv()

st.set_page_config(
    page_title="AdSmart AI",
    page_icon="🧠",
    layout="wide"
)

def check_api_keys():
    """Check if required API keys are available"""
    openai_key = os.getenv('OPENAI_API_KEY')
    serp_key = os.getenv('SERP_API_KEY')
    
    missing_keys = []
    if not openai_key:
        missing_keys.append('OPENAI_API_KEY')
    if not serp_key:
        missing_keys.append('SERP_API_KEY')
    
    return missing_keys

def create_zip_file(files_dict):
    """Create a ZIP file containing all generated files"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename, content in files_dict.items():
            if isinstance(content, str):
                zip_file.writestr(filename, content.encode('utf-8'))
            else:
                zip_file.writestr(filename, content)
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

def main():
    st.title("🧠 AdSmart AI")
    st.markdown("**Intelligent advertising, automated** - Transform manual keyword research into AI-powered campaign creation")
    
    
    
    # Check API keys first
    missing_keys = check_api_keys()
    
    if missing_keys:
        st.error(f"❌ Missing API keys in .env file: {', '.join(missing_keys)}")
        st.info("""
        **Setup Instructions:**
        1. Create a `.env` file in your project root
        2. Add your API keys:
        ```
        OPENAI_API_KEY=your_openai_api_key_here
        SERP_API_KEY=your_serp_api_key_here
        ```
        3. Restart the Streamlit app
        """)
        return
    
    # Show success message for API keys
    st.success("✅ API keys loaded successfully")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Website inputs
        st.subheader("Websites")
        brand_website = st.text_input(
            "Brand Website", 
            placeholder="https://yourbrand.com",
            help="Your company's website"
        )
        competitor_website = st.text_input(
            "Competitor Website", 
            placeholder="https://competitor.com",
            help="Main competitor's website"
        )
        
        # Locations
        st.subheader("Service Locations")
        locations_text = st.text_area(
            "Locations (one per line)",
            placeholder="Mumbai, Maharashtra\nDelhi, NCR\nBangalore, Karnataka",
            value="Mumbai, Maharashtra\nDelhi, NCR\nBangalore, Karnataka"
        )
        
        # Budgets
        st.subheader("Campaign Budgets")
        search_budget = st.number_input("Search Ads Budget (₹)", min_value=0, value=50000)
        shopping_budget = st.number_input("Shopping Ads Budget (₹)", min_value=0, value=30000)
        pmax_budget = st.number_input("PMax Ads Budget (₹)", min_value=0, value=20000)
        
        # Settings
        st.subheader("Research Settings")
        min_volume = st.number_input("Min Search Volume", min_value=0, value=500)
        mode = st.selectbox("Content Mode", ["minimal_content", "rich_content"])
        country = st.selectbox("Country", [
            "India", 
            "United States", 
            "Canada", 
            "United Kingdom", 
            "Australia"
        ])
        
        # Advanced settings
        with st.expander("⚙️ Advanced Settings"):
            conversion_rate = st.number_input("Conversion Rate", min_value=0.001, max_value=1.0, value=0.02, step=0.001)
            
            st.markdown("**Scoring Weights**")
            search_weight = st.slider("Search Volume Weight", 0.0, 1.0, 0.5, 0.1)
            competition_weight = st.slider("Competition Weight", 0.0, 1.0, 0.3, 0.1)
            cpc_weight = st.slider("CPC Weight", 0.0, 1.0, 0.2, 0.1)
            
            # Normalize weights
            total_weight = search_weight + competition_weight + cpc_weight
            if total_weight != 1.0:
                search_weight = search_weight / total_weight
                competition_weight = competition_weight / total_weight
                cpc_weight = cpc_weight / total_weight
        
        # Run button
        run_pipeline = st.button("🚀 Generate Keywords", type="primary", use_container_width=True)
        
        # Creator attribution in sidebar footer
        st.markdown("---")
        st.markdown(
            """
            <div style='text-align: center; color: #888; font-size: 12px; margin-top: 20px;'>
                💡 Created by<br><strong>Arpit Mohankar</strong>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # Main content area
    if not run_pipeline:
        st.info("👈 Configure your settings in the sidebar and click '**Generate Keywords**' to start")
        
        # Show example
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 What you'll get:")
            st.markdown("""
            - **Organized Ad Groups**: Brand, Category, Competitor, Location, Informational
            - **Keyword Metrics**: Search volume, competition, performance scores
            - **Smart Recommendations**: Match types and CPC bid ranges
            - **Ready-to-use Files**: CSV for Excel, JSON for tools, Reports for analysis
            """)
        
        with col2:
            st.markdown("### ⚡ Process:")
            st.markdown("""
            1. **AI Website Analysis** - Understands your business
            2. **Competitor Research** - Finds keyword opportunities  
            3. **SERP Data Mining** - Gets real search volumes
            4. **Smart Categorization** - Organizes into campaigns
            5. **Instant Download** - Ready-to-import files
            """)
    
    else:
        # Validate inputs
        if not all([brand_website, competitor_website]):
            st.error("❌ Please fill in both brand and competitor websites")
            return
        
        # Parse locations
        locations = [loc.strip() for loc in locations_text.split('\n') if loc.strip()]
        if not locations:
            locations = ["India"]
        
        # Create config
        config = {
            'brand': {
                'website': brand_website,
                'name': 'Brand'
            },
            'competitor': {
                'website': competitor_website,
                'name': 'Competitor'
            },
            'service_locations': locations,
            'budgets': {
                'search_ads': search_budget,
                'shopping_ads': shopping_budget,
                'pmax_ads': pmax_budget
            },
            'keyword_settings': {
                'min_search_volume': min_volume,
                'conversion_rate': conversion_rate,
                'mode': mode
            },
            'geo_targeting': {
                'country': country,
                'language': 'en'
            },
            'scoring': {
                'search_volume_weight': search_weight,
                'competition_weight': competition_weight,
                'cpc_weight': cpc_weight
            }
        }
        
        # Run pipeline
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("🔄 Initializing AI pipeline...")
            progress_bar.progress(10)
            
            pipeline = SEMKeywordPipeline(config_dict=config)
            
            status_text.text("🔄 Running keyword research...")
            progress_bar.progress(50)
            
            ad_groups, summary, download_files = pipeline.run_pipeline()
            
            progress_bar.progress(100)
            status_text.text("✅ Pipeline completed successfully!")
            
            # Display results
            display_results_and_downloads(ad_groups, summary, download_files)
            
        except Exception as e:
            st.error(f"❌ Error running pipeline: {str(e)}")
            st.exception(e)

def display_results_and_downloads(ad_groups, summary, download_files):
    """Display pipeline results with direct download options"""
    
    st.header("📊 Results & Downloads")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Keywords", summary['total_keywords'])
    
    with col2:
        st.metric("Ad Groups", summary['total_ad_groups'])
    
    with col3:
        total_volume = sum(
            details['avg_search_volume'] * details['keyword_count'] 
            for details in summary['ad_group_details'].values()
        )
        st.metric("Total Search Volume", f"{total_volume:,}")
    
    with col4:
        avg_cpc = sum(
            details['avg_cpc_start'] 
            for details in summary['ad_group_details'].values()
        ) / len(summary['ad_group_details']) if summary['ad_group_details'] else 0
        st.metric("Avg Starting CPC", f"₹{avg_cpc:.2f}")
    
    # Download Section (Most Important)
    st.subheader("📥 Download Your Files")
    
    # Create download columns
    col1, col2, col3 = st.columns(3)
    
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    with col1:
        st.markdown("#### 📋 Essential Files")
        
        # Master keywords
        if 'keywords_master.csv' in download_files:
            st.download_button(
                label="📄 All Keywords (CSV)",
                data=download_files['keywords_master.csv'],
                file_name=f"keywords_master_{timestamp}.csv",
                mime="text/csv",
                help="Complete list of all keywords with metrics",
                use_container_width=True
            )
        
        # Summary report
        if 'run_report.md' in download_files:
            st.download_button(
                label="📊 Summary Report (MD)",
                data=download_files['run_report.md'],
                file_name=f"keyword_report_{timestamp}.md",
                mime="text/markdown",
                help="Detailed analysis and top keywords",
                use_container_width=True
            )
    
    with col2:
        st.markdown("#### 📁 Ad Groups")
        
        # Individual ad group files
        ad_group_files = {k: v for k, v in download_files.items() if k.startswith('ad_group_')}
        
        for filename, content in ad_group_files.items():
            group_name = filename.replace('ad_group_', '').replace('.csv', '').replace('_', ' ').title()
            st.download_button(
                label=f"📄 {group_name}",
                data=content,
                file_name=f"{filename.replace('.csv', f'_{timestamp}.csv')}",
                mime="text/csv",
                use_container_width=True
            )
    
    with col3:
        st.markdown("#### 🔧 Technical Files")
        
        # JSON files for developers
        if 'ad_groups_search.json' in download_files:
            st.download_button(
                label="⚙️ Ad Groups (JSON)",
                data=download_files['ad_groups_search.json'],
                file_name=f"ad_groups_{timestamp}.json",
                mime="application/json",
                help="Structured data for API integration",
                use_container_width=True
            )
        
        # ZIP file with everything
        zip_data = create_zip_file(download_files)
        st.download_button(
            label="📦 Download All (ZIP)",
            data=zip_data,
            file_name=f"adsmart_ai_keywords_{timestamp}.zip",
            mime="application/zip",
            help="All files in one ZIP package",
            use_container_width=True
        )
    
    # Quick preview of results
    st.subheader("👀 Quick Preview")
    
    # Top keywords preview
    if ad_groups:
        all_keywords = []
        for keywords in ad_groups.values():
            all_keywords.extend(keywords)
        
        # Sort by score and show top 10
        top_keywords = sorted(all_keywords, key=lambda x: x['score'], reverse=True)[:10]
        
        df_preview = pd.DataFrame(top_keywords)
        df_preview = df_preview[['keyword', 'avg_monthly_searches', 'competition', 'score', 'suggested_cpc_start']]
        df_preview['avg_monthly_searches'] = df_preview['avg_monthly_searches'].apply(lambda x: f"{x:,}")
        df_preview['suggested_cpc_start'] = df_preview['suggested_cpc_start'].apply(lambda x: f"₹{x:.2f}")
        
        st.dataframe(df_preview, use_container_width=True)
    
    # Footer attribution
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 14px; margin-top: 30px;'>
            🎯 <strong>AdSmart AI</strong> - Powered by AI | Created by <strong>Arpit Mohankar</strong><br>
            <small>Transforming keyword research with artificial intelligence</small>
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
