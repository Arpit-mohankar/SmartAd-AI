from typing import Dict, List
from src.llm_helper import LLMHelper

class AdGroupBuilder:
    def __init__(self, config: Dict):
        self.config = config
        self.llm_helper = LLMHelper()
        self.conversion_rate = config['keyword_settings']['conversion_rate']
    
    def build_ad_groups(self, keywords: List[Dict]) -> Dict[str, List[Dict]]:
        """Build ad groups from categorized keywords"""
        
        # Use LLM to categorize keywords
        categorized = self.llm_helper.categorize_keywords(keywords)
        
        # Add match types and CPC recommendations to each keyword
        for category, kw_list in categorized.items():
            for kw in kw_list:
                kw['match_types'] = self._get_match_types(kw, category)
                kw['suggested_cpc_start'] = self._calculate_suggested_cpc(kw, 'start')
                kw['suggested_cpc_ceiling'] = self._calculate_suggested_cpc(kw, 'ceiling')
                kw['category'] = category
        
        return categorized
    
    def _get_match_types(self, keyword: Dict, category: str) -> List[str]:
        """Determine appropriate match types for keyword based on category"""
        
        match_type_rules = {
            'brand_terms': ['Exact', 'Phrase'],
            'category_terms': ['Phrase', 'Exact'],
            'competitor_terms': ['Exact'],
            'location_terms': ['Phrase', 'Exact'],
            'informational_terms': ['Phrase']
        }
        
        base_match_types = match_type_rules.get(category, ['Phrase'])
        
        # Add Broad match for high-volume, low-competition keywords
        if (keyword['avg_monthly_searches'] > 2000 and 
            keyword['competition'] == 'LOW' and 
            category in ['category_terms', 'informational_terms']):
            base_match_types.append('Broad')
        
        return base_match_types
    
    def _calculate_suggested_cpc(self, keyword: Dict, cpc_type: str) -> float:
        """Calculate suggested CPC based on bid benchmarks"""
        
        low_bid = keyword['top_of_page_bid_low']
        high_bid = keyword['top_of_page_bid_high']
        
        if cpc_type == 'start':
            # Start at 70-80% of low bid or mid-point
            suggested = min(low_bid * 0.75, (low_bid + high_bid) / 2)
        else:  # ceiling
            # Ceiling at high bid
            suggested = high_bid
        
        # Adjust based on conversion rate and competition
        if keyword['competition'] == 'LOW':
            suggested *= 0.9
        elif keyword['competition'] == 'HIGH':
            suggested *= 1.1
        
        return round(suggested, 2)
    
    def generate_ad_group_summary(self, ad_groups: Dict[str, List[Dict]]) -> Dict:
        """Generate summary statistics for ad groups"""
        
        summary = {
            'total_keywords': sum(len(keywords) for keywords in ad_groups.values()),
            'total_ad_groups': len(ad_groups),
            'ad_group_details': {}
        }
        
        for group_name, keywords in ad_groups.items():
            if keywords:
                summary['ad_group_details'][group_name] = {
                    'keyword_count': len(keywords),
                    'avg_search_volume': round(sum(kw['avg_monthly_searches'] for kw in keywords) / len(keywords)),
                    'avg_score': round(sum(kw['score'] for kw in keywords) / len(keywords), 3),
                    'avg_cpc_start': round(sum(kw['suggested_cpc_start'] for kw in keywords) / len(keywords), 2),
                    'top_keywords': [kw['keyword'] for kw in sorted(keywords, key=lambda x: x['score'], reverse=True)[:5]]
                }
        
        return summary
