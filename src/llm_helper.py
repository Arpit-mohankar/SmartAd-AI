from openai import OpenAI
from typing import List, Dict
import json
import os
from dotenv import load_dotenv

load_dotenv()

class LLMHelper:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def generate_seed_keywords(self, brand_content: Dict, competitor_content: Dict) -> List[str]:
        """Generate seed keywords using LLM based on website content"""
        
        prompt = f"""
        Based on the following website content, generate 15-20 relevant seed keywords for Google Ads campaigns.
        
        BRAND WEBSITE:
        Title: {brand_content.get('title', '')}
        Meta Description: {brand_content.get('meta_description', '')}
        Main Headings: {brand_content.get('headings', {}).get('h1', [])}
        Navigation: {brand_content.get('navigation', [])}
        Content Sample: {brand_content.get('content', '')[:1000]}
        
        COMPETITOR WEBSITE:
        Title: {competitor_content.get('title', '')}
        Navigation: {competitor_content.get('navigation', [])}
        
        Generate seed keywords that are:
        1. Relevant to the brand's products/services
        2. Include both broad and specific terms
        3. Include location-based variations if applicable
        4. Include competitor comparison terms
        5. Include long-tail informational queries
        
        Return ONLY a JSON array of keywords, no other text:
        ["keyword1", "keyword2", ...]
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            # Extract JSON from response
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            json_str = content[start_idx:end_idx]
            
            keywords = json.loads(json_str)
            return keywords
            
        except Exception as e:
            print(f"Error generating seed keywords: {e}")
            return []
    
    def categorize_keywords(self, keywords: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize keywords into ad groups using LLM"""
        
        keyword_list = [kw['keyword'] for kw in keywords]
        
        prompt = f"""
        Categorize the following keywords into these ad group types:
        - brand_terms: Keywords containing the brand name
        - category_terms: Product/service category keywords
        - competitor_terms: Keywords mentioning competitors
        - location_terms: Keywords with location intent
        - informational_terms: How-to, what is, best, reviews, etc.
        
        Keywords to categorize:
        {keyword_list}
        
        Return a JSON object with categories as keys and arrays of keywords as values:
        {{
            "brand_terms": ["keyword1", "keyword2"],
            "category_terms": ["keyword3", "keyword4"],
            ...
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            
            categorized = json.loads(json_str)
            
            # Map back to full keyword objects
            result = {}
            for category, keyword_names in categorized.items():
                result[category] = []
                for kw_name in keyword_names:
                    for kw_obj in keywords:
                        if kw_obj['keyword'].lower() == kw_name.lower():
                            result[category].append(kw_obj)
                            break
            
            return result
            
        except Exception as e:
            print(f"Error categorizing keywords: {e}")
            return self._fallback_categorization(keywords)
    
    def _fallback_categorization(self, keywords: List[Dict]) -> Dict[str, List[Dict]]:
        """Simple rule-based categorization as fallback"""
        categories = {
            'brand_terms': [],
            'category_terms': [],
            'competitor_terms': [],
            'location_terms': [],
            'informational_terms': []
        }
        
        location_words = ['near me', 'in', 'city', 'local', 'area']
        info_words = ['how', 'what', 'best', 'top', 'review', 'guide', 'tips']
        
        for kw in keywords:
            keyword_lower = kw['keyword'].lower()
            
            if any(word in keyword_lower for word in info_words):
                categories['informational_terms'].append(kw)
            elif any(word in keyword_lower for word in location_words):
                categories['location_terms'].append(kw)
            else:
                categories['category_terms'].append(kw)
        
        return categories
