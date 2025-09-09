"""
IMS (Integrated Management System) Services

This module provides services for managing IMS-specific operations including:
- Process categorization and management
- Document type handling
- Compliance tracking
- IMS reference code generation
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Dict, List, Optional, Tuple
from .models import ProcessDepartment, Process, ProcessDocument


class IMSService:
    """
    Service class for IMS-specific operations
    """
    
    # IMS Department mappings
    IMS_DEPARTMENTS = {
        'MANAGEMENT': {
            'name': 'MANAGEMENT',
            'description': 'Management processes including internal auditing, change management, management review, document control, legal requirements, operational planning, communication, and accident investigation.',
            'order': 1,
            'process_count': 10,
        },
        'TRANSPORT': {
            'name': 'TRANSPORT',
            'description': 'Transport-related processes including vehicle licensing, repairs outsourcing, registration of new vehicles, road traffic accidents, vehicle hire, vehicle tracking, vehicle maintenance, vehicle inspection, and crane requests.',
            'order': 2,
            'process_count': 9,
        },
        'DISTRICTS': {
            'name': 'DISTRICTS',
            'description': 'District operations including electrical faults, new connections, line maintenance, theft management, transformer replacement, meter replacement, network projects, disconnections, billing, customer complaints, and revenue management.',
            'order': 3,
            'process_count': 21,
        },
    }
    
    # IMS Process mappings by department
    IMS_PROCESSES = {
        'MANAGEMENT': [
            {'name': 'Internal Auditing', 'code': '01-001', 'iso_clause': 'ISO 9001:2015 9.2'},
            {'name': 'Change Management', 'code': '01-002', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Management Review', 'code': '01-003', 'iso_clause': 'ISO 9001:2015 9.3'},
            {'name': 'Document Control (External)', 'code': '01-004', 'iso_clause': 'ISO 9001:2015 7.5.3'},
            {'name': 'Document Control (Internal)', 'code': '01-005', 'iso_clause': 'ISO 9001:2015 7.5.2'},
            {'name': 'Legal and Other Requirements', 'code': '01-006', 'iso_clause': 'ISO 9001:2015 4.2'},
            {'name': 'Operational Planning', 'code': '01-007', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Communication', 'code': '01-008', 'iso_clause': 'ISO 9001:2015 7.4'},
            {'name': 'Accident Investigation', 'code': '01-009', 'iso_clause': 'ISO 45001:2018 10.2'},
            {'name': 'Accident Investigation Review', 'code': '01-010', 'iso_clause': 'ISO 45001:2018 10.2'},
        ],
        'TRANSPORT': [
            {'name': 'Vehicle Licensing', 'code': '01-001', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Repairs Outsourcing', 'code': '01-002', 'iso_clause': 'ISO 9001:2015 8.4'},
            {'name': 'Registration of New Vehicles', 'code': '01-003', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Road Traffic Accidents', 'code': '01-004', 'iso_clause': 'ISO 45001:2018 8.1'},
            {'name': 'Vehicle Hire', 'code': '01-005', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Vehicle Tracking', 'code': '01-006', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Vehicle Maintenance', 'code': '01-007', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Vehicle Inspection', 'code': '01-008', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Crane Requests', 'code': '01-009', 'iso_clause': 'ISO 9001:2015 8.1'},
        ],
        'DISTRICTS': [
            {'name': 'Electrical Faults', 'code': '01-001', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'New Connections (Standard)', 'code': '01-002', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Line Maintenance', 'code': '01-003', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Theft Management', 'code': '01-004', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Faulty Transformer Replacement', 'code': '01-005', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'New Connection (Non-Standard)', 'code': '01-006', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Faulty Meter Replacement', 'code': '01-007', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Network Re-enforcement Project', 'code': '01-008', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Network Disconnection', 'code': '01-009', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Relocation Project', 'code': '01-010', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Disconnection and Reconnection', 'code': '01-011', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Energy Loss Banking', 'code': '01-012', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Meter Reading', 'code': '01-013', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Receipt/Batch Cancellation', 'code': '01-014', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Receiving Bill Exceptions', 'code': '01-015', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Receiving in SAP', 'code': '01-016', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Receipt Templates', 'code': '01-017', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Customer Complaints Handling', 'code': '01-018', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Customer Supplied Materials', 'code': '01-019', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Clear Tamper Requests', 'code': '01-020', 'iso_clause': 'ISO 9001:2015 8.1'},
            {'name': 'Calculation and Posting of Lost Revenue', 'code': '01-021', 'iso_clause': 'ISO 9001:2015 8.1'},
        ],
    }
    
    @classmethod
    def get_ims_departments(cls) -> Dict[str, Dict]:
        """Get all IMS departments configuration"""
        return cls.IMS_DEPARTMENTS
    
    @classmethod
    def get_ims_processes(cls) -> Dict[str, List[Dict]]:
        """Get all IMS processes configuration"""
        return cls.IMS_PROCESSES
    
    @classmethod
    def generate_ims_reference(cls, department: str, process_code: str) -> str:
        """Generate IMS reference code"""
        dept_mapping = {
            'MANAGEMENT': 'MANAGEMENT',
            'TRANSPORT': 'TRANS',
            'DISTRICTS': 'DIS',
        }
        
        dept_code = dept_mapping.get(department, department)
        return f"ZETDC-HRE {dept_code} {process_code}"
    
    @classmethod
    def get_process_by_ims_reference(cls, ims_reference: str) -> Optional[Process]:
        """Get process by IMS reference code"""
        try:
            return Process.objects.get(ims_reference=ims_reference)
        except Process.DoesNotExist:
            return None
    
    @classmethod
    def get_processes_by_department(cls, department_name: str) -> List[Process]:
        """Get all processes for a specific department"""
        try:
            department = ProcessDepartment.objects.get(name=department_name)
            return Process.objects.filter(department=department).order_by('ims_reference')
        except ProcessDepartment.DoesNotExist:
            return []
    
    @classmethod
    def get_ims_processes_summary(cls) -> Dict[str, Dict]:
        """Get summary of IMS processes by department"""
        summary = {}
        
        for dept_name in cls.IMS_DEPARTMENTS.keys():
            processes = cls.get_processes_by_department(dept_name)
            summary[dept_name] = {
                'total_processes': processes.count(),
                'expected_processes': cls.IMS_DEPARTMENTS[dept_name]['process_count'],
                'processes': list(processes.values('name', 'ims_reference', 'iso_clause')),
                'completion_percentage': (processes.count() / cls.IMS_DEPARTMENTS[dept_name]['process_count']) * 100,
            }
        
        return summary
    
    @classmethod
    def get_document_compliance_summary(cls, process: Process) -> Dict[str, Dict]:
        """Get document compliance summary for a process"""
        documents = process.documents.filter(is_current=True)
        
        summary = {
            'total_document_types': len(ProcessDocument.DOCUMENT_TYPES),
            'documents_found': documents.count(),
            'completion_percentage': (documents.count() / len(ProcessDocument.DOCUMENT_TYPES)) * 100,
            'document_types': {},
        }
        
        # Check each document type
        for doc_type, doc_name in ProcessDocument.DOCUMENT_TYPES:
            doc = documents.filter(document_type=doc_type).first()
            summary['document_types'][doc_type] = {
                'name': doc_name,
                'exists': doc is not None,
                'status': doc.status if doc else None,
                'compliance_status': doc.compliance_status if doc else None,
                'review_due_date': doc.review_due_date if doc else None,
            }
        
        return summary
    
    @classmethod
    def get_overall_compliance_summary(cls) -> Dict[str, any]:
        """Get overall IMS compliance summary"""
        total_processes = Process.objects.filter(ims_reference__startswith='ZETDC-HRE').count()
        expected_processes = sum(dept['process_count'] for dept in cls.IMS_DEPARTMENTS.values())
        
        # Get document compliance
        total_documents = 0
        compliant_documents = 0
        
        for process in Process.objects.filter(ims_reference__startswith='ZETDC-HRE'):
            doc_summary = cls.get_document_compliance_summary(process)
            total_documents += doc_summary['total_document_types']
            compliant_documents += doc_summary['documents_found']
        
        return {
            'process_completion': {
                'total_processes': total_processes,
                'expected_processes': expected_processes,
                'completion_percentage': (total_processes / expected_processes) * 100 if expected_processes > 0 else 0,
            },
            'document_completion': {
                'total_documents': total_documents,
                'documents_found': compliant_documents,
                'completion_percentage': (compliant_documents / total_documents) * 100 if total_documents > 0 else 0,
            },
            'departments': cls.get_ims_processes_summary(),
        }
    
    @classmethod
    def validate_ims_structure(cls) -> Tuple[bool, List[str]]:
        """Validate that the IMS structure is properly implemented"""
        errors = []
        
        # Check departments
        for dept_name, dept_config in cls.IMS_DEPARTMENTS.items():
            try:
                dept = ProcessDepartment.objects.get(name=dept_name)
                processes = Process.objects.filter(department=dept)
                if processes.count() != dept_config['process_count']:
                    errors.append(f"Department {dept_name}: Expected {dept_config['process_count']} processes, found {processes.count()}")
            except ProcessDepartment.DoesNotExist:
                errors.append(f"Department {dept_name} not found")
        
        # Check total IMS processes
        total_ims_processes = Process.objects.filter(ims_reference__startswith='ZETDC-HRE').count()
        expected_total = sum(dept['process_count'] for dept in cls.IMS_DEPARTMENTS.values())
        
        if total_ims_processes != expected_total:
            errors.append(f"Total IMS processes: Expected {expected_total}, found {total_ims_processes}")
        
        return len(errors) == 0, errors
    
    @classmethod
    def get_process_document_grid(cls, process: Process) -> Dict[str, Dict]:
        """Get the 7-column document grid for a process (IMS view)"""
        documents = process.documents.filter(is_current=True)
        
        grid = {}
        for doc_type, doc_name in ProcessDocument.DOCUMENT_TYPES:
            doc = documents.filter(document_type=doc_type).first()
            grid[doc_type] = {
                'name': doc_name,
                'document': doc,
                'exists': doc is not None,
                'status': doc.status if doc else 'missing',
                'compliance_status': doc.compliance_status if doc else None,
                'review_due_date': doc.review_due_date if doc else None,
                'file_size': doc.file_size if doc else 0,
                'version': doc.version if doc else None,
            }
        
        return grid
