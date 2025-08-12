"""
Royal Sanction Watch - Sanction Checker
Checks vessels, persons, and companies against sanctions lists using OpenSanctions API
"""

import requests
import pandas as pd
import time
import re
import logging
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import os
from urllib.parse import urljoin
import xml.etree.ElementTree as ET
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SanctionMatch:
    """Data class for storing sanction match information"""
    entity_name: str
    entity_type: str  # 'vessel', 'person', 'company'
    sanction_list: str  # 'OFAC', 'UK', 'EU', 'UN', 'OpenSanctions'
    match_type: str  # 'exact', 'partial', 'fuzzy'
    confidence: float
    details: Dict
    source_url: str
    last_updated: datetime

class OpenSanctionsAPI:
    """OpenSanctions API client"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.opensanctions.org"):
        self.base_url = base_url
        self.api_key = api_key
        self.session = self._setup_session()
    
    def _setup_session(self) -> requests.Session:
        """Setup requests session with retry strategy"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        # Add API key to headers if provided
        if self.api_key:
            session.headers.update({"Authorization": f"ApiKey {self.api_key}"})
        
        return session
    
    def search_entities(self, query: str, dataset: str = "default", limit: int = 10, 
                       schema: str = "Thing", topics: Optional[List[str]] = None) -> Dict:
        """
        Search for entities using OpenSanctions search API
        
        Args:
            query: Search query
            dataset: Dataset to search in (default, sanctions, peps, etc.)
            limit: Maximum number of results
            schema: Entity schema type (Person, Company, Vessel, etc.)
            topics: Filter by topics (e.g., ['sanction', 'role.pep'])
        
        Returns:
            Search response dictionary
        """
        url = f"{self.base_url}/search/{dataset}"
        
        params = {
            "q": query,
            "limit": min(limit, 500),  # API limit is 500
            "schema": schema
        }
        
        if topics:
            params["topics"] = topics
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error(f"OpenSanctions API authentication failed. Please check your API key in .env file")
                logger.info("Get your API key from: https://www.opensanctions.org/api/")
            else:
                logger.error(f"OpenSanctions search error: {e}")
            return {"results": [], "total": {"value": 0}}
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenSanctions search error: {e}")
            return {"results": [], "total": {"value": 0}}
    
    def match_entities(self, entities: List[Dict], dataset: str = "default", 
                      threshold: float = 0.7, limit: int = 5) -> Dict:
        """
        Match entities using OpenSanctions matching API
        
        Args:
            entities: List of entity dictionaries with schema and properties
            dataset: Dataset to match against
            threshold: Score threshold for matches
            limit: Maximum results per entity
        
        Returns:
            Match response dictionary
        """
        url = f"{self.base_url}/match/{dataset}"
        
        # Prepare queries
        queries = {}
        for i, entity in enumerate(entities):
            queries[f"entity_{i}"] = entity
        
        payload = {
            "queries": queries,
            "threshold": threshold,
            "limit": limit
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenSanctions match error: {e}")
            return {"responses": {}}
    
    def get_entity_details(self, entity_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific entity
        
        Args:
            entity_id: OpenSanctions entity ID
        
        Returns:
            Entity details dictionary
        """
        url = f"{self.base_url}/entities/{entity_id}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenSanctions entity fetch error: {e}")
            return None
    
    def get_catalog(self) -> Dict:
        """Get available datasets catalog"""
        url = f"{self.base_url}/catalog"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenSanctions catalog error: {e}")
            return {"datasets": []}

class SanctionChecker:
    """Main class for checking entities against various sanctions lists"""
    
    def __init__(self, cache_dir: str = None, cache_duration_hours: int = None, 
                 opensanctions_api_key: Optional[str] = None):
        # Import config here to avoid circular imports
        from config import Config
        
        self.cache_dir = cache_dir or Config.CACHE_DIR
        self.cache_duration = timedelta(hours=cache_duration_hours or Config.CACHE_DURATION_HOURS)
        self.session = self._setup_session()
        self.ua = UserAgent()
        
        # Initialize OpenSanctions API
        api_key = opensanctions_api_key or Config.OPENSANCTIONS_API_KEY
        self.opensanctions = OpenSanctionsAPI(api_key=api_key, base_url=Config.OPENSANCTIONS_BASE_URL)
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Sanction list configurations
        self.sanction_sources = {
            'OpenSanctions': {
                'description': 'OpenSanctions - Comprehensive sanctions and PEP database',
                'datasets': ['sanctions', 'peps', 'default']
            },
            'OFAC': {
                'sdn_url': 'https://www.treasury.gov/ofac/downloads/sdn.csv',
                'vessel_url': 'https://www.treasury.gov/ofac/downloads/sdn.csv',  # Use SDN list for vessels too
                'description': 'US Office of Foreign Assets Control'
            },
            'UK': {
                'url': 'https://www.gov.uk/government/publications/the-uk-sanctions-list',
                'description': 'UK Sanctions List'
            },
            'EU': {
                'url': 'https://www.dma.dk/Media/638834044135010725/2025118019-7%20Importversion%20-%20List%20of%20EU%20designated%20vessels%20(20-05-2025)%203010691_2_0.XLSX',
                'description': 'EU Sanctions List'
            },
            'UN': {
                'url': 'https://www.un.org/securitycouncil/content/un-sc-consolidated-list',
                'description': 'UN Security Council Consolidated List'
            }
        }
    
    def _setup_session(self) -> requests.Session:
        """Setup requests session with retry strategy"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for requests"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""
        return re.sub(r'[^\w\s]', '', text.lower().strip())
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using simple ratio"""
        if not text1 or not text2:
            return 0.0
        
        norm1 = self._normalize_text(text1)
        norm2 = self._normalize_text(text2)
        
        if norm1 == norm2:
            return 1.0
        
        # Simple similarity calculation
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _detect_entity_type(self, entity_name: str) -> str:
        """Auto-detect entity type based on name patterns"""
        name_lower = entity_name.lower()
        
        # Vessel indicators
        vessel_indicators = ['vessel', 'ship', 'boat', 'tanker', 'cargo', 'imo', 'mmsi']
        if any(indicator in name_lower for indicator in vessel_indicators):
            return 'vessel'
        
        # Company indicators
        company_indicators = ['ltd', 'inc', 'corp', 'company', 'co.', 'llc', 'plc']
        if any(indicator in name_lower for indicator in company_indicators):
            return 'company'
        
        # Person indicators (names with spaces, typical person name patterns)
        if len(entity_name.split()) >= 2 and not any(char.isdigit() for char in entity_name):
            return 'person'
        
        # Default to vessel for maritime context
        return 'vessel'
    
    def _map_entity_type_to_schema(self, entity_type: str) -> str:
        """Map entity type to OpenSanctions schema"""
        schema_map = {
            'vessel': 'Vessel',
            'person': 'Person',
            'company': 'Company',
            'organization': 'Organization'
        }
        return schema_map.get(entity_type, 'Thing')
    
    def _create_opensanctions_entity(self, entity_name: str, entity_type: str) -> Dict:
        """Create OpenSanctions entity format"""
        schema = self._map_entity_type_to_schema(entity_type)
        
        entity = {
            "schema": schema,
            "properties": {
                "name": [entity_name]
            }
        }
        
        # Add additional properties based on entity type
        if entity_type == 'person':
            # Could add birthDate, nationality, etc. if available
            pass
        elif entity_type in ['company', 'organization']:
            # Could add jurisdiction, registrationNumber, etc. if available
            pass
        elif entity_type == 'vessel':
            # Could add imo, mmsi, etc. if available
            pass
        
        return entity
    
    def _process_opensanctions_results(self, results: List[Dict], entity_name: str, 
                                     entity_type: str) -> List[SanctionMatch]:
        """Process OpenSanctions search results into SanctionMatch objects"""
        matches = []
        
        for result in results:
            # Extract basic information
            entity_id = result.get('id', '')
            caption = result.get('caption', '')
            schema = result.get('schema', '')
            datasets = result.get('datasets', [])
            properties = result.get('properties', {})
            
            # Calculate confidence based on name similarity
            confidence = self._calculate_similarity(entity_name, caption)
            
            # Determine match type
            if confidence >= 0.9:
                match_type = 'exact'
            elif confidence >= 0.7:
                match_type = 'partial'
            else:
                match_type = 'fuzzy'
            
            # Create SanctionMatch object
            match = SanctionMatch(
                entity_name=entity_name,
                entity_type=entity_type,
                sanction_list='OpenSanctions',
                match_type=match_type,
                confidence=confidence,
                details={
                    'entity_id': entity_id,
                    'caption': caption,
                    'schema': schema,
                    'datasets': datasets,
                    'properties': properties,
                    'target': result.get('target', False),
                    'first_seen': result.get('first_seen'),
                    'last_seen': result.get('last_seen')
                },
                source_url=f"https://www.opensanctions.org/entities/{entity_id}",
                last_updated=datetime.now()
            )
            
            matches.append(match)
        
        return matches
    
    def check_single_entity(self, entity_name: str, entity_type: str = 'auto') -> List[SanctionMatch]:
        """
        Check a single entity against sanctions lists
        
        Args:
            entity_name: Name of the entity to check
            entity_type: Type of entity ('vessel', 'person', 'company', 'auto')
        
        Returns:
            List of SanctionMatch objects
        """
        logger.info(f"Checking entity: {entity_name} (type: {entity_type})")
        
        # Auto-detect entity type if not specified
        if entity_type == 'auto':
            entity_type = self._detect_entity_type(entity_name)
        
        all_matches = []
        
        # Check against OpenSanctions API
        try:
            logger.info("Checking against OpenSanctions API...")
            
            # Search in sanctions dataset
            sanctions_results = self.opensanctions.search_entities(
                query=entity_name,
                dataset="sanctions",
                schema=self._map_entity_type_to_schema(entity_type),
                topics=['sanction'],
                limit=10
            )
            
            if sanctions_results.get('results'):
                matches = self._process_opensanctions_results(
                    sanctions_results['results'], entity_name, entity_type
                )
                all_matches.extend(matches)
            
            # Search in default dataset for broader results
            default_results = self.opensanctions.search_entities(
                query=entity_name,
                dataset="default",
                schema=self._map_entity_type_to_schema(entity_type),
                limit=10
            )
            
            if default_results.get('results'):
                matches = self._process_opensanctions_results(
                    default_results['results'], entity_name, entity_type
                )
                all_matches.extend(matches)
            
            # Remove duplicates based on entity_id
            seen_ids = set()
            unique_matches = []
            for match in all_matches:
                entity_id = match.details.get('entity_id', '')
                if entity_id not in seen_ids:
                    seen_ids.add(entity_id)
                    unique_matches.append(match)
            
            all_matches = unique_matches
            
        except Exception as e:
            logger.error(f"Error checking OpenSanctions for {entity_name}: {e}")
        
        # Check against other sources (legacy support)
        for source in ['OFAC', 'UK', 'EU', 'UN']:
            try:
                if source == 'OFAC':
                    sanction_data = self._fetch_ofac_data()
                elif source == 'UK':
                    sanction_data = self._fetch_uk_data()
                elif source == 'EU':
                    sanction_data = self._fetch_eu_data()
                elif source == 'UN':
                    sanction_data = self._fetch_un_data()
                else:
                    continue
                
                if not sanction_data.empty:
                    matches = self._search_entity(entity_name, entity_type, sanction_data, source)
                    all_matches.extend(matches)
                
                # Add delay to be respectful to servers
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error checking {source} for {entity_name}: {e}")
        
        return all_matches
    
    def check_bulk_entities(self, entities: List[Dict]) -> Dict[str, List[SanctionMatch]]:
        """
        Check multiple entities against sanctions lists using OpenSanctions matching API
        
        Args:
            entities: List of dictionaries with 'name' and optional 'type' keys
        
        Returns:
            Dictionary mapping entity names to lists of SanctionMatch objects
        """
        logger.info(f"Checking {len(entities)} entities in bulk")
        
        results = {}
        
        # Prepare entities for OpenSanctions matching API
        opensanctions_entities = []
        entity_mapping = {}
        
        for i, entity in enumerate(entities):
            entity_name = entity.get('name', '')
            entity_type = entity.get('type', 'auto')
            
            if not entity_name:
                continue
            
            # Auto-detect entity type if needed
            if entity_type == 'auto':
                entity_type = self._detect_entity_type(entity_name)
            
            # Create OpenSanctions entity format
            opensanctions_entity = self._create_opensanctions_entity(entity_name, entity_type)
            opensanctions_entities.append(opensanctions_entity)
            entity_mapping[f"entity_{i}"] = {
                'name': entity_name,
                'type': entity_type
            }
        
        # Use OpenSanctions matching API for bulk check
        try:
            logger.info("Performing bulk check with OpenSanctions matching API...")
            
            match_response = self.opensanctions.match_entities(
                entities=opensanctions_entities,
                dataset="sanctions",
                threshold=0.7,
                limit=5
            )
            
            # Process results
            responses = match_response.get('responses', {})
            
            for query_id, response in responses.items():
                if query_id in entity_mapping:
                    entity_info = entity_mapping[query_id]
                    entity_name = entity_info['name']
                    entity_type = entity_info['type']
                    
                    matches = []
                    for result in response.get('results', []):
                        # Create SanctionMatch object
                        match = SanctionMatch(
                            entity_name=entity_name,
                            entity_type=entity_type,
                            sanction_list='OpenSanctions',
                            match_type='fuzzy' if result.get('score', 0) < 0.9 else 'exact',
                            confidence=result.get('score', 0),
                            details=result,
                            source_url=f"https://www.opensanctions.org/entities/{result.get('id', '')}",
                            last_updated=datetime.now()
                        )
                        matches.append(match)
                    
                    results[entity_name] = matches
            
        except Exception as e:
            logger.error(f"Error in bulk OpenSanctions check: {e}")
            
            # Fallback to individual checks
            logger.info("Falling back to individual entity checks...")
            for entity in entities:
                entity_name = entity.get('name', '')
                entity_type = entity.get('type', 'auto')
                
                if entity_name:
                    matches = self.check_single_entity(entity_name, entity_type)
                    results[entity_name] = matches
        
        return results
    
    def _search_entity(self, entity_name: str, entity_type: str, 
                      sanction_data: pd.DataFrame, source: str) -> List[SanctionMatch]:
        """Search for an entity in sanction data (legacy method)"""
        matches = []
        normalized_name = self._normalize_text(entity_name)
        
        # Determine which columns to search based on entity type
        search_columns = []
        if entity_type == 'vessel':
            search_columns = ['vessel_name', 'name', 'title', 'vessel']
        elif entity_type == 'person':
            search_columns = ['name', 'title', 'individual', 'person']
        elif entity_type == 'company':
            search_columns = ['name', 'title', 'entity', 'company', 'organization']
        else:
            search_columns = ['name', 'title']  # Default search columns
        
        # Find actual columns in the dataframe
        available_columns = [col for col in search_columns if col in sanction_data.columns]
        if not available_columns:
            available_columns = sanction_data.columns.tolist()
        
        for _, row in sanction_data.iterrows():
            for col in available_columns:
                if pd.isna(row[col]):
                    continue
                
                cell_value = str(row[col])
                normalized_cell = self._normalize_text(cell_value)
                
                # Check for exact match
                if normalized_name == normalized_cell:
                    matches.append(SanctionMatch(
                        entity_name=entity_name,
                        entity_type=entity_type,
                        sanction_list=source,
                        match_type='exact',
                        confidence=1.0,
                        details=row.to_dict(),
                        source_url=self.sanction_sources[source].get('url', ''),
                        last_updated=datetime.now()
                    ))
                    break
                
                # Check for partial match
                elif normalized_name in normalized_cell or normalized_cell in normalized_name:
                    similarity = self._calculate_similarity(entity_name, cell_value)
                    if similarity > 0.7:  # Threshold for partial match
                        matches.append(SanctionMatch(
                            entity_name=entity_name,
                            entity_type=entity_type,
                            sanction_list=source,
                            match_type='partial',
                            confidence=similarity,
                            details=row.to_dict(),
                            source_url=self.sanction_sources[source].get('url', ''),
                            last_updated=datetime.now()
                        ))
                        break
        
        return matches
    
    # Legacy methods for other sanction sources (kept for compatibility)
    def _fetch_ofac_data(self) -> pd.DataFrame:
        """Fetch OFAC SDN and vessel data (legacy method)"""
        logger.info("Fetching OFAC data...")
        try:
            # Fetch SDN list only (vessel data is included in SDN list)
            sdn_response = self.session.get(
                self.sanction_sources['OFAC']['sdn_url'],
                headers=self._get_headers(),
                timeout=30
            )
            sdn_response.raise_for_status()
            
            # Parse CSV data
            sdn_df = pd.read_csv(StringIO(sdn_response.text))
            
            # Filter for vessels if 'type' column exists
            if 'type' in sdn_df.columns:
                vessel_df = sdn_df[sdn_df['type'].str.contains('vessel', case=False, na=False)]
            else:
                vessel_df = sdn_df
            
            logger.info(f"Successfully fetched OFAC data: {len(vessel_df)} vessel records")
            return vessel_df
            
        except Exception as e:
            logger.error(f"Failed to fetch OFAC data: {e}")
            return pd.DataFrame()
    
    def _fetch_uk_data(self) -> pd.DataFrame:
        """Fetch UK sanctions data (legacy method)"""
        logger.info("Fetching UK sanctions data...")
        try:
            response = self.session.get(
                self.sanction_sources['UK']['url'],
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            
            # Placeholder - actual implementation would depend on UK data format
            df = pd.DataFrame({
                'name': [],
                'type': [],
                'country': [],
                'reason': [],
                'date_added': []
            })
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch UK data: {e}")
            return pd.DataFrame()
    
    def _fetch_eu_data(self) -> pd.DataFrame:
        """Fetch EU sanctions data (legacy method)"""
        logger.info("Fetching EU sanctions data...")
        try:
            response = self.session.get(
                self.sanction_sources['EU']['url'],
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            
            # Parse Excel file
            df = pd.read_excel(BytesIO(response.content))
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch EU data: {e}")
            return pd.DataFrame()
    
    def _fetch_un_data(self) -> pd.DataFrame:
        """Fetch UN sanctions data (legacy method)"""
        logger.info("Fetching UN sanctions data...")
        try:
            response = self.session.get(
                self.sanction_sources['UN']['url'],
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            
            # Try to parse XML data with error handling
            try:
                root = ET.fromstring(response.content)
                
                # Extract data from XML (simplified example)
                data = []
                for entity in root.findall('.//INDIVIDUAL'):
                    name = entity.find('FIRST_NAME')
                    if name is not None and name.text:
                        data.append({
                            'name': name.text,
                            'type': 'person',
                            'source': 'UN'
                        })
                
                df = pd.DataFrame(data)
                logger.info(f"Successfully parsed UN data: {len(df)} records")
                return df
                
            except ET.ParseError as xml_error:
                logger.warning(f"XML parsing failed for UN data: {xml_error}")
                # Return empty DataFrame if XML parsing fails
                return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Failed to fetch UN data: {e}")
            return pd.DataFrame()
    
    def generate_report(self, results: Dict[str, List[SanctionMatch]], 
                       output_format: str = 'excel') -> str:
        """
        Generate a report from sanction check results
        
        Args:
            results: Results from check_bulk_entities
            output_format: 'excel', 'csv', or 'json'
        
        Returns:
            Path to the generated report file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Prepare data for report
        report_data = []
        for entity_name, matches in results.items():
            if matches:
                for match in matches:
                    report_data.append({
                        'Entity Name': entity_name,
                        'Entity Type': match.entity_type,
                        'Sanction List': match.sanction_list,
                        'Match Type': match.match_type,
                        'Confidence': match.confidence,
                        'Details': json.dumps(match.details),
                        'Source URL': match.source_url,
                        'Check Date': match.last_updated.strftime("%Y-%m-%d %H:%M:%S")
                    })
            else:
                report_data.append({
                    'Entity Name': entity_name,
                    'Entity Type': 'unknown',
                    'Sanction List': 'None',
                    'Match Type': 'None',
                    'Confidence': 0.0,
                    'Details': 'No matches found',
                    'Source URL': '',
                    'Check Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        
        df = pd.DataFrame(report_data)
        
        # Generate report file
        if output_format == 'excel':
            filename = f"royal_sanction_watch_report_{timestamp}.xlsx"
            df.to_excel(filename, index=False)
        elif output_format == 'csv':
            filename = f"royal_sanction_watch_report_{timestamp}.csv"
            df.to_csv(filename, index=False)
        elif output_format == 'json':
            filename = f"royal_sanction_watch_report_{timestamp}.json"
            df.to_json(filename, orient='records', indent=2)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        logger.info(f"Report generated: {filename}")
        return filename

# Import statements for dependencies
from io import StringIO, BytesIO 