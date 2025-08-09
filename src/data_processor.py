import pandas as pd
from typing import List, Dict
import numpy as np
import json

class KeywordDataProcessor:
    def __init__(self, config: Dict):
        self.config = config
        self.min_volume = config['keyword_settings']['min_search_volume']
        self.scoring_weights = config['scoring']
    
    def deduplicate_keywords(self, keywords: List[Dict]) -> List[Dict]:
        """Remove duplicate keywords"""
        seen = set()
        unique_keywords = []
        
        for kw in keywords:
            keyword_normalized = kw['keyword'].lower().strip()
            if keyword_normalized not in seen:
                seen.add(keyword_normalized)
                unique_keywords.append(kw)
        
        print(f"Deduplicated keywords: {len(keywords)} -> {len(unique_keywords)}")
        return unique_keywords
    
    def filter_keywords(self, keywords: List[Dict]) -> List[Dict]:
        """Filter keywords based on minimum search volume"""
        filtered = []
        for kw in keywords:
            if kw['avg_monthly_searches'] >= self.min_volume:
                filtered.append(kw)
        
        print(f"Filtered keywords: {len(keywords)} -> {len(filtered)} (min volume: {self.min_volume})")
        return filtered
    
    def score_keywords(self, keywords: List[Dict]) -> List[Dict]:
        """Score keywords based on search volume, competition, and CPC"""
        if not keywords:
            return keywords
        
        # Extract metrics for normalization
        volumes = [kw['avg_monthly_searches'] for kw in keywords]
        competitions = [kw['competition_score'] for kw in keywords]
        cpcs = [kw['top_of_page_bid_high'] for kw in keywords]
        
        # Normalize metrics (0-1 scale)
        volume_min, volume_max = min(volumes), max(volumes)
        cpc_min, cpc_max = min(cpcs), max(cpcs)
        
        for kw in keywords:
            # Normalize search volume (higher is better)
            volume_norm = (kw['avg_monthly_searches'] - volume_min) / (volume_max - volume_min) if volume_max > volume_min else 0.5
            
            # Normalize CPC (lower is better for scoring)
            cpc_norm = 1 - ((kw['top_of_page_bid_high'] - cpc_min) / (cpc_max - cpc_min)) if cpc_max > cpc_min else 0.5
            
            # Competition score (lower is better)
            comp_norm = 1 - kw['competition_score']
            
            # Calculate weighted score
            score = (
                self.scoring_weights['search_volume_weight'] * volume_norm +
                self.scoring_weights['cpc_weight'] * cpc_norm +
                self.scoring_weights['competition_weight'] * comp_norm
            )
            
            kw['score'] = round(score, 3)
        
        # Sort by score (highest first)
        keywords.sort(key=lambda x: x['score'], reverse=True)
        
        return keywords
    
    def add_location_variants(self, keywords: List[Dict], locations: List[str]) -> List[Dict]:
        """Add location-based variants for relevant keywords"""
        location_keywords = []
        
        for kw in keywords:
            keyword = kw['keyword']
            
            # Skip if already location-specific
            if any(loc.split(',')[0].lower() in keyword.lower() for loc in locations):
                continue
            
            # Add location variants for relevant keywords
            if self._is_location_relevant(keyword):
                for location in locations:
                    city = location.split(',')[0]  # Extract city name
                    
                    # Create location variants
                    variants = [
                        f"{keyword} {city}",
                        f"{keyword} in {city}",
                        f"{city} {keyword}"
                    ]
                    
                    for variant in variants:
                        location_kw = kw.copy()
                        location_kw['keyword'] = variant
                        location_kw['avg_monthly_searches'] = int(kw['avg_monthly_searches'] * 0.1)  # Estimate lower volume
                        location_kw['is_location_variant'] = True
                        location_keywords.append(location_kw)
        
        return keywords + location_keywords
    
    def _is_location_relevant(self, keyword: str) -> bool:
        """Check if keyword is relevant for location variants"""
        location_relevant_terms = [
            'service', 'repair', 'store', 'shop', 'clinic', 'doctor', 'dentist',
            'restaurant', 'delivery', 'installation', 'contractor', 'lawyer',
            'real estate', 'plumber', 'electrician', 'near me', 'local'
        ]
        
        return any(term in keyword.lower() for term in location_relevant_terms)
    
    def generate_download_files(self, ad_groups: Dict, summary: Dict, scored_keywords: List[Dict]) -> Dict:
        """Generate all files as in-memory objects for download"""
        files = {}
        
        # 1. Master keywords CSV
        df_master = pd.DataFrame(scored_keywords)
        files['keywords_master.csv'] = df_master.to_csv(index=False)
        
        # 2. Ad groups JSON
        files['ad_groups_search.json'] = json.dumps(ad_groups, indent=2)
        
        # 3. Summary JSON
        files['ad_groups_summary.json'] = json.dumps(summary, indent=2)
        
        # 4. Individual ad group CSVs
        for group_name, keywords in ad_groups.items():
            if keywords:
                df_group = pd.DataFrame(keywords)
                # Select relevant columns for CSV
                columns = ['keyword', 'avg_monthly_searches', 'competition', 'score', 
                          'suggested_cpc_start', 'suggested_cpc_ceiling', 'match_types']
                
                # Handle missing columns gracefully
                available_columns = [col for col in columns if col in df_group.columns]
                df_group = df_group[available_columns]
                
                # Format match_types if it exists
                if 'match_types' in df_group.columns:
                    df_group['match_types'] = df_group['match_types'].apply(
                        lambda x: ', '.join(x) if isinstance(x, list) else str(x)
                    )
                
                filename = f'ad_group_{group_name}.csv'
                files[filename] = df_group.to_csv(index=False)
        
        # 5. Generate markdown report
        files['run_report.md'] = self._generate_markdown_report(summary, scored_keywords)
        
        return files
    
    def _generate_markdown_report(self, summary: Dict, keywords: List[Dict]) -> str:
        """Generate markdown report as string"""
        report = f"""# AdSmart AI - Keyword Research Report

## Summary
- **Total Keywords**: {summary['total_keywords']}
- **Total Ad Groups**: {summary['total_ad_groups']}
- **Configuration**: {self.config['keyword_settings']['mode']} mode
- **Min Search Volume**: {self.config['keyword_settings']['min_search_volume']}

## Ad Group Breakdown

"""
        
        for group_name, details in summary['ad_group_details'].items():
            report += f"""### {group_name.replace('_', ' ').title()}
- **Keywords**: {details['keyword_count']}
- **Avg Search Volume**: {details['avg_search_volume']:,}
- **Avg Score**: {details['avg_score']}
- **Avg Starting CPC**: ₹{details['avg_cpc_start']}
- **Top Keywords**: {', '.join(details['top_keywords'])}

"""
        
        report += f"""## Top 20 Keywords Overall

| Keyword | Search Volume | Competition | Score | CPC Low | CPC High |
|---------|---------------|-------------|-------|---------|----------|
"""
        
        for kw in sorted(keywords, key=lambda x: x['score'], reverse=True)[:20]:
            # Use the original CPC fields that are always available
            cpc_low = kw.get('top_of_page_bid_low', 0)
            cpc_high = kw.get('top_of_page_bid_high', 0)
            
            report += f"| {kw['keyword']} | {kw['avg_monthly_searches']:,} | {kw['competition']} | {kw['score']} | ₹{cpc_low} | ₹{cpc_high} |\n"
        
        return report
