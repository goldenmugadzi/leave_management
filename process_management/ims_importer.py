"""
IMS Document Importer Module
Handles importing IMS document register data and creating processes.
Part of Phase 3 of the IMS migration plan.
"""

import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Process, ProcessDepartment, ProcessDocument

logger = logging.getLogger(__name__)


class IMSDocumentImporter:
    """
    Handles importing IMS register from Excel files and populating the database.
    """
    
    def __init__(self):
        self.import_log = []
        self.error_log = []
        self.processes_created = 0
        self.processes_updated = 0
        self.errors_count = 0
    
    def import_from_excel(self, file_path: str) -> Dict:
        """
        Import IMS register from Excel file.
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            Dict with import statistics
        """
        try:
            logger.info(f"Starting IMS import from {file_path}")
            self.import_log.append(f"Starting import from {file_path}")
            
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Parse and validate structure
            validated_data = self.parse_ims_structure(df)
            
            if not validated_data:
                raise ValueError("No valid data found in Excel file")
            
            # Import processes
            with transaction.atomic():
                for row_data in validated_data:
                    try:
                        self.create_process_from_ims(row_data)
                        self.processes_created += 1
                    except Exception as e:
                        self.error_log.append(f"Error creating process {row_data.get('name', 'Unknown')}: {str(e)}")
                        self.errors_count += 1
                        logger.error(f"Error creating process: {e}")
            
            self.import_log.append(f"Import completed. Created: {self.processes_created}, Errors: {self.errors_count}")
            
            return {
                'success': True,
                'processes_created': self.processes_created,
                'processes_updated': self.processes_updated,
                'errors_count': self.errors_count,
                'import_log': self.import_log,
                'error_log': self.error_log
            }
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            self.error_log.append(f"Import failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'import_log': self.import_log,
                'error_log': self.error_log
            }
    
    def parse_ims_structure(self, df: pd.DataFrame) -> List[Dict]:
        """
        Parse IMS worksheet structure and validate data.
        
        Args:
            df: Pandas DataFrame from Excel file
            
        Returns:
            List of validated process data dictionaries
        """
        validated_data = []
        
        # Expected columns (customize based on actual Excel structure)
        required_columns = ['Process Name', 'Department', 'IMS Reference', 'ISO Clause']
        
        # Check if required columns exist
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        for index, row in df.iterrows():
            try:
                # Skip empty rows
                if pd.isna(row['Process Name']) or row['Process Name'].strip() == '':
                    continue
                
                process_data = {
                    'name': str(row['Process Name']).strip(),
                    'department_name': str(row['Department']).strip().upper(),
                    'ims_reference': str(row['IMS Reference']).strip(),
                    'iso_clause': str(row.get('ISO Clause', '')).strip(),
                    'description': str(row.get('Description', '')).strip()
                }
                
                # Validate IMS reference format
                if not self.validate_ims_reference(process_data['ims_reference']):
                    self.error_log.append(f"Invalid IMS reference format: {process_data['ims_reference']}")
                    continue
                
                validated_data.append(process_data)
                
            except Exception as e:
                self.error_log.append(f"Error parsing row {index + 1}: {str(e)}")
                continue
        
        self.import_log.append(f"Parsed {len(validated_data)} valid process records")
        return validated_data
    
    def validate_ims_reference(self, ims_ref: str) -> bool:
        """
        Validate IMS reference format (e.g., ZETDC-HRE MANAGEMENT 01-001).
        
        Args:
            ims_ref: IMS reference string
            
        Returns:
            True if valid format
        """
        if not ims_ref or len(ims_ref) < 10:
            return False
        
        # Basic validation - should contain ZETDC-HRE and a department
        return 'ZETDC-HRE' in ims_ref and any(dept in ims_ref for dept in ['MANAGEMENT', 'TRANSPORT', 'DIS'])
    
    def create_process_from_ims(self, row_data: Dict) -> Process:
        """
        Create process from IMS row data.
        
        Args:
            row_data: Dictionary containing process data
            
        Returns:
            Created Process instance
        """
        # Get or create department
        department, created = ProcessDepartment.objects.get_or_create(
            name=row_data['department_name'],
            defaults={
                'description': f'{row_data["department_name"]} department processes',
                'order': self.get_department_order(row_data['department_name'])
            }
        )
        
        if created:
            self.import_log.append(f"Created department: {department.name}")
        
        # Create or update process
        process, created = Process.objects.get_or_create(
            ims_reference=row_data['ims_reference'],
            defaults={
                'name': row_data['name'],
                'description': row_data['description'],
                'department': department,
                'iso_clause': row_data['iso_clause'],
                'is_active': True
            }
        )
        
        if not created:
            # Update existing process
            process.name = row_data['name']
            process.description = row_data['description']
            process.department = department
            process.iso_clause = row_data['iso_clause']
            process.save()
            self.processes_updated += 1
            self.import_log.append(f"Updated process: {process.name}")
        else:
            self.import_log.append(f"Created process: {process.name}")
        
        return process
    
    def get_department_order(self, department_name: str) -> int:
        """
        Get display order for department.
        
        Args:
            department_name: Name of the department
            
        Returns:
            Integer order value
        """
        order_map = {
            'MANAGEMENT': 1,
            'TRANSPORT': 2,
            'DISTRICTS': 3
        }
        return order_map.get(department_name, 99)
    
    def populate_predefined_ims_processes(self) -> Dict:
        """
        Populate database with predefined IMS processes from the migration plan.
        This is an alternative to Excel import for initial setup.
        
        Returns:
            Dict with import statistics
        """
        try:
            logger.info("Starting predefined IMS processes population")
            self.import_log.append("Starting predefined IMS processes population")
            
            # Ensure departments exist
            departments_data = [
                ('MANAGEMENT', 'Management processes for organizational control', 1),
                ('TRANSPORT', 'Transport and vehicle management processes', 2),
                ('DISTRICTS', 'District operations and customer service processes', 3)
            ]
            
            for name, description, order in departments_data:
                dept, created = ProcessDepartment.objects.get_or_create(
                    name=name,
                    defaults={'description': description, 'order': order}
                )
                if created:
                    self.import_log.append(f"Created department: {name}")
            
            # Get departments
            management_dept = ProcessDepartment.objects.get(name='MANAGEMENT')
            transport_dept = ProcessDepartment.objects.get(name='TRANSPORT')
            districts_dept = ProcessDepartment.objects.get(name='DISTRICTS')
            
            # Define all IMS processes
            processes_data = self.get_predefined_processes_data(management_dept, transport_dept, districts_dept)
            
            # Create processes
            with transaction.atomic():
                for process_data in processes_data:
                    try:
                        process, created = Process.objects.get_or_create(
                            ims_reference=process_data['ims_reference'],
                            defaults=process_data
                        )
                        
                        if created:
                            self.processes_created += 1
                            self.import_log.append(f"Created process: {process.name}")
                        else:
                            # Update existing process
                            for key, value in process_data.items():
                                if key != 'ims_reference':
                                    setattr(process, key, value)
                            process.save()
                            self.processes_updated += 1
                            self.import_log.append(f"Updated process: {process.name}")
                            
                    except Exception as e:
                        self.error_log.append(f"Error creating process {process_data.get('name', 'Unknown')}: {str(e)}")
                        self.errors_count += 1
                        logger.error(f"Error creating process: {e}")
            
            self.import_log.append(f"Population completed. Created: {self.processes_created}, Updated: {self.processes_updated}, Errors: {self.errors_count}")
            
            return {
                'success': True,
                'processes_created': self.processes_created,
                'processes_updated': self.processes_updated,
                'errors_count': self.errors_count,
                'import_log': self.import_log,
                'error_log': self.error_log
            }
            
        except Exception as e:
            logger.error(f"Population failed: {e}")
            self.error_log.append(f"Population failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'import_log': self.import_log,
                'error_log': self.error_log
            }
    
    def get_predefined_processes_data(self, management_dept, transport_dept, districts_dept) -> List[Dict]:
        """
        Get predefined IMS processes data.
        
        Returns:
            List of process data dictionaries
        """
        # MANAGEMENT PROCESSES
        management_processes = [
            {
                'name': 'Internal Auditing',
                'description': 'Internal auditing process for quality management system compliance',
                'department': management_dept,
                'ims_reference': 'ZETDC-HRE MANAGEMENT 01-001',
                'iso_clause': 'ISO 9001:2015 9.2',
            },
            {
                'name': 'Change Management',
                'description': 'Change management process for organizational changes',
                'department': management_dept,
                'ims_reference': 'ZETDC-HRE MANAGEMENT 01-002',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
            {
                'name': 'Management Review',
                'description': 'Management review process for continuous improvement',
                'department': management_dept,
                'ims_reference': 'ZETDC-HRE MANAGEMENT 01-003',
                'iso_clause': 'ISO 9001:2015 9.3',
            },
            {
                'name': 'Document Control (External)',
                'description': 'External document control process',
                'department': management_dept,
                'ims_reference': 'ZETDC-HRE MANAGEMENT 01-004',
                'iso_clause': 'ISO 9001:2015 7.5.3',
            },
            {
                'name': 'Document Control (Internal)',
                'description': 'Internal document control process',
                'department': management_dept,
                'ims_reference': 'ZETDC-HRE MANAGEMENT 01-005',
                'iso_clause': 'ISO 9001:2015 7.5.3',
            },
            {
                'name': 'Legal and Other Requirements',
                'description': 'Legal and regulatory requirements management',
                'department': management_dept,
                'ims_reference': 'ZETDC-HRE MANAGEMENT 01-006',
                'iso_clause': 'ISO 9001:2015 4.2',
            },
            {
                'name': 'Operational Planning',
                'description': 'Operational planning and control process',
                'department': management_dept,
                'ims_reference': 'ZETDC-HRE MANAGEMENT 01-007',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
            {
                'name': 'Communication',
                'description': 'Internal and external communication process',
                'department': management_dept,
                'ims_reference': 'ZETDC-HRE MANAGEMENT 01-008',
                'iso_clause': 'ISO 9001:2015 7.4',
            },
            {
                'name': 'Accident Investigation',
                'description': 'Accident investigation and reporting process',
                'department': management_dept,
                'ims_reference': 'ZETDC-HRE MANAGEMENT 01-001',
                'iso_clause': 'ISO 45001:2018 10.2',
            },
            {
                'name': 'Accident Investigation Review',
                'description': 'Accident investigation review and follow-up process',
                'department': management_dept,
                'ims_reference': 'ZETDC-HRE MANAGEMENT 01-002',
                'iso_clause': 'ISO 45001:2018 10.2',
            },
        ]
        
        # TRANSPORT PROCESSES
        transport_processes = [
            {
                'name': 'Vehicle Licensing',
                'description': 'Vehicle licensing and registration management',
                'department': transport_dept,
                'ims_reference': 'ZETDC-HRE TRANS 01-001',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
            {
                'name': 'Repairs Outsourcing',
                'description': 'Vehicle repair outsourcing management',
                'department': transport_dept,
                'ims_reference': 'ZETDC-HRE TRANS 01-002',
                'iso_clause': 'ISO 9001:2015 8.4',
            },
            {
                'name': 'Registration of New Vehicles',
                'description': 'New vehicle registration process',
                'department': transport_dept,
                'ims_reference': 'ZETDC-HRE TRANS 01-003',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
            {
                'name': 'Road Traffic Accidents',
                'description': 'Road traffic accident management and reporting',
                'department': transport_dept,
                'ims_reference': 'ZETDC-HRE TRANS 01-004',
                'iso_clause': 'ISO 45001:2018 10.2',
            },
            {
                'name': 'Vehicle Hire',
                'description': 'Vehicle hire and rental management',
                'department': transport_dept,
                'ims_reference': 'ZETDC-HRE TRANS 01-005',
                'iso_clause': 'ISO 9001:2015 8.4',
            },
            {
                'name': 'Vehicle Tracking',
                'description': 'Vehicle tracking and monitoring system',
                'department': transport_dept,
                'ims_reference': 'ZETDC-HRE TRANS 01-006',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
            {
                'name': 'Vehicle Maintenance',
                'description': 'Preventive and corrective vehicle maintenance',
                'department': transport_dept,
                'ims_reference': 'ZETDC-HRE TRANS 01-007',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
            {
                'name': 'Vehicle Inspection',
                'description': 'Vehicle safety and compliance inspection',
                'department': transport_dept,
                'ims_reference': 'ZETDC-HRE TRANS 01-008',
                'iso_clause': 'ISO 45001:2018 8.1',
            },
            {
                'name': 'Crane Requests',
                'description': 'Crane service request and deployment',
                'department': transport_dept,
                'ims_reference': 'ZETDC-HRE TRANS 01-009',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
        ]
        
        # DISTRICTS PROCESSES
        districts_processes = [
            {
                'name': 'Electrical Faults',
                'description': 'Electrical fault reporting and resolution',
                'department': districts_dept,
                'ims_reference': 'ZETDC-HRE DIS 01-001',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
            {
                'name': 'New Connections (Standard)',
                'description': 'Standard new electrical connection process',
                'department': districts_dept,
                'ims_reference': 'ZETDC-HRE DIS 01-002',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
            {
                'name': 'Line Maintenance',
                'description': 'Electrical line maintenance and repair',
                'department': districts_dept,
                'ims_reference': 'ZETDC-HRE DIS 01-003',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
            {
                'name': 'Theft Management',
                'description': 'Electrical equipment theft management and prevention',
                'department': districts_dept,
                'ims_reference': 'ZETDC-HRE DIS 01-004',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
            {
                'name': 'Faulty Transformer Replacement',
                'description': 'Transformer fault diagnosis and replacement',
                'department': districts_dept,
                'ims_reference': 'ZETDC-HRE DIS 01-005',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
            {
                'name': 'New Connection (Non-Standard)',
                'description': 'Non-standard new electrical connection process',
                'department': districts_dept,
                'ims_reference': 'ZETDC-HRE DIS 01-006',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
            {
                'name': 'Faulty Meter Replacement',
                'description': 'Electricity meter fault diagnosis and replacement',
                'department': districts_dept,
                'ims_reference': 'ZETDC-HRE DIS 01-007',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
            {
                'name': 'Network Re-enforcement Project',
                'description': 'Electrical network reinforcement and upgrade projects',
                'department': districts_dept,
                'ims_reference': 'ZETDC-HRE DIS 01-008',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
            {
                'name': 'Network Disconnection',
                'description': 'Electrical network disconnection process',
                'department': districts_dept,
                'ims_reference': 'ZETDC-HRE DIS 01-009',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
            {
                'name': 'Relocation Project',
                'description': 'Electrical infrastructure relocation projects',
                'department': districts_dept,
                'ims_reference': 'ZETDC-HRE DIS 01-010',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
            {
                'name': 'Disconnection and Reconnection',
                'description': 'Customer disconnection and reconnection service',
                'department': districts_dept,
                'ims_reference': 'ZETDC-HRE DIS 01-011',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
            {
                'name': 'Energy Loss Banking',
                'description': 'Energy loss calculation and banking process',
                'department': districts_dept,
                'ims_reference': 'ZETDC-HRE DIS 01-012',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
            {
                'name': 'Meter Reading',
                'description': 'Electricity meter reading and data collection',
                'department': districts_dept,
                'ims_reference': 'ZETDC-HRE DIS 01-013',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
            {
                'name': 'Receipt/Batch Cancellation',
                'description': 'Payment receipt and batch cancellation process',
                'department': districts_dept,
                'ims_reference': 'ZETDC-HRE DIS 01-014',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
            {
                'name': 'Receiving Bill Exceptions',
                'description': 'Bill exception handling and resolution',
                'department': districts_dept,
                'ims_reference': 'ZETDC-HRE DIS 01-015',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
            {
                'name': 'Receiving in SAP',
                'description': 'SAP system data receiving and processing',
                'department': districts_dept,
                'ims_reference': 'ZETDC-HRE DIS 01-016',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
            {
                'name': 'Receipt Templates',
                'description': 'Payment receipt template management',
                'department': districts_dept,
                'ims_reference': 'ZETDC-HRE DIS 01-017',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
            {
                'name': 'Customer Complaints Handling',
                'description': 'Customer complaint receipt and resolution process',
                'department': districts_dept,
                'ims_reference': 'ZETDC-HRE DIS 01-018',
                'iso_clause': 'ISO 9001:2015 9.1.2',
            },
            {
                'name': 'Customer Supplied Materials',
                'description': 'Customer supplied materials management',
                'department': districts_dept,
                'ims_reference': 'ZETDC-HRE DIS 01-019',
                'iso_clause': 'ISO 9001:2015 8.5.3',
            },
            {
                'name': 'Clear Tamper Requests',
                'description': 'Meter tamper clearing and resolution process',
                'department': districts_dept,
                'ims_reference': 'ZETDC-HRE DIS 01-020',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
            {
                'name': 'Calculation and Posting of Lost Revenue',
                'description': 'Lost revenue calculation and posting process',
                'department': districts_dept,
                'ims_reference': 'ZETDC-HRE DIS 01-021',
                'iso_clause': 'ISO 9001:2015 8.1',
            },
        ]
        
        # Combine all processes
        return management_processes + transport_processes + districts_processes
