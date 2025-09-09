"""
Django management command for analyzing Knowledge Center structure.

This command helps understand the current Knowledge Center data structure
before planning the migration to Process Management.

Usage:
    python manage.py analyze_kc_structure [options]

Examples:
    # Basic analysis
    python manage.py analyze_kc_structure
    
    # Detailed analysis with file information
    python manage.py analyze_kc_structure --detailed
    
    # Export analysis to JSON
    python manage.py analyze_kc_structure --export=kc_analysis.json
"""

import json
import os
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.db.models import Count


class Command(BaseCommand):
    help = 'Analyze Knowledge Center structure for migration planning'
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Include detailed file information in analysis'
        )
        
        parser.add_argument(
            '--export',
            type=str,
            help='Export analysis results to JSON file'
        )
        
        parser.add_argument(
            '--app-id',
            type=int,
            default=2,
            help='Knowledge Center application ID to analyze (default: 2 for PROCESS MAPS)'
        )
    
    def handle(self, *args, **options):
        """Execute the analysis command."""
        
        try:
            # Import KC models
            from knowledge_center.models import (
                FolderApplication, KnowledgeCentreFolder, 
                KnowldgeCentreFile
            )
            
            app_id = options['app_id']
            
            # Get the application
            app = FolderApplication.objects.filter(id=app_id).first()
            if not app:
                self.stdout.write(
                    self.style.ERROR(f"Application with ID {app_id} not found")
                )
                return
            
            self.stdout.write(f"Analyzing Knowledge Center Application: {app.name}")
            self.stdout.write("=" * 60)
            
            # Perform analysis
            analysis = self._analyze_application(app, options['detailed'])
            
            # Display results
            self._display_analysis(analysis)
            
            # Export if requested
            if options.get('export'):
                self._export_analysis(analysis, options['export'])
            
        except ImportError:
            self.stdout.write(
                self.style.ERROR("Knowledge Center models not available")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Analysis failed: {str(e)}")
            )
    
    def _analyze_application(self, app, detailed=False):
        """Analyze a Knowledge Center application."""
        
        from knowledge_center.models import KnowledgeCentreFolder, KnowldgeCentreFile
        
        analysis = {
            'application': {
                'id': app.id,
                'name': app.name,
                'created_at': app.created_at.isoformat() if app.created_at else None
            },
            'folder_structure': {},
            'statistics': {
                'total_folders': 0,
                'total_files': 0,
                'total_archived_files': 0,
                'folder_depth_distribution': defaultdict(int),
                'file_type_distribution': defaultdict(int),
                'files_per_folder_distribution': defaultdict(int)
            },
            'potential_processes': []
        }
        
        # Get root folders
        root_folders = KnowledgeCentreFolder.objects.filter(
            folder_application=app,
            parent__isnull=True
        ).order_by('name')
        
        analysis['statistics']['total_folders'] = KnowledgeCentreFolder.objects.filter(
            folder_application=app
        ).count()
        
        analysis['statistics']['total_files'] = KnowldgeCentreFile.objects.filter(
            folder__folder_application=app,
            archived=False
        ).count()
        
        analysis['statistics']['total_archived_files'] = KnowldgeCentreFile.objects.filter(
            folder__folder_application=app,
            archived=True
        ).count()
        
        # Analyze each root folder
        for root_folder in root_folders:
            folder_analysis = self._analyze_folder_recursive(root_folder, 0, detailed)
            analysis['folder_structure'][root_folder.name] = folder_analysis
            
            # Update statistics
            self._update_statistics_from_folder(analysis['statistics'], folder_analysis)
            
            # Identify potential processes
            potential_processes = self._identify_potential_processes(folder_analysis)
            analysis['potential_processes'].extend(potential_processes)
        
        return analysis
    
    def _analyze_folder_recursive(self, folder, depth, detailed=False):
        """Recursively analyze a folder and its contents."""
        
        from knowledge_center.models import KnowldgeCentreFile
        
        folder_info = {
            'id': folder.id,
            'name': folder.name,
            'depth': depth,
            'created_at': folder.created_at.isoformat() if folder.created_at else None,
            'subfolders': {},
            'files': [],
            'statistics': {
                'file_count': 0,
                'archived_file_count': 0,
                'subfolder_count': 0,
                'total_descendants': 0
            }
        }
        
        # Analyze files in this folder
        files = KnowldgeCentreFile.objects.filter(folder=folder)
        
        for file in files:
            file_info = {
                'id': file.id,
                'filename': file.filename,
                'archived': file.archived,
                'created_on': file.created_on.isoformat() if file.created_on else None,
                'region': file.region.region if file.region else None,
                'section': file.section.section if file.section else None
            }
            
            if detailed:
                file_info.update({
                    'file_path': file.file.name if file.file else None,
                    'file_exists': self._check_file_exists(file),
                    'file_size': self._get_file_size(file),
                    'file_extension': self._get_file_extension(file.filename)
                })
            
            folder_info['files'].append(file_info)
            
            if file.archived:
                folder_info['statistics']['archived_file_count'] += 1
            else:
                folder_info['statistics']['file_count'] += 1
        
        # Analyze subfolders
        subfolders = folder.subfolders.all().order_by('name')
        folder_info['statistics']['subfolder_count'] = subfolders.count()
        
        for subfolder in subfolders:
            subfolder_analysis = self._analyze_folder_recursive(subfolder, depth + 1, detailed)
            folder_info['subfolders'][subfolder.name] = subfolder_analysis
            
            # Add descendant counts
            folder_info['statistics']['total_descendants'] += (
                1 + subfolder_analysis['statistics']['total_descendants']
            )
        
        return folder_info
    
    def _check_file_exists(self, file):
        """Check if a file actually exists on disk."""
        try:
            if file.file and hasattr(file.file, 'path'):
                return os.path.exists(file.file.path)
        except:
            pass
        return False
    
    def _get_file_size(self, file):
        """Get file size safely."""
        try:
            if file.file and hasattr(file.file, 'size'):
                return file.file.size
        except:
            pass
        return 0
    
    def _get_file_extension(self, filename):
        """Get file extension."""
        if filename and '.' in filename:
            return filename.split('.')[-1].lower()
        return ''
    
    def _update_statistics_from_folder(self, stats, folder_info):
        """Update global statistics from folder analysis."""
        
        depth = folder_info['depth']
        stats['folder_depth_distribution'][depth] += 1
        
        file_count = folder_info['statistics']['file_count']
        stats['files_per_folder_distribution'][file_count] += 1
        
        # Count file types
        for file_info in folder_info['files']:
            if not file_info['archived']:
                ext = self._get_file_extension(file_info['filename'])
                if ext:
                    stats['file_type_distribution'][ext] += 1
        
        # Recursively update from subfolders
        for subfolder_info in folder_info['subfolders'].values():
            self._update_statistics_from_folder(stats, subfolder_info)
    
    def _identify_potential_processes(self, folder_info, path=""):
        """Identify folders that could represent processes."""
        
        potential_processes = []
        current_path = f"{path}/{folder_info['name']}" if path else folder_info['name']
        
        # Check if this folder could be a process
        file_count = folder_info['statistics']['file_count']
        subfolder_count = folder_info['statistics']['subfolder_count']
        
        # Heuristics for identifying processes:
        # 1. Has files but not too many subfolders (leaf-ish nodes)
        # 2. Has a reasonable number of files (1-20)
        # 3. Folder name suggests it's a process
        
        is_potential_process = (
            file_count > 0 and 
            file_count <= 20 and
            subfolder_count <= 3 and
            self._folder_name_suggests_process(folder_info['name'])
        )
        
        if is_potential_process:
            # Classify files
            file_types = self._classify_files_in_folder(folder_info['files'])
            
            potential_processes.append({
                'folder_id': folder_info['id'],
                'folder_name': folder_info['name'],
                'folder_path': current_path,
                'file_count': file_count,
                'subfolder_count': subfolder_count,
                'file_types': file_types,
                'confidence_score': self._calculate_process_confidence(
                    folder_info, file_types
                )
            })
        
        # Recursively check subfolders
        for subfolder_info in folder_info['subfolders'].values():
            sub_processes = self._identify_potential_processes(subfolder_info, current_path)
            potential_processes.extend(sub_processes)
        
        return potential_processes
    
    def _folder_name_suggests_process(self, name):
        """Check if folder name suggests it contains a process."""
        
        name_lower = name.lower()
        
        # Process-related keywords (updated based on your folder structure)
        process_keywords = [
            'process', 'procedure', 'sop', 'standard', 'operating',
            'workflow', 'guideline', 'manual', 'instruction', 'policy',
            'interactions', 'maps', 'work instructions', 'forms', 'registers',
            'commercial', 'engineering', 'finance', 'human resources',
            'risk management', 'procurement', 'legal services', 'management'
        ]
        
        # Non-process keywords (folders that are likely just organizational)
        non_process_keywords = [
            'archive', 'backup', 'temp', 'temporary', 'misc', 'miscellaneous',
            'other', 'general', 'admin', 'administration'
        ]
        
        # Check for non-process keywords first
        for keyword in non_process_keywords:
            if keyword in name_lower:
                return False
        
        # Check for process keywords
        for keyword in process_keywords:
            if keyword in name_lower:
                return True
        
        # If no specific keywords, consider it potential if name is descriptive
        return len(name) > 3 and not name.isdigit()
    
    def _classify_files_in_folder(self, files):
        """Classify files in a folder by potential document type."""
        
        classification = {
            'process_map': 0,
            'procedure': 0,
            'risk_register': 0,
            'unclassified': 0
        }
        
        # Document type patterns (simplified)
        patterns = {
            'process_map': ['map', 'flow', 'chart', 'diagram'],
            'procedure': ['procedure', 'sop', 'instruction', 'manual', 'guideline'],
            'risk_register': ['risk', 'register', 'assessment', 'matrix']
        }
        
        for file_info in files:
            if file_info['archived']:
                continue
                
            filename_lower = file_info['filename'].lower()
            classified = False
            
            for doc_type, keywords in patterns.items():
                if any(keyword in filename_lower for keyword in keywords):
                    classification[doc_type] += 1
                    classified = True
                    break
            
            if not classified:
                classification['unclassified'] += 1
        
        return classification
    
    def _calculate_process_confidence(self, folder_info, file_types):
        """Calculate confidence score that this folder represents a process."""
        
        score = 0.0
        
        # Base score for having files
        if folder_info['statistics']['file_count'] > 0:
            score += 0.3
        
        # Bonus for having classified documents
        classified_docs = sum(file_types[t] for t in ['process_map', 'procedure', 'risk_register'])
        if classified_docs > 0:
            score += 0.4 * min(classified_docs / 3, 1.0)  # Max bonus for having all 3 types
        
        # Bonus for process-like folder name
        if self._folder_name_suggests_process(folder_info['name']):
            score += 0.2
        
        # Penalty for too many subfolders (suggests organizational folder)
        if folder_info['statistics']['subfolder_count'] > 5:
            score -= 0.2
        
        # Penalty for too many files (suggests dump folder)
        if folder_info['statistics']['file_count'] > 20:
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _display_analysis(self, analysis):
        """Display analysis results."""
        
        app_info = analysis['application']
        stats = analysis['statistics']
        
        self.stdout.write(f"\nApplication: {app_info['name']} (ID: {app_info['id']})")
        
        # Overall statistics
        self.stdout.write(f"\nOverall Statistics:")
        self.stdout.write(f"  Total folders: {stats['total_folders']}")
        self.stdout.write(f"  Total active files: {stats['total_files']}")
        self.stdout.write(f"  Total archived files: {stats['total_archived_files']}")
        
        # Folder depth distribution
        if stats['folder_depth_distribution']:
            self.stdout.write(f"\nFolder Depth Distribution:")
            for depth in sorted(stats['folder_depth_distribution'].keys()):
                count = stats['folder_depth_distribution'][depth]
                self.stdout.write(f"  Depth {depth}: {count} folders")
        
        # File type distribution
        if stats['file_type_distribution']:
            self.stdout.write(f"\nFile Type Distribution (top 10):")
            sorted_types = sorted(
                stats['file_type_distribution'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            for ext, count in sorted_types[:10]:
                self.stdout.write(f"  .{ext}: {count} files")
        
        # Files per folder distribution
        if stats['files_per_folder_distribution']:
            self.stdout.write(f"\nFiles per Folder Distribution:")
            sorted_dist = sorted(stats['files_per_folder_distribution'].items())
            for file_count, folder_count in sorted_dist[:10]:
                self.stdout.write(f"  {file_count} files: {folder_count} folders")
        
        # Potential processes
        potential_processes = analysis['potential_processes']
        if potential_processes:
            self.stdout.write(f"\nPotential Processes Found: {len(potential_processes)}")
            
            # Sort by confidence score
            sorted_processes = sorted(
                potential_processes,
                key=lambda x: x['confidence_score'],
                reverse=True
            )
            
            self.stdout.write(f"\nTop 10 Process Candidates:")
            for i, process in enumerate(sorted_processes[:10], 1):
                self.stdout.write(
                    f"  {i}. {process['folder_name']} "
                    f"(confidence: {process['confidence_score']:.2f}, "
                    f"files: {process['file_count']})"
                )
        
        # Root folder structure
        self.stdout.write(f"\nRoot Folder Structure:")
        for folder_name, folder_info in analysis['folder_structure'].items():
            file_count = folder_info['statistics']['file_count']
            subfolder_count = folder_info['statistics']['subfolder_count']
            total_descendants = folder_info['statistics']['total_descendants']
            
            self.stdout.write(
                f"  {folder_name}: {file_count} files, "
                f"{subfolder_count} subfolders, "
                f"{total_descendants} total descendants"
            )
    
    def _export_analysis(self, analysis, filename):
        """Export analysis to JSON file."""
        
        try:
            # Convert defaultdict to regular dict for JSON serialization
            def convert_defaultdict(obj):
                if isinstance(obj, defaultdict):
                    return dict(obj)
                return obj
            
            # Deep convert defaultdicts
            def deep_convert(obj):
                if isinstance(obj, defaultdict):
                    return {k: deep_convert(v) for k, v in obj.items()}
                elif isinstance(obj, dict):
                    return {k: deep_convert(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [deep_convert(item) for item in obj]
                else:
                    return obj
            
            converted_analysis = deep_convert(analysis)
            
            with open(filename, 'w') as f:
                json.dump(converted_analysis, f, indent=2, default=str)
            
            self.stdout.write(f"\nAnalysis exported to: {filename}")
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"Could not export analysis: {e}")
            )