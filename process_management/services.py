"""
Service functions for process management and migration.
"""
import os
import re
import difflib
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
from django.conf import settings
from django.db import transaction
from .models import ProcessDepartment, Process, ProcessDocument
from knowledge_center.models import (
    FolderApplication, KnowledgeCentreFolder, KnowldgeCentreFile, 
    KnowledgeCenter, Filetype, First_Category, Secondary_Category
)
from it.users.models import Regions, Sections, UserProfile


class FolderAnalysisService:
    """
    Service class for analyzing existing folder structure and identifying processes.
    """
    
    # Department mapping based on folder names and content patterns
    DEPARTMENT_MAPPING = {
        'general manager': 'GENERAL MANAGER\'S OFFICE',
        'gm': 'GENERAL MANAGER\'S OFFICE',
        'engineering manager': 'ENGINEERING MANAGER\'S OFFICE',
        'em': 'ENGINEERING MANAGER\'S OFFICE',
        'districts': 'DISTRICTS',
        'district': 'DISTRICTS',
        'network development': 'NETWORK DEVELOPMENT',
        'network': 'NETWORK DEVELOPMENT',
        'operations': 'OPERATIONS AND MAINTENANCE',
        'maintenance': 'OPERATIONS AND MAINTENANCE',
        'ops': 'OPERATIONS AND MAINTENANCE',
        'commercial': 'COMMERCIAL',
        'finance': 'FINANCE',
        'procurement': 'PROCUREMENT',
        'risk management': 'RISK MANAGEMENT',
        'risk': 'RISK MANAGEMENT',
        'safety': 'SAFETY',
        'human resources': 'HUMAN RESOURCES AND ADMINISTRATION',
        'hr': 'HUMAN RESOURCES AND ADMINISTRATION',
        'administration': 'HUMAN RESOURCES AND ADMINISTRATION',
        'admin': 'HUMAN RESOURCES AND ADMINISTRATION',
        'information technology': 'INFORMATION AND COMMUNICATION TECHNOLOGY',
        'it': 'INFORMATION AND COMMUNICATION TECHNOLOGY',
        'ict': 'INFORMATION AND COMMUNICATION TECHNOLOGY',
        'communication': 'INFORMATION AND COMMUNICATION TECHNOLOGY',
    }
    
    def __init__(self):
        self.analysis_report = {
            'folders_analyzed': 0,
            'processes_identified': 0,
            'documents_found': 0,
            'mapping_errors': [],
            'categorization_errors': [],
            'department_distribution': {},
        }
    
    def analyze_existing_processes(self) -> Dict:
        """
        Analyze existing process data from the knowledge center.
        
        Returns:
            Dict containing analysis results and identified processes
        """
        analysis_results = {
            'total_processes': 0,
            'processes_by_department': {},
            'processes_by_folder': {},
            'unmapped_processes': [],
            'department_mapping': {},
        }
        
        try:
            # Get the processes_and_procedures application (id=2)
            processes_app = FolderApplication.objects.filter(id=2).first()
            if not processes_app:
                self.analysis_report['mapping_errors'].append("Processes and Procedures application not found")
                return analysis_results
            
            # Analyze folder structure for processes_and_procedures
            process_folders = KnowledgeCentreFolder.objects.filter(
                folder_application=processes_app,
                parent__isnull=True
            )
            
            for folder in process_folders:
                dept_name = self._map_folder_to_department(folder.name)
                
                # Get all files in this folder and subfolders
                folder_files = self._get_all_files_in_folder(folder)
                
                if dept_name:
                    if dept_name not in analysis_results['processes_by_department']:
                        analysis_results['processes_by_department'][dept_name] = []
                    
                    for file_info in folder_files:
                        analysis_results['processes_by_department'][dept_name].append(file_info)
                else:
                    analysis_results['unmapped_processes'].extend(folder_files)
                
                # Store folder mapping
                analysis_results['processes_by_folder'][folder.name] = {
                    'id': folder.id,
                    'department': dept_name,
                    'files_count': len(folder_files),
                    'files': folder_files
                }
            
            # Also analyze legacy KnowledgeCenter data for processes
            legacy_processes = KnowledgeCenter.objects.filter(
                archived=False,
                file_type__icontains='process'
            )
            
            for process in legacy_processes:
                dept_name = self._map_folder_to_department(process.sub_category_1 or '')
                if dept_name:
                    if dept_name not in analysis_results['processes_by_department']:
                        analysis_results['processes_by_department'][dept_name] = []
                    
                    process_info = {
                        'id': process.id,
                        'filename': process.filename,
                        'filepath': process.filepath,
                        'section': process.section,
                        'region': process.region,
                        'filetype': process.file_type,
                        'sub_category_1': process.sub_category_1,
                        'sub_category_2': process.sub_category_2,
                        'source': 'legacy_knowledge_center'
                    }
                    analysis_results['processes_by_department'][dept_name].append(process_info)
                else:
                    analysis_results['unmapped_processes'].append({
                        'id': process.id,
                        'filename': process.filename,
                        'sub_category_1': process.sub_category_1,
                        'filepath': process.filepath,
                        'source': 'legacy_knowledge_center'
                    })
            
            analysis_results['total_processes'] = sum(
                len(files) for files in analysis_results['processes_by_department'].values()
            ) + len(analysis_results['unmapped_processes'])
            
            self.analysis_report['folders_analyzed'] = len(process_folders)
            self.analysis_report['processes_identified'] = analysis_results['total_processes']
            self.analysis_report['department_distribution'] = {
                k: len(v) for k, v in analysis_results['processes_by_department'].items()
            }
            
        except Exception as e:
            self.analysis_report['mapping_errors'].append(f"Error analyzing existing processes: {str(e)}")
        
        return analysis_results
    
    def analyze_folder_structure(self, base_path: str = None) -> Dict:
        """
        Analyze the folder structure to identify processes and their organization.
        
        Args:
            base_path: Base path to analyze (defaults to uploads/processes)
            
        Returns:
            Dict containing folder analysis results
        """
        if base_path is None:
            base_path = os.path.join(settings.MEDIA_ROOT, 'uploads', 'processes')
        
        folder_analysis = {
            'base_path': base_path,
            'folders_found': [],
            'files_found': [],
            'potential_processes': [],
            'department_mapping': {},
        }
        
        try:
            if not os.path.exists(base_path):
                self.analysis_report['mapping_errors'].append(f"Base path does not exist: {base_path}")
                return folder_analysis
            
            # Walk through directory structure
            for root, dirs, files in os.walk(base_path):
                rel_path = os.path.relpath(root, base_path)
                
                if rel_path != '.':
                    folder_analysis['folders_found'].append(rel_path)
                
                for file in files:
                    file_path = os.path.join(rel_path, file) if rel_path != '.' else file
                    folder_analysis['files_found'].append({
                        'path': file_path,
                        'name': file,
                        'size': self._get_file_size(os.path.join(root, file)),
                        'extension': self._get_file_extension(file),
                    })
            
            # Identify potential processes from folder structure
            folder_analysis['potential_processes'] = self._identify_processes_from_folders(
                folder_analysis['folders_found']
            )
            
            # Map folders to departments
            folder_analysis['department_mapping'] = self._create_department_mapping(
                folder_analysis['folders_found']
            )
            
            self.analysis_report['folders_analyzed'] = len(folder_analysis['folders_found'])
            self.analysis_report['documents_found'] = len(folder_analysis['files_found'])
            
        except Exception as e:
            self.analysis_report['mapping_errors'].append(f"Error analyzing folder structure: {str(e)}")
        
        return folder_analysis
    
    def consolidate_department_folders(self, folders: List[KnowledgeCentreFolder]) -> Dict[str, List[KnowledgeCentreFolder]]:
        """
        Consolidate duplicate department folders by grouping them under the correct department mapping.
        
        Args:
            folders: List of KnowledgeCentreFolder instances to consolidate
            
        Returns:
            Dict mapping department names to lists of folders
        """
        department_folders = defaultdict(list)
        unmapped_folders = []
        
        for folder in folders:
            dept_name = self._map_folder_to_department_with_fuzzy(folder.name)
            if dept_name:
                department_folders[dept_name].append(folder)
            else:
                unmapped_folders.append(folder)
        
        # Handle unmapped folders
        if unmapped_folders:
            department_folders['UNMAPPED'] = unmapped_folders
            self.analysis_report['mapping_errors'].append(
                f"Found {len(unmapped_folders)} unmapped folders: {[f.name for f in unmapped_folders]}"
            )
        
        # Log consolidation results
        for dept_name, dept_folders in department_folders.items():
            if len(dept_folders) > 1:
                folder_names = [f.name for f in dept_folders]
                self.analysis_report['mapping_errors'].append(
                    f"Consolidated {len(dept_folders)} folders under {dept_name}: {folder_names}"
                )
        
        return dict(department_folders)
    
    def infer_business_processes(self, documents: List[Dict]) -> List[Dict]:
        """
        Analyze document patterns to infer logical business processes.
        
        Args:
            documents: List of document information dictionaries
            
        Returns:
            List of inferred business process dictionaries
        """
        # Group documents by potential business areas
        business_areas = defaultdict(list)
        
        for doc in documents:
            filename = doc.get('filename', '').lower()
            folder_path = doc.get('folder_path', '').lower()
            
            # Extract business area keywords from filename and folder path
            business_area = self._extract_business_area(filename, folder_path)
            business_areas[business_area].append(doc)
        
        # Create logical processes from business areas
        inferred_processes = []
        for business_area, area_docs in business_areas.items():
            if len(area_docs) >= 1:  # At least one document to form a process
                process_info = {
                    'name': self._generate_process_name(business_area, area_docs),
                    'business_area': business_area,
                    'documents': area_docs,
                    'document_count': len(area_docs),
                    'department': self._infer_department_from_documents(area_docs),
                    'confidence': self._calculate_process_confidence(business_area, area_docs),
                    'document_types': self._analyze_document_types(area_docs)
                }
                inferred_processes.append(process_info)
        
        # Sort by confidence and document count
        inferred_processes.sort(key=lambda x: (x['confidence'], x['document_count']), reverse=True)
        
        self.analysis_report['processes_identified'] = len(inferred_processes)
        return inferred_processes
    
    def _map_folder_to_department_with_fuzzy(self, folder_name: str) -> Optional[str]:
        """
        Map a folder name to an appropriate department using fuzzy matching.
        
        Args:
            folder_name: Name of the folder to map
            
        Returns:
            Department name or None if no mapping found
        """
        if not folder_name:
            return None
        
        folder_lower = folder_name.lower().strip()
        
        # Direct mapping first
        if folder_lower in self.DEPARTMENT_MAPPING:
            return self.DEPARTMENT_MAPPING[folder_lower]
        
        # Enhanced matching with scoring
        best_match = None
        best_score = 0.0
        
        for key, dept in self.DEPARTMENT_MAPPING.items():
            score = 0.0
            
            # Exact substring matching (high score)
            if key == folder_lower:
                score = 1.0
            elif key in folder_lower or folder_lower in key:
                # But only if it's not a short substring that could be misleading
                if len(key) >= 3 and (len(key) / len(folder_lower) >= 0.5 or len(folder_lower) / len(key) >= 0.5):
                    score = 0.8
            
            # Fuzzy matching using difflib
            ratio = difflib.SequenceMatcher(None, folder_lower, key).ratio()
            if ratio >= 0.6:
                score = max(score, ratio)
            
            # Check for common abbreviations
            if 'mgmt' in folder_lower and 'management' in key:
                score = max(score, 0.85)
            
            # Check for word-level matching (e.g., "risk mgmt" should match "risk management")
            folder_words = set(folder_lower.replace('mgmt', 'management').split())
            key_words = set(key.split())
            if folder_words & key_words:  # If there's any word overlap
                word_ratio = len(folder_words & key_words) / len(key_words)
                if word_ratio >= 0.5:
                    score = max(score, word_ratio * 0.9)  # Slightly lower than exact match
            
            if score > best_score:
                best_score = score
                best_match = dept
        
        if best_match and best_score >= 0.6:
            return best_match
        
        # Pattern-based matching as fallback
        if any(word in folder_lower for word in ['manager', 'office']):
            if 'general' in folder_lower or 'gm' in folder_lower:
                return 'GENERAL MANAGER\'S OFFICE'
            elif 'engineering' in folder_lower or 'em' in folder_lower:
                return 'ENGINEERING MANAGER\'S OFFICE'
        
        return None
    
    def _map_folder_to_department(self, folder_name: str) -> Optional[str]:
        """
        Map a folder name to an appropriate department (legacy method for backward compatibility).
        
        Args:
            folder_name: Name of the folder to map
            
        Returns:
            Department name or None if no mapping found
        """
        return self._map_folder_to_department_with_fuzzy(folder_name)
    
    def _extract_business_area(self, filename: str, folder_path: str) -> str:
        """
        Extract business area from filename and folder path.
        
        Args:
            filename: Document filename
            folder_path: Folder path containing the document
            
        Returns:
            Business area identifier
        """
        # Common business area keywords
        business_keywords = {
            'procurement': ['procurement', 'purchase', 'buying', 'tender', 'supplier', 'vendor'],
            'maintenance': ['maintenance', 'repair', 'service', 'upkeep', 'preventive'],
            'safety': ['safety', 'health', 'hazard', 'accident', 'incident', 'ppe'],
            'finance': ['finance', 'budget', 'cost', 'payment', 'invoice', 'accounting'],
            'hr': ['hr', 'human', 'employee', 'staff', 'personnel', 'recruitment'],
            'operations': ['operations', 'production', 'workflow', 'process', 'procedure'],
            'quality': ['quality', 'audit', 'compliance', 'standard', 'iso'],
            'risk': ['risk', 'opportunity', 'assessment', 'mitigation', 'register'],
            'training': ['training', 'competence', 'skill', 'development', 'education'],
            'planning': ['planning', 'strategy', 'plan', 'schedule', 'forecast']
        }
        
        combined_text = f"{filename} {folder_path}".lower()
        
        # Find matching business areas with priority scoring
        area_scores = {}
        for area, keywords in business_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in combined_text:
                    # Give higher score for exact matches in filename
                    if keyword in filename.lower():
                        score += 2
                    else:
                        score += 1
            if score > 0:
                area_scores[area] = score
        
        if area_scores:
            # Return the area with highest score
            return max(area_scores.items(), key=lambda x: x[1])[0]
        
        # Fallback: use folder name or filename parts
        if folder_path:
            folder_parts = folder_path.split('/')
            if len(folder_parts) > 1:
                return folder_parts[-1].replace('_', ' ').replace('-', ' ')
        
        # Last resort: use filename without extension
        base_filename = filename.split('.')[0] if '.' in filename else filename
        return base_filename.replace('_', ' ').replace('-', ' ')
    
    def _generate_process_name(self, business_area: str, documents: List[Dict]) -> str:
        """
        Generate a meaningful process name from business area and documents.
        
        Args:
            business_area: Business area identifier
            documents: List of documents in this process
            
        Returns:
            Generated process name
        """
        # Clean up business area name
        area_name = business_area.replace('_', ' ').title()
        
        # Get department from documents
        dept_name = self._infer_department_from_documents(documents)
        
        # Create process name
        if dept_name and dept_name != 'UNMAPPED':
            # Extract department abbreviation
            dept_abbrev = self._get_department_abbreviation(dept_name)
            return f"{dept_abbrev} {area_name} Process"
        else:
            return f"{area_name} Process"
    
    def _infer_department_from_documents(self, documents: List[Dict]) -> Optional[str]:
        """
        Infer department from document folder paths and metadata.
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            Inferred department name
        """
        department_votes = defaultdict(int)
        
        for doc in documents:
            # Try to get department from folder path
            folder_path = doc.get('folder_path', '')
            if folder_path:
                folder_parts = folder_path.split('/')
                for part in folder_parts:
                    dept = self._map_folder_to_department_with_fuzzy(part)
                    if dept:
                        department_votes[dept] += 1
            
            # Try to get department from document metadata
            if 'section' in doc and doc['section']:
                # Map section to department if possible
                section_dept = self._map_section_to_department(doc['section'])
                if section_dept:
                    department_votes[section_dept] += 1
        
        if department_votes:
            # Return department with most votes
            return max(department_votes.items(), key=lambda x: x[1])[0]
        
        return 'UNMAPPED'
    
    def _calculate_process_confidence(self, business_area: str, documents: List[Dict]) -> float:
        """
        Calculate confidence score for inferred process.
        
        Args:
            business_area: Business area identifier
            documents: List of documents in process
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.5  # Base confidence
        
        # Boost confidence based on document count
        doc_count = len(documents)
        if doc_count >= 3:
            confidence += 0.3
        elif doc_count >= 2:
            confidence += 0.2
        elif doc_count == 1:
            confidence += 0.1
        
        # Boost confidence if documents have clear department mapping
        dept_mapped_count = sum(1 for doc in documents 
                               if self._infer_department_from_documents([doc]) != 'UNMAPPED')
        if dept_mapped_count > 0:
            confidence += 0.2 * (dept_mapped_count / doc_count)
        
        # Boost confidence if business area is well-defined
        if business_area and len(business_area.split()) <= 2:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _analyze_document_types(self, documents: List[Dict]) -> Dict[str, int]:
        """
        Analyze document types in the process.
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            Dict mapping document types to counts
        """
        type_counts = defaultdict(int)
        
        for doc in documents:
            filename = doc.get('filename', '').lower()
            
            # Simple type detection based on filename
            if any(keyword in filename for keyword in ['map', 'flow', 'chart', 'diagram']):
                type_counts['process_map'] += 1
            elif any(keyword in filename for keyword in ['procedure', 'manual', 'instruction', 'sop']):
                type_counts['procedure'] += 1
            elif any(keyword in filename for keyword in ['risk', 'opportunity', 'register']):
                type_counts['risk_register'] += 1
            else:
                type_counts['other'] += 1
        
        return dict(type_counts)
    
    def _get_department_abbreviation(self, dept_name: str) -> str:
        """
        Get department abbreviation for process naming.
        
        Args:
            dept_name: Full department name
            
        Returns:
            Department abbreviation
        """
        abbreviations = {
            'GENERAL MANAGER\'S OFFICE': 'GM',
            'ENGINEERING MANAGER\'S OFFICE': 'EM',
            'DISTRICTS': 'DIST',
            'NETWORK DEVELOPMENT': 'ND',
            'OPERATIONS AND MAINTENANCE': 'OPS',
            'COMMERCIAL': 'COM',
            'FINANCE': 'FIN',
            'PROCUREMENT': 'PROC',
            'RISK MANAGEMENT': 'RISK',
            'HUMAN RESOURCES AND ADMINISTRATION': 'HR',
            'INFORMATION AND COMMUNICATION TECHNOLOGY': 'ICT',
            'SAFETY': 'SAFE',
        }
        
        return abbreviations.get(dept_name, dept_name[:3].upper())
    
    def _map_section_to_department(self, section: str) -> Optional[str]:
        """
        Map section information to department.
        
        Args:
            section: Section identifier or name
            
        Returns:
            Department name or None
        """
        # This would need to be implemented based on your section-to-department mapping
        # For now, return None as we don't have the specific mapping
        return None
    
    def _identify_processes_from_folders(self, folders: List[str]) -> List[Dict]:
        """
        Identify potential processes from folder names.
        
        Args:
            folders: List of folder paths
            
        Returns:
            List of potential process information
        """
        processes = []
        
        for folder in folders:
            # Skip system folders
            if any(skip in folder.lower() for skip in ['.git', '__pycache__', 'temp', 'tmp']):
                continue
            
            # Extract process name from folder path
            folder_parts = folder.split(os.sep)
            process_name = folder_parts[-1]  # Use the deepest folder as process name
            
            # Map to department
            dept_name = self._map_folder_to_department(process_name)
            if not dept_name and len(folder_parts) > 1:
                # Try parent folder for department mapping
                dept_name = self._map_folder_to_department(folder_parts[-2])
            
            processes.append({
                'name': process_name,
                'folder_path': folder,
                'department': dept_name,
                'confidence': self._calculate_mapping_confidence(process_name, dept_name),
            })
        
        return processes
    
    def _create_department_mapping(self, folders: List[str]) -> Dict[str, List[str]]:
        """
        Create mapping of departments to their folders.
        
        Args:
            folders: List of folder paths
            
        Returns:
            Dict mapping department names to folder lists
        """
        mapping = {}
        
        for folder in folders:
            dept_name = self._map_folder_to_department(folder)
            if dept_name:
                if dept_name not in mapping:
                    mapping[dept_name] = []
                mapping[dept_name].append(folder)
        
        return mapping
    
    def _calculate_mapping_confidence(self, process_name: str, dept_name: str) -> float:
        """
        Calculate confidence score for process-to-department mapping.
        
        Args:
            process_name: Name of the process
            dept_name: Mapped department name
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not dept_name:
            return 0.0
        
        # High confidence for direct matches
        process_lower = process_name.lower()
        for key in self.DEPARTMENT_MAPPING:
            if key in process_lower:
                return 0.9
        
        # Medium confidence for partial matches
        dept_words = dept_name.lower().split()
        process_words = process_lower.split()
        
        common_words = set(dept_words) & set(process_words)
        if common_words:
            return 0.7
        
        # Low confidence for mapped but no clear connection
        return 0.3
    
    def _get_file_size(self, file_path: str) -> int:
        """Get file size in bytes."""
        try:
            return os.path.getsize(file_path)
        except (OSError, IOError):
            return 0
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension."""
        return filename.split('.')[-1].lower() if '.' in filename else ''
    
    def _get_all_files_in_folder(self, folder: 'KnowledgeCentreFolder') -> List[Dict]:
        """
        Recursively get all files in a folder and its subfolders.
        
        Args:
            folder: KnowledgeCentreFolder instance
            
        Returns:
            List of file information dictionaries
        """
        files = []
        
        # Get direct files in this folder
        for file in folder.files.filter(archived=False):
            files.append({
                'id': file.id,
                'filename': file.filename,
                'folder_name': folder.name,
                'folder_path': self._get_folder_path(folder),
                'section': file.section.section if file.section else '',
                'region': file.region.region if file.region else '',
                'created_at': file.created_on,
                'source': 'knowledge_center_folder'
            })
        
        # Recursively get files from subfolders
        for subfolder in folder.subfolders.all():
            files.extend(self._get_all_files_in_folder(subfolder))
        
        return files
    
    def _get_folder_path(self, folder: 'KnowledgeCentreFolder') -> str:
        """
        Get the full path of a folder from root.
        
        Args:
            folder: KnowledgeCentreFolder instance
            
        Returns:
            Full folder path as string
        """
        path_parts = []
        current = folder
        
        while current:
            path_parts.append(current.name)
            current = current.parent
        
        return '/'.join(reversed(path_parts))
    
    def get_analysis_report(self) -> Dict:
        """
        Get the complete analysis report.
        
        Returns:
            Dict containing analysis statistics and errors
        """
        return self.analysis_report.copy()


class DocumentCategorizationService:
    """
    Service class for categorizing documents by naming conventions with context-aware categorization.
    """
    
    # Enhanced document type patterns with filename, folder, and content hints
    ENHANCED_DOCUMENT_PATTERNS = {
        'process_map': {
            'filename_patterns': [
                r'process[\s_-]*map',
                r'flow[\s_-]*chart',
                r'workflow',
                r'process[\s_-]*flow',
                r'flowchart',
                r'diagram',
                r'\bmap\b',  # Word boundary for 'map'
                r'process[\s_-]*diagram',
                r'business[\s_-]*process',
            ],
            'folder_patterns': [
                r'process[\s_-]*maps?',
                r'workflows?',
                r'diagrams?',
                r'flowcharts?',
                r'business[\s_-]*process',
            ],
            'content_hints': [
                'flowchart', 'diagram', 'process flow', 'workflow', 'business process',
                'swim lane', 'decision tree', 'process model'
            ]
        },
        'procedure': {
            'filename_patterns': [
                r'procedure',
                r'manual',
                r'guide',
                r'instruction',
                r'sop',  # Standard Operating Procedure
                r'work[\s_-]*instruction',
                r'handbook',
                r'policy',
                r'guideline',
                r'protocol',
                r'standard',
            ],
            'folder_patterns': [
                r'procedures?',
                r'manuals?',
                r'instructions?',
                r'guidelines?',
                r'policies',
                r'protocols?',
                r'standards?',
                r'handbooks?',
            ],
            'content_hints': [
                'step by step', 'how to', 'guidelines', 'instructions', 'procedure',
                'standard operating', 'work instruction', 'protocol', 'policy'
            ]
        },
        'risk_register': {
            'filename_patterns': [
                r'risk[\s_-]*register',
                r'risk[\s_-]*assessment',
                r'opportunity[\s_-]*register',
                r'risk[\s_-]*and[\s_-]*opportunity',
                r'hazard[\s_-]*register',
                r'risk[\s_-]*matrix',
                r'\brisk\b',  # Word boundary for 'risk'
                r'opportunity',
                r'hazard',
            ],
            'folder_patterns': [
                r'risk',
                r'opportunity',
                r'hazards?',
                r'risk[\s_-]*management',
                r'risk[\s_-]*assessment',
            ],
            'content_hints': [
                'risk matrix', 'hazard', 'mitigation', 'risk assessment', 'opportunity',
                'threat', 'vulnerability', 'impact', 'likelihood', 'risk register'
            ]
        },
    }
    
    # Legacy patterns for backward compatibility
    DOCUMENT_PATTERNS = {
        'process_map': [
            r'process[\s_-]*map',
            r'flow[\s_-]*chart',
            r'workflow',
            r'process[\s_-]*flow',
            r'flowchart',
            r'diagram',
            r'\bmap\b',  # Word boundary for 'map'
        ],
        'procedure': [
            r'procedure',
            r'manual',
            r'guide',
            r'instruction',
            r'sop',  # Standard Operating Procedure
            r'work[\s_-]*instruction',
            r'handbook',
            r'policy',
        ],
        'risk_register': [
            r'risk[\s_-]*register',
            r'risk[\s_-]*assessment',
            r'opportunity[\s_-]*register',
            r'risk[\s_-]*and[\s_-]*opportunity',
            r'hazard[\s_-]*register',
            r'risk[\s_-]*matrix',
            r'\brisk\b',  # Word boundary for 'risk'
        ],
    }
    
    def __init__(self):
        self.categorization_report = {
            'documents_processed': 0,
            'documents_categorized': 0,
            'uncategorized_documents': [],
            'categorization_errors': [],
            'type_distribution': {
                'process_map': 0,
                'procedure': 0,
                'risk_register': 0,
                'uncategorized': 0,
            },
        }
    
    def categorize_document(self, filename: str, content_hint: str = None, folder_context: str = None) -> Tuple[Optional[str], float]:
        """
        Categorize a document based on its filename, content hint, and folder context with enhanced confidence scoring.
        
        Args:
            filename: Name of the file
            content_hint: Optional hint about document content
            folder_context: Optional folder path or context information
            
        Returns:
            Tuple of (document_type, confidence_score)
        """
        self.categorization_report['documents_processed'] += 1
        
        try:
            if not filename or not filename.strip():
                return self._apply_fallback_categorization(filename, "Empty filename")
            
            filename_lower = filename.lower()
            content_lower = (content_hint or '').lower()
            folder_lower = (folder_context or '').lower()
            
            best_match = None
            best_score = 0.0
            confidence_details = {}
            
            # Use enhanced pattern matching with context awareness
            for doc_type, pattern_config in self.ENHANCED_DOCUMENT_PATTERNS.items():
                score = self._calculate_enhanced_pattern_score(
                    filename_lower, content_lower, folder_lower, pattern_config
                )
                confidence_details[doc_type] = score
                
                if score > best_score:
                    best_score = score
                    best_match = doc_type
            
            # If no match found, set a default best_match for fallback processing
            if best_match is None and best_score == 0.0:
                best_match = 'procedure'  # Default for fallback consideration
            
            # Apply confidence scoring system
            final_type, final_confidence = self._apply_confidence_scoring(
                best_match, best_score, confidence_details, filename, content_hint, folder_context
            )
            
            # Update categorization report
            if final_type:
                self.categorization_report['documents_categorized'] += 1
                self.categorization_report['type_distribution'][final_type] += 1
            else:
                self.categorization_report['type_distribution']['uncategorized'] += 1
            
            return final_type, final_confidence
            
        except Exception as e:
            self.categorization_report['categorization_errors'].append({
                'filename': filename,
                'error': str(e),
            })
            return self._apply_fallback_categorization(filename, f"Error: {str(e)}")
    
    def categorize_documents_batch(self, documents: List[Dict]) -> List[Dict]:
        """
        Categorize multiple documents in batch with enhanced context awareness.
        
        Args:
            documents: List of document info dicts with 'filename', optional 'content_hint', and 'folder_context'
            
        Returns:
            List of documents with added 'document_type' and 'confidence' fields
        """
        categorized_docs = []
        
        for doc in documents:
            filename = doc.get('filename', '')
            content_hint = doc.get('content_hint', '')
            folder_context = doc.get('folder_context', '') or doc.get('folder_path', '')
            
            doc_type, confidence = self.categorize_document(filename, content_hint, folder_context)
            
            categorized_doc = doc.copy()
            categorized_doc.update({
                'document_type': doc_type,
                'confidence': confidence,
            })
            categorized_docs.append(categorized_doc)
        
        return categorized_docs
    
    def _calculate_enhanced_pattern_score(self, filename: str, content: str, folder: str, pattern_config: Dict) -> float:
        """
        Calculate enhanced pattern score using filename, content, and folder context.
        
        Args:
            filename: Lowercase filename
            content: Lowercase content hint
            folder: Lowercase folder context
            pattern_config: Pattern configuration with filename_patterns, folder_patterns, and content_hints
            
        Returns:
            Enhanced confidence score between 0.0 and 1.0
        """
        total_score = 0.0
        weight_sum = 0.0
        
        # Filename patterns (highest weight)
        filename_score = self._calculate_pattern_score(filename, pattern_config.get('filename_patterns', []))
        if filename_score > 0:
            total_score += filename_score * 0.5  # 50% weight for filename
            weight_sum += 0.5
        
        # Folder patterns (medium weight)
        folder_score = self._calculate_pattern_score(folder, pattern_config.get('folder_patterns', []))
        if folder_score > 0:
            total_score += folder_score * 0.3  # 30% weight for folder context
            weight_sum += 0.3
        
        # Content hints (lower weight but still valuable)
        content_score = self._calculate_content_hint_score(content, pattern_config.get('content_hints', []))
        if content_score > 0:
            total_score += content_score * 0.2  # 20% weight for content hints
            weight_sum += 0.2
        
        # Calculate weighted average, but ensure we have some signal
        if weight_sum > 0:
            base_score = total_score / weight_sum
            
            # Boost score if multiple sources match
            source_count = sum([1 for score in [filename_score, folder_score, content_score] if score > 0])
            if source_count > 1:
                base_score = min(base_score * (1 + 0.1 * (source_count - 1)), 1.0)
            
            return base_score
        
        return 0.0
    
    def _calculate_content_hint_score(self, content: str, hints: List[str]) -> float:
        """
        Calculate score based on content hints using substring matching.
        
        Args:
            content: Content text to analyze
            hints: List of content hint strings
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not content or not hints:
            return 0.0
        
        matches = 0
        for hint in hints:
            if hint.lower() in content:
                matches += 1
        
        if matches > 0:
            score = matches / len(hints)
            # Boost score for multiple matches
            if matches > 1:
                score = min(score * 1.2, 1.0)
            return score
        
        return 0.0
    
    def _apply_confidence_scoring(self, best_match: str, best_score: float, confidence_details: Dict, 
                                filename: str, content_hint: str, folder_context: str) -> Tuple[Optional[str], float]:
        """
        Apply confidence scoring system to determine final categorization.
        
        Args:
            best_match: Best matching document type
            best_score: Best matching score
            confidence_details: Detailed scores for all types
            filename: Original filename
            content_hint: Content hint
            folder_context: Folder context
            
        Returns:
            Tuple of (final_document_type, final_confidence_score)
        """
        # Define confidence thresholds
        HIGH_CONFIDENCE_THRESHOLD = 0.6
        MEDIUM_CONFIDENCE_THRESHOLD = 0.3
        LOW_CONFIDENCE_THRESHOLD = 0.15
        FALLBACK_THRESHOLD = 0.05
        
        if best_score >= HIGH_CONFIDENCE_THRESHOLD:
            # High confidence - use the best match
            return best_match, best_score
        elif best_score >= MEDIUM_CONFIDENCE_THRESHOLD:
            # Medium confidence - check for competing matches
            competing_matches = [
                (doc_type, score) for doc_type, score in confidence_details.items()
                if score >= MEDIUM_CONFIDENCE_THRESHOLD and doc_type != best_match
            ]
            
            if not competing_matches:
                # No competing matches, use best match
                return best_match, best_score
            else:
                # Competing matches exist, reduce confidence slightly
                adjusted_confidence = best_score * 0.9
                return best_match, adjusted_confidence
        elif best_score >= LOW_CONFIDENCE_THRESHOLD:
            # Low confidence - still use the match but with reduced confidence
            return best_match, best_score * 0.8
        elif best_score >= FALLBACK_THRESHOLD or best_score == 0.0:
            # Very low confidence or no match - apply fallback categorization
            return self._apply_fallback_categorization(
                filename, f"Low confidence match: {best_match} ({best_score:.2f})", max(best_score * 0.6, 0.1)
            )
        else:
            # This branch should rarely be reached now
            self.categorization_report['uncategorized_documents'].append({
                'filename': filename,
                'reason': f"No confident match found (best: {best_match}, score: {best_score:.2f})",
                'best_match': best_match,
                'best_score': best_score,
                'fallback_applied': False,
            })
            self.categorization_report['type_distribution']['uncategorized'] += 1
            return None, 0.0
    
    def _apply_fallback_categorization(self, filename: str, reason: str, base_confidence: float = 0.25) -> Tuple[str, float]:
        """
        Apply fallback categorization strategy that defaults to "procedure" type for documents that show some categorization potential.
        
        Args:
            filename: Original filename
            reason: Reason for fallback
            base_confidence: Base confidence for fallback (default 0.25)
            
        Returns:
            Tuple of ("procedure", confidence_score)
        """
        # Check if the document has any characteristics that suggest it could be a document
        filename_lower = filename.lower()
        
        # Only apply fallback if the document has strong document-like characteristics
        # Be very selective about when to apply fallback to match expected behavior
        document_extensions = ['.pdf', '.doc', '.docx', '.rtf', '.odt']
        strong_document_keywords = ['manual', 'guide', 'instruction', 'procedure', 'policy', 'handbook', 'sop']
        
        has_document_extension = any(ext in filename_lower for ext in document_extensions)
        has_strong_keywords = any(keyword in filename_lower for keyword in strong_document_keywords)
        
        # Only apply fallback if we have both a document extension AND strong keywords,
        # OR if we have very strong keywords regardless of extension
        has_document_indicators = (has_document_extension and has_strong_keywords) or (
            any(keyword in filename_lower for keyword in ['manual', 'procedure', 'handbook', 'guide'])
        )
        
        if has_document_indicators:
            # Log the fallback decision
            self.categorization_report['uncategorized_documents'].append({
                'filename': filename,
                'reason': reason,
                'fallback_applied': True,
                'fallback_type': 'procedure',
            })
            
            # Default to "procedure" type with moderate confidence
            fallback_confidence = min(base_confidence, 0.4)  # Cap fallback confidence at 0.4
            
            # Update distribution for procedure (since we're defaulting to it)
            self.categorization_report['type_distribution']['procedure'] += 1
            self.categorization_report['documents_categorized'] += 1
            
            return 'procedure', fallback_confidence
        else:
            # No fallback for files that don't look like documents
            self.categorization_report['uncategorized_documents'].append({
                'filename': filename,
                'reason': f"{reason} - No document indicators found",
                'fallback_applied': False,
            })
            self.categorization_report['type_distribution']['uncategorized'] += 1
            return None, 0.0
    
    def _calculate_pattern_score(self, text: str, patterns: List[str]) -> float:
        """
        Calculate how well text matches a list of patterns with improved scoring.
        
        Args:
            text: Text to analyze
            patterns: List of regex patterns
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not text or not patterns:
            return 0.0
        
        matches = 0
        total_patterns = len(patterns)
        match_quality_sum = 0.0
        
        for pattern in patterns:
            try:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    matches += 1
                    # Calculate match quality based on match length and position
                    match_length = len(match.group())
                    text_length = len(text)
                    
                    # Higher quality for longer matches and matches at word boundaries
                    quality = match_length / text_length
                    
                    # Boost quality for matches at the beginning of text
                    if match.start() == 0:
                        quality *= 1.2
                    
                    # Boost quality for word boundary matches
                    if match.start() == 0 or text[match.start() - 1].isspace():
                        quality *= 1.1
                    
                    match_quality_sum += min(quality, 1.0)
                    
            except re.error:
                # Skip invalid regex patterns
                total_patterns -= 1
                continue
        
        # Calculate score based on match ratio and quality
        if total_patterns == 0:
            return 0.0
        
        # Base score from match ratio
        match_ratio = matches / total_patterns
        
        # Average match quality
        avg_quality = match_quality_sum / matches if matches > 0 else 0.0
        
        # Combine ratio and quality
        score = (match_ratio * 0.7) + (avg_quality * 0.3)
        
        # Boost score if multiple patterns match
        if matches > 1:
            score = min(score * (1 + 0.1 * (matches - 1)), 1.0)
        
        return min(score, 1.0)
    
    def get_categorization_report(self) -> Dict:
        """
        Get the complete categorization report with enhanced details.
        
        Returns:
            Dict containing categorization statistics and errors
        """
        report = self.categorization_report.copy()
        
        # Add additional statistics
        total_processed = report['documents_processed']
        if total_processed > 0:
            report['categorization_rate'] = report['documents_categorized'] / total_processed
            report['fallback_rate'] = len([doc for doc in report['uncategorized_documents'] 
                                         if doc.get('fallback_applied', False)]) / total_processed
        else:
            report['categorization_rate'] = 0.0
            report['fallback_rate'] = 0.0
        
        return report
    
    def categorize_document_legacy(self, filename: str, content_hint: str = None) -> Tuple[Optional[str], float]:
        """
        Legacy method for backward compatibility with old signature.
        
        Args:
            filename: Name of the file
            content_hint: Optional hint about document content
            
        Returns:
            Tuple of (document_type, confidence_score)
        """
        return self.categorize_document(filename, content_hint, None)


def get_migration_services() -> Tuple[FolderAnalysisService, DocumentCategorizationService]:
    """
    Factory function to get migration service instances.
    
    Returns:
        Tuple of (FolderAnalysisService, DocumentCategorizationService)
    """
    return FolderAnalysisService(), DocumentCategorizationService()