import os
from serpapi import GoogleSearch
from typing import List, Dict
import time
import asyncio
import concurrent.futures
from dotenv import load_dotenv

load_dotenv()

class SERPKeywordResearcher:
    def __init__(self):
        self.api_key = os.getenv('SERP_API_KEY')
        if not self.api_key:
            raise ValueError("SERP_API_KEY not found in environment variables")
    
    def get_keyword_ideas(self, seed_keywords: List[str], location: str = "India") -> List[Dict]:
        """Get keyword ideas and metrics using SERP API"""
        if not seed_keywords:
            print("Warning: No seed keywords provided")
            return []
        
        # Fix location parameter - convert codes to canonical names
        canonical_location = self._get_canonical_location(location)
        print(f"🔍 Researching {len(seed_keywords)} seed keywords for location: {canonical_location}")
        
        all_keywords = []
        
        for i, seed in enumerate(seed_keywords):
            try:
                print(f"  Processing seed {i+1}/{len(seed_keywords)}: {seed}")
                
                # Search for related keywords using Google suggestions
                params = {
                    "engine": "google_autocomplete",
                    "q": seed,
                    "api_key": self.api_key
                }
                
                results = self._make_serp_request(params)
                
                if results and 'suggestions' in results:
                    batch_keywords = []
                    for suggestion in results['suggestions']:
                        keyword = suggestion.get('value', '')
                        if keyword and len(keyword) > 2:
                            batch_keywords.append(keyword)
                            all_keywords.append(keyword)
                    
                    print(f"    Found {len(batch_keywords)} suggestions")
                
                time.sleep(0.3)  # Reduced rate limiting
                
            except Exception as e:
                print(f"    Error getting suggestions for {seed}: {e}")
                continue
        
        # Remove duplicates
        unique_keywords = list(set(all_keywords))
        print(f"📊 Total unique keywords found: {len(unique_keywords)}")
        
        # Limit keywords for faster processing (optional)
        if len(unique_keywords) > 100:
            unique_keywords = unique_keywords[:100]
            print(f"📌 Limited to top 100 keywords for faster processing")
        
        # Get search volume and metrics for collected keywords
        return self._get_keyword_metrics_parallel(unique_keywords, canonical_location)
    
    def _get_canonical_location(self, location: str) -> str:
        """Convert location codes to SERP API canonical names"""
        location_mapping = {
            "US": "United States",
            "IN": "India",
            "CA": "Canada",
            "UK": "United Kingdom", 
            "AU": "Australia"
        }
        
        # Return canonical name or use input if already canonical
        return location_mapping.get(location, location)
    
    def _get_keyword_metrics_parallel(self, keywords: List[str], location: str) -> List[Dict]:
        """Get search volume and competition metrics using parallel processing"""
        if not keywords:
            return []
        
        canonical_location = self._get_canonical_location(location)
        print(f"📈 Getting metrics for {len(keywords)} keywords using parallel processing...")
        
        # Use ThreadPoolExecutor for parallel API calls
        keyword_data = []
        max_workers = 5  # Adjust based on SERP API rate limits
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_keyword = {
                executor.submit(self._get_single_keyword_metrics, keyword, canonical_location): keyword 
                for keyword in keywords
            }
            
            # Process completed tasks
            for i, future in enumerate(concurrent.futures.as_completed(future_to_keyword)):
                keyword = future_to_keyword[future]
                try:
                    result = future.result()
                    if result:
                        keyword_data.append(result)
                    
                    # Progress update every 10 keywords
                    if (i + 1) % 10 == 0 or (i + 1) == len(keywords):
                        print(f"  ✅ Processed {i + 1}/{len(keywords)} keywords ({len(keyword_data)} successful)")
                        
                except Exception as e:
                    print(f"    Error processing {keyword}: {e}")
        
        print(f"📊 Successfully processed {len(keyword_data)} out of {len(keywords)} keywords")
        return keyword_data
    
    def _get_single_keyword_metrics(self, keyword: str, location: str) -> Dict:
        """Get metrics for a single keyword"""
        try:
            params = {
                "engine": "google",
                "q": keyword,
                "location": location,
                "api_key": self.api_key
            }
            
            results = self._make_serp_request(params, max_retries=2)  # Reduced retries
            
            if results:
                # Extract metrics
                search_info = results.get('search_information', {})
                total_results = search_info.get('total_results', 0)
                
                # Estimate search volume
                estimated_volume = self._estimate_search_volume(keyword, total_results)
                
                # Estimate competition level
                competition = self._estimate_competition(total_results)
                
                # Estimate CPC
                cpc_low, cpc_high = self._estimate_cpc(keyword, competition)
                
                return {
                    'keyword': keyword,
                    'avg_monthly_searches': estimated_volume,
                    'competition': competition,
                    'competition_score': self._competition_to_score(competition),
                    'top_of_page_bid_low': cpc_low,
                    'top_of_page_bid_high': cpc_high,
                    'total_results': total_results
                }
            
            return None
            
        except Exception as e:
            print(f"    Error getting metrics for {keyword}: {e}")
            return None
    
    def _get_keyword_metrics(self, keywords: List[str], location: str) -> List[Dict]:
        """Fallback method - faster sequential processing"""
        if not keywords:
            return []
        
        keyword_data = []
        canonical_location = self._get_canonical_location(location)
        print(f"📈 Getting metrics for {len(keywords)} keywords (fast mode)...")
        
        # Reduced batch size and faster processing
        for i, keyword in enumerate(keywords):
            try:
                params = {
                    "engine": "google",
                    "q": keyword,
                    "location": canonical_location,
                    "api_key": self.api_key
                }
                
                results = self._make_serp_request(params, max_retries=1)  # Single retry only
                
                if results:
                    search_info = results.get('search_information', {})
                    total_results = search_info.get('total_results', 0)
                    
                    estimated_volume = self._estimate_search_volume(keyword, total_results)
                    competition = self._estimate_competition(total_results)
                    cpc_low, cpc_high = self._estimate_cpc(keyword, competition)
                    
                    keyword_data.append({
                        'keyword': keyword,
                        'avg_monthly_searches': estimated_volume,
                        'competition': competition,
                        'competition_score': self._competition_to_score(competition),
                        'top_of_page_bid_low': cpc_low,
                        'top_of_page_bid_high': cpc_high,
                        'total_results': total_results
                    })
                
                # Minimal delay for rate limiting
                time.sleep(0.1)
                
                # Progress update every 20 keywords
                if (i + 1) % 20 == 0 or (i + 1) == len(keywords):
                    print(f"  ✅ Processed {i + 1}/{len(keywords)} keywords ({len(keyword_data)} successful)")
                    
            except Exception as e:
                print(f"    Error getting metrics for {keyword}: {e}")
                continue
        
        print(f"📊 Successfully processed {len(keyword_data)} out of {len(keywords)} keywords")
        return keyword_data
    
    def _make_serp_request(self, params, max_retries=2):
        """Make SERP API request with reduced retry logic"""
        for attempt in range(max_retries):
            try:
                search = GoogleSearch(params)
                results = search.get_dict()
                
                if 'error' in results:
                    raise Exception(f"SERP API Error: {results['error']}")
                
                return results
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 1  # Fixed 1 second wait
                    time.sleep(wait_time)
                else:
                    return {}
        
        return {}
    
    def _estimate_search_volume(self, keyword: str, total_results: int) -> int:
        """Estimate search volume based on various factors"""
        if total_results == 0:
            return 500
        
        base_volume = min(total_results // 1000, 100000)
        word_count = len(keyword.split())
        
        if word_count == 1:
            base_volume = int(base_volume * 2.5)
        elif word_count == 2:
            base_volume = int(base_volume * 1.5)
        elif word_count > 4:
            base_volume = int(base_volume * 0.3)
        
        commercial_words = ['buy', 'purchase', 'order', 'price', 'cost', 'best', 'review']
        if any(word in keyword.lower() for word in commercial_words):
            base_volume = int(base_volume * 1.3)
        
        if any(word in keyword.lower() for word in ['near me', 'online', 'delivery']):
            base_volume = int(base_volume * 1.2)
        
        return max(base_volume, 500)
    
    def _estimate_competition(self, total_results: int) -> str:
        """Estimate competition level based on total results"""
        if total_results > 100_000_000:
            return "HIGH"
        elif total_results > 10_000_000:
            return "MEDIUM"
        elif total_results > 1_000_000:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _competition_to_score(self, competition: str) -> float:
        """Convert competition level to numeric score (0-1)"""
        scores = {"LOW": 0.2, "MEDIUM": 0.5, "HIGH": 0.8}
        return scores.get(competition, 0.5)
    
    def _estimate_cpc(self, keyword: str, competition: str) -> tuple:
        """Estimate CPC range based on keyword and competition"""
        base_cpc = {
            "LOW": (5, 25),
            "MEDIUM": (15, 75),
            "HIGH": (30, 200)
        }
        
        low, high = base_cpc.get(competition, (15, 75))
        keyword_lower = keyword.lower()
        
        if any(word in keyword_lower for word in ['buy', 'purchase', 'order', 'price', 'cost', 'hire', 'service']):
            low = int(low * 2.0)
            high = int(high * 2.5)
        elif any(word in keyword_lower for word in ['how', 'what', 'why', 'guide', 'tips', 'tutorial', 'free']):
            low = int(low * 0.4)
            high = int(high * 0.6)
        elif any(word in keyword_lower for word in ['vs', 'alternative', 'competitor', 'compare']):
            low = int(low * 1.5)
            high = int(high * 1.8)
        elif any(word in keyword_lower for word in ['near me', 'in', 'mumbai', 'delhi', 'bangalore', 'local']):
            low = int(low * 1.2)
            high = int(high * 1.3)
        
        low = max(low, 5)
        high = max(high, low + 10)
        return round(low, 2), round(high, 2)
    
    def get_competitor_keywords(self, competitor_url: str) -> List[str]:
        """Extract potential keywords from competitor website using SERP API"""
        try:
            print(f"🔍 Analyzing competitor: {competitor_url}")
            
            from urllib.parse import urlparse
            domain = urlparse(competitor_url).netloc
            if domain.startswith('www.'):
                domain = domain[4:]
            
            params = {
                "engine": "google",
                "q": f"site:{domain}",
                "api_key": self.api_key,
                "num": 20,
                "location": "India"
            }
            
            results = self._make_serp_request(params)
            
            if not results:
                return []
            
            keywords = set()
            organic_results = results.get('organic_results', [])
            
            print(f"  Found {len(organic_results)} pages from competitor")
            
            for result in organic_results:
                title = result.get('title', '')
                snippet = result.get('snippet', '')
                text_content = f"{title} {snippet}".lower()
                words = text_content.split()
                
                for word in words:
                    cleaned_word = ''.join(c for c in word if c.isalpha())
                    if len(cleaned_word) > 3:
                        keywords.add(cleaned_word)
                
                for i in range(len(words) - 1):
                    word1 = ''.join(c for c in words[i] if c.isalpha())
                    word2 = ''.join(c for c in words[i+1] if c.isalpha())
                    if len(word1) > 2 and len(word2) > 2:
                        phrase = f"{word1} {word2}"
                        keywords.add(phrase)
            
            stop_words = {'and', 'the', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'she', 'use', 'her', 'way', 'many', 'then', 'them', 'well', 'were'}
            
            filtered_keywords = [kw for kw in keywords if kw not in stop_words and len(kw.split()) <= 3]
            
            print(f"  Extracted {len(filtered_keywords)} potential keywords")
            return list(filtered_keywords)[:30]  # Reduced from 50 to 30
            
        except Exception as e:
            print(f"Error analyzing competitor {competitor_url}: {e}")
            return []
