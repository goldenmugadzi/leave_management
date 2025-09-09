"""
ProcessCreationStrategy class for intelligent process generation.

This module provides intelligent process creation based on document analysis,
business function grouping, and department-based naming conventions.
"""
import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import ProcessDepartment, Process
from .services import FolderAnalysisService, DocumentCategorizationService


@dataclass
class BusinessFunction:
    """Represents a business function identified from document analysis."""
    name: str
    keywords: List[str]
    documents: List[Dict]
    department: Optional[str] = None
    confidence: float = 0.0
    document_types: Dict[str, int] = None
    
    def __post_init__(self):
        if self.document_types is None:
            self.document_types = {}


@dataclass
class ProcessCandidate:
    """Represents a candidate process to be created."""
    name: str
    process_code: str
    department: str
    business_function: BusinessFunction
    documents: List[Dict]
    confidence: float
    duplicate_handling_applied: bool = False
    original_name: Optional[str] = None
    original_code: Optional[str] = None


class ProcessCreationStrategy:
    """
    Strategy class for creating logical business processes from document analysis.
    
    This class implements intelligent process generation by:
    1. Analyzing documents to identify business functions
    2. Grouping related documents under logical processes
    3. Generating meaningful process names with department codes
    4. Handling duplicates with sequential numbering
    """
    
    # Business function keywords for grouping documents
    BUSINESS_FUNCTION_KEYWORDS = {
        'asset_management': {
            'keywords': ['asset', 'equipment', 'maintenance', 'repair', 'service', 'upkeep', 'preventive'],
            'weight': 1.0,
            'aliases': ['asset management', 'equipment management', 'maintenance management']
        },
        'procurement': {
            'keywords': ['procurement', 'purchase', 'buying', 'tender', 'supplier', 'vendor', 'contract'],
            'weight': 1.0,
            'aliases': ['purchasing', 'sourcing', 'vendor management']
        },
        'safety_management': {
            'keywords': ['safety', 'health', 'hazard', 'accident', 'incident', 'ppe', 'emergency'],
            'weight': 1.0,
            'aliases': ['health and safety', 'occupational safety', 'emergency management']
        },
        'financial_management': {
            'keywords': ['finance', 'budget', 'cost', 'payment', 'invoice', 'accounting', 'financial'],
            'weight': 1.0,
            'aliases': ['finance', 'accounting', 'budgeting']
        },
        'human_resources': {
            'keywords': ['hr', 'human', 'employee', 'staff', 'personnel', 'recruitment', 'training'],
            'weight': 1.0,
            'aliases': ['human resources', 'personnel management', 'staff management']
        },
        'operations': {
            'keywords': ['operations', 'production', 'workflow', 'process', 'procedure', 'operational'],
            'weight': 0.8,  # Lower weight as it's more generic
            'aliases': ['operational management', 'business operations']
        },
        'quality_management': {
            'keywords': ['quality', 'audit', 'compliance', 'standard', 'iso', 'certification'],
            'weight': 1.0,
            'aliases': ['quality assurance', 'compliance management']
        },
        'risk_management': {
            'keywords': ['risk', 'opportunity', 'assessment', 'mitigation', 'register', 'threat'],
            'weight': 1.0,
            'aliases': ['risk assessment', 'opportunity management']
        },
        'project_management': {
            'keywords': ['project', 'planning', 'schedule', 'milestone', 'deliverable', 'timeline'],
            'weight': 1.0,
            'aliases': ['project planning', 'project execution']
        },
        'communication': {
            'keywords': ['communication', 'meeting', 'report', 'notification', 'announcement'],
            'weight': 0.7,  # Lower weight as it's often supporting
            'aliases': ['communications', 'reporting']
        },
        'network_development': {
            'keywords': ['network', 'development', 'expansion', 'infrastructure', 'construction'],
            'weight': 1.0,
            'aliases': ['infrastructure development', 'network expansion']
        },
        'customer_service': {
            'keywords': ['customer', 'service', 'client', 'complaint', 'feedback', 'satisfaction'],
            'weight': 1.0,
            'aliases': ['customer management', 'client service']
        }
    }
    
    # Department code mapping for process naming
    DEPARTMENT_CODES = {
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
        'UNMAPPED': 'UNK'
    }
    
    def __init__(self):
        """Initialize the process creation strategy."""
        self.folder_analysis_service = FolderAnalysisService()
        self.document_categorization_service = DocumentCategorizationService()
        self.creation_report = {
            'documents_analyzed': 0,
            'business_functions_identified': 0,
            'processes_created': 0,
            'duplicates_handled': 0,
            'errors': [],
            'function_distribution': {},
            'department_distribution': {},
        }
        
        # Track existing process codes and names to avoid duplicates
        self._existing_codes: Set[str] = set()
        self._existing_names: Set[str] = set()
        self._code_counters: Dict[str, int] = defaultdict(int)
        
        # Initialize with existing processes
        self._load_existing_processes()
    
    def analyze_business_functions(self, documents: List[Dict]) -> List[BusinessFunction]:
        """
        Analyze documents to identify business functions and group related documents.
        
        Args:
            documents: List of document dictionaries with metadata
            
        Returns:
            List of identified business functions with grouped documents
        """
        self.creation_report['documents_analyzed'] = len(documents)
        
        # Group documents by business function
        function_groups = defaultdict(list)
        
        for doc in documents:
            # Analyze document to identify business functions
            functions = self._identify_document_functions(doc)
            
            # Assign document to the best matching function
            if functions:
                best_function = max(functions.items(), key=lambda x: x[1])[0]
                function_groups[best_function].append(doc)
            else:
                # Fallback to generic operations if no specific function identified
                function_groups['operations'].append(doc)
        
        # Create BusinessFunction objects
        business_functions = []
        for function_name, function_docs in function_groups.items():
            if not function_docs:
                continue
                
            function_config = self.BUSINESS_FUNCTION_KEYWORDS.get(function_name, {})
            
            # Infer department from documents
            department = self._infer_department_from_documents(function_docs)
            
            # Calculate confidence based on document analysis
            confidence = self._calculate_function_confidence(function_name, function_docs)
            
            # Analyze document types in this function
            document_types = self._analyze_document_types(function_docs)
            
            business_function = BusinessFunction(
                name=function_name,
                keywords=function_config.get('keywords', []),
                documents=function_docs,
                department=department,
                confidence=confidence,
                document_types=document_types
            )
            
            business_functions.append(business_function)
        
        # Sort by confidence and document count
        business_functions.sort(key=lambda x: (x.confidence, len(x.documents)), reverse=True)
        
        self.creation_report['business_functions_identified'] = len(business_functions)
        self.creation_report['function_distribution'] = {
            bf.name: len(bf.documents) for bf in business_functions
        }
        
        return business_functions
    
    def create_process_candidates(self, business_functions: List[BusinessFunction]) -> List[ProcessCandidate]:
        """
        Create process candidates from business functions with naming conventions.
        
        Args:
            business_functions: List of business functions to convert to processes
            
        Returns:
            List of process candidates ready for creation
        """
        process_candidates = []
        
        for business_function in business_functions:
            # Generate process name and code
            process_name = self._generate_process_name(business_function)
            process_code = self._generate_process_code(business_function)
            
            # Handle duplicates
            final_name, final_code = self._handle_duplicates(
                process_name, process_code, business_function.department
            )
            
            # Create process candidate
            candidate = ProcessCandidate(
                name=final_name,
                process_code=final_code,
                department=business_function.department or 'UNMAPPED',
                business_function=business_function,
                documents=business_function.documents,
                confidence=business_function.confidence,
                duplicate_handling_applied=(final_name != process_name or final_code != process_code),
                original_name=process_name if final_name != process_name else None,
                original_code=process_code if final_code != process_code else None
            )
            
            process_candidates.append(candidate)
            
            # Track the new names and codes
            self._existing_names.add(final_name)
            self._existing_codes.add(final_code)
        
        return process_candidates
    
    def create_processes_from_candidates(self, candidates: List[ProcessCandidate]) -> List[Process]:
        """
        Create actual Process instances from process candidates.
        
        Args:
            candidates: List of process candidates to create
            
        Returns:
            List of created Process instances
        """
        created_processes = []
        
        with transaction.atomic():
            for candidate in candidates:
                try:
                    # Get or create department
                    department = self._get_or_create_department(candidate.department)
                    
                    # Create process
                    process = Process(
                        name=candidate.name,
                        process_code=candidate.process_code,
                        department=department,
                        description=self._generate_process_description(candidate),
                        is_active=True
                    )
                    
                    # Validate before saving
                    process.full_clean()
                    process.save()
                    
                    created_processes.append(process)
                    self.creation_report['processes_created'] += 1
                    
                    if candidate.duplicate_handling_applied:
                        self.creation_report['duplicates_handled'] += 1
                    
                except ValidationError as e:
                    error_msg = f"Validation error creating process '{candidate.name}': {e}"
                    self.creation_report['errors'].append(error_msg)
                    
                except Exception as e:
                    error_msg = f"Error creating process '{candidate.name}': {str(e)}"
                    self.creation_report['errors'].append(error_msg)
        
        # Update department distribution
        self.creation_report['department_distribution'] = {
            dept: len([p for p in created_processes if p.department.name == dept])
            for dept in set(p.department.name for p in created_processes)
        }
        
        return created_processes
    
    def _identify_document_functions(self, document: Dict) -> Dict[str, float]:
        """
        Identify business functions for a document based on filename and context.
        
        Args:
            document: Document dictionary with metadata
            
        Returns:
            Dict mapping function names to confidence scores
        """
        filename = document.get('filename', '').lower()
        folder_path = document.get('folder_path', '').lower()
        content_hint = document.get('content_hint', '').lower()
        
        # Combine all text for analysis
        combined_text = f"{filename} {folder_path} {content_hint}"
        
        function_scores = {}
        
        for function_name, config in self.BUSINESS_FUNCTION_KEYWORDS.items():
            score = 0.0
            keywords = config.get('keywords', [])
            weight = config.get('weight', 1.0)
            
            # Calculate keyword matches
            for keyword in keywords:
                if keyword in combined_text:
                    # Higher score for filename matches
                    if keyword in filename:
                        score += 2.0
                    elif keyword in folder_path:
                        score += 1.5
                    else:
                        score += 1.0
            
            # Normalize score by number of keywords and apply weight
            if keywords:
                normalized_score = (score / len(keywords)) * weight
                function_scores[function_name] = min(normalized_score, 1.0)
        
        return function_scores
    
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
            # Try folder analysis service for department mapping
            folder_path = doc.get('folder_path', '')
            if folder_path:
                folder_parts = folder_path.split('/')
                for part in folder_parts:
                    dept = self.folder_analysis_service._map_folder_to_department_with_fuzzy(part)
                    if dept:
                        department_votes[dept] += 1
            
            # Try direct department field if available
            if 'department' in doc and doc['department']:
                department_votes[doc['department']] += 2  # Higher weight for explicit department
        
        if department_votes:
            return max(department_votes.items(), key=lambda x: x[1])[0]
        
        return 'UNMAPPED'
    
    def _calculate_function_confidence(self, function_name: str, documents: List[Dict]) -> float:
        """
        Calculate confidence score for a business function.
        
        Args:
            function_name: Name of the business function
            documents: Documents in this function
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_confidence = 0.5
        
        # Boost confidence based on document count
        doc_count = len(documents)
        if doc_count >= 5:
            base_confidence += 0.3
        elif doc_count >= 3:
            base_confidence += 0.2
        elif doc_count >= 2:
            base_confidence += 0.1
        
        # Boost confidence if function has specific keywords
        function_config = self.BUSINESS_FUNCTION_KEYWORDS.get(function_name, {})
        if function_config.get('weight', 1.0) >= 1.0:
            base_confidence += 0.1
        
        # Boost confidence if documents have consistent department mapping
        departments = [self._infer_department_from_documents([doc]) for doc in documents]
        consistent_dept_count = sum(1 for dept in departments if dept != 'UNMAPPED')
        if consistent_dept_count > 0:
            base_confidence += 0.1 * (consistent_dept_count / len(documents))
        
        return min(base_confidence, 1.0)
    
    def _analyze_document_types(self, documents: List[Dict]) -> Dict[str, int]:
        """
        Analyze document types in a business function.
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            Dict mapping document types to counts
        """
        type_counts = defaultdict(int)
        
        for doc in documents:
            filename = doc.get('filename', '')
            folder_context = doc.get('folder_path', '')
            
            doc_type, confidence = self.document_categorization_service.categorize_document(
                filename, folder_context=folder_context
            )
            
            if doc_type:
                type_counts[doc_type] += 1
            else:
                type_counts['other'] += 1
        
        return dict(type_counts)
    
    def _generate_process_name(self, business_function: BusinessFunction) -> str:
        """
        Generate a meaningful process name from business function.
        
        Args:
            business_function: Business function to generate name for
            
        Returns:
            Generated process name
        """
        # Get function aliases for better naming
        function_config = self.BUSINESS_FUNCTION_KEYWORDS.get(business_function.name, {})
        aliases = function_config.get('aliases', [])
        
        # Use the first alias if available, otherwise clean up the function name
        if aliases:
            base_name = aliases[0]
        else:
            base_name = business_function.name.replace('_', ' ').title()
        
        # Get department abbreviation
        dept_code = self.DEPARTMENT_CODES.get(business_function.department, 'UNK')
        
        # Create process name
        return f"{dept_code} {base_name}"
    
    def _generate_process_code(self, business_function: BusinessFunction) -> str:
        """
        Generate process code using department codes and sequential numbers.
        
        Args:
            business_function: Business function to generate code for
            
        Returns:
            Generated process code
        """
        dept_code = self.DEPARTMENT_CODES.get(business_function.department, 'UNK')
        
        # Create base code from function name
        function_words = business_function.name.replace('_', ' ').split()
        if len(function_words) >= 2:
            function_code = ''.join(word[:2].upper() for word in function_words[:2])
        else:
            function_code = function_words[0][:4].upper() if function_words else 'PROC'
        
        # Get next sequential number for this department
        base_code = f"{dept_code}-{function_code}"
        counter = self._code_counters[base_code] + 1
        
        return f"{base_code}-{counter:03d}"
    
    def _handle_duplicates(self, process_name: str, process_code: str, department: str) -> Tuple[str, str]:
        """
        Handle duplicate process codes and names with sequential numbering.
        
        Args:
            process_name: Original process name
            process_code: Original process code
            department: Department name
            
        Returns:
            Tuple of (final_name, final_code) with duplicates resolved
        """
        final_name = process_name
        final_code = process_code
        
        # Handle duplicate names
        name_counter = 1
        while final_name in self._existing_names:
            name_counter += 1
            final_name = f"{process_name} {name_counter:02d}"
        
        # Handle duplicate codes
        code_base = process_code.rsplit('-', 1)[0]  # Remove the last number part
        code_counter = 1
        while final_code in self._existing_codes:
            code_counter += 1
            final_code = f"{code_base}-{code_counter:03d}"
        
        # Update counters
        if final_code != process_code:
            self._code_counters[code_base] = code_counter
        
        return final_name, final_code
    
    def _get_or_create_department(self, department_name: str) -> ProcessDepartment:
        """
        Get or create a ProcessDepartment instance.
        
        Args:
            department_name: Name of the department
            
        Returns:
            ProcessDepartment instance
        """
        try:
            return ProcessDepartment.objects.get(name=department_name)
        except ProcessDepartment.DoesNotExist:
            # Create new department
            department = ProcessDepartment(
                name=department_name,
                description=f"Auto-created department for {department_name}",
                order=999  # Put auto-created departments at the end
            )
            department.save()
            return department
    
    def _generate_process_description(self, candidate: ProcessCandidate) -> str:
        """
        Generate a process description from the candidate information.
        
        Args:
            candidate: Process candidate
            
        Returns:
            Generated description
        """
        business_function = candidate.business_function
        doc_count = len(candidate.documents)
        
        # Get document type summary
        type_summary = []
        for doc_type, count in business_function.document_types.items():
            if count > 0:
                type_summary.append(f"{count} {doc_type.replace('_', ' ')}")
        
        type_text = ", ".join(type_summary) if type_summary else "various documents"
        
        description = (
            f"Business process for {business_function.name.replace('_', ' ')} "
            f"in {candidate.department}. "
            f"Contains {doc_count} documents including {type_text}."
        )
        
        if candidate.duplicate_handling_applied:
            description += " (Name/code adjusted to avoid duplicates)"
        
        return description
    
    def _load_existing_processes(self):
        """Load existing process codes and names to avoid duplicates."""
        existing_processes = Process.objects.all()
        
        for process in existing_processes:
            if process.process_code:
                self._existing_codes.add(process.process_code)
                
                # Update code counters
                if '-' in process.process_code:
                    code_parts = process.process_code.split('-')
                    if len(code_parts) >= 3 and code_parts[-1].isdigit():
                        base_code = '-'.join(code_parts[:-1])
                        counter = int(code_parts[-1])
                        self._code_counters[base_code] = max(self._code_counters[base_code], counter)
            
            self._existing_names.add(process.name)
    
    def get_creation_report(self) -> Dict:
        """
        Get comprehensive process creation report.
        
        Returns:
            Dict containing creation statistics and details
        """
        report = self.creation_report.copy()
        
        # Add success rates
        if report['documents_analyzed'] > 0:
            report['process_creation_rate'] = report['processes_created'] / report['business_functions_identified'] if report['business_functions_identified'] > 0 else 0
            report['document_to_process_ratio'] = report['documents_analyzed'] / report['processes_created'] if report['processes_created'] > 0 else 0
        
        return report