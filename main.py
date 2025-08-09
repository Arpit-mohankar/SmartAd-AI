import yaml
import json
import pandas as pd
from pathlib import Path
import os
from dotenv import load_dotenv

from src.scraper import WebsiteScraper
from src.keyword_research import SERPKeywordResearcher
from src.data_processor import KeywordDataProcessor
from src.ad_group_builder import AdGroupBuilder
from src.llm_helper import LLMHelper

load_dotenv()

class SEMKeywordPipeline:
    def __init__(self, config_path: str = None, config_dict: dict = None):
        """
        Initialize pipeline with either config file path OR config dictionary
        Args:
            config_path: Path to YAML config file (for CLI usage)
            config_dict: Configuration dictionary (for Streamlit usage)
        """
        if config_dict:
            # Use config dictionary directly (from Streamlit)
            self.config = config_dict
        elif config_path:
            # Load from YAML file (for CLI usage)  
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            # Default fallback to config.yaml
            try:
                with open('config.yaml', 'r') as f:
                    self.config = yaml.safe_load(f)
            except FileNotFoundError:
                raise ValueError("Either provide config_path or config_dict parameter")
        
        # Initialize components
        self.scraper = WebsiteScraper()
        self.keyword_researcher = SERPKeywordResearcher()
        self.data_processor = KeywordDataProcessor(self.config)
        self.ad_group_builder = AdGroupBuilder(self.config)
        self.llm_helper = LLMHelper()

    def run_pipeline(self):
        """Execute the complete SEM keyword pipeline - returns data for direct download"""
        
        print("🚀 Starting AdSmart AI Pipeline...")
        
        # Step 1: Scrape websites
        print("\n📄 Step 1: Scraping websites...")
        brand_content = self.scraper.scrape_website(self.config['brand']['website'])
        competitor_content = self.scraper.scrape_website(self.config['competitor']['website'])
        
        # Step 2: Generate seed keywords
        print("\n🌱 Step 2: Generating seed keywords...")
        if self.config['keyword_settings']['mode'] == 'minimal_content':
            seed_keywords = self.llm_helper.generate_seed_keywords(brand_content, competitor_content)
        else:
            # Extract from content directly
            seed_keywords = (self.scraper.extract_products_services(brand_content) +
                           self.scraper.extract_products_services(competitor_content))
        
        print(f"Generated {len(seed_keywords)} seed keywords")
        
        # Step 3: Research keywords using SERP API
        print("\n🔍 Step 3: Researching keywords with SERP API...")
        raw_keywords = self.keyword_researcher.get_keyword_ideas(
            seed_keywords, 
            self.config['geo_targeting']['country']
        )
        
        # Add competitor keywords
        competitor_keywords = self.keyword_researcher.get_competitor_keywords(
            self.config['competitor']['website']
        )
        if competitor_keywords:
            competitor_keyword_data = self.keyword_researcher._get_keyword_metrics(
                competitor_keywords[:20],  # Limit for API costs
                self.config['geo_targeting']['country']
            )
            raw_keywords.extend(competitor_keyword_data)
        
        print(f"Found {len(raw_keywords)} raw keywords")
        
        # Step 4: Process and filter keywords
        print("\n⚙️ Step 4: Processing keywords...")
        
        # Deduplicate
        unique_keywords = self.data_processor.deduplicate_keywords(raw_keywords)
        
        # Filter by search volume
        filtered_keywords = self.data_processor.filter_keywords(unique_keywords)
        
        # Add location variants
        location_keywords = self.data_processor.add_location_variants(
            filtered_keywords, 
            self.config['service_locations']
        )
        
        # Score keywords
        scored_keywords = self.data_processor.score_keywords(location_keywords)
        
        # Step 5: Build ad groups
        print("\n📊 Step 5: Building ad groups...")
        ad_groups = self.ad_group_builder.build_ad_groups(scored_keywords)
        
        # Generate summary
        summary = self.ad_group_builder.generate_ad_group_summary(ad_groups)
        
        # Step 6: Generate download files (in-memory)
        print("\n💾 Step 6: Preparing download files...")
        download_files = self.data_processor.generate_download_files(ad_groups, summary, scored_keywords)
        
        print(f"\n✅ Pipeline completed! Generated {len(download_files)} files for download")
        
        return ad_groups, summary, download_files

if __name__ == "__main__":
    # CLI usage example
    pipeline = SEMKeywordPipeline(config_path='config.yaml')
    ad_groups, summary, download_files = pipeline.run_pipeline()
    
    # For CLI usage, you can still save files if needed
    print("\n📁 Available download files:")
    for filename in download_files.keys():
        print(f"  - {filename}")
