import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from it.users.models import Regions, Sections, UserProfile
from knowledge_center.models import (
    FolderApplication,
    KnowledgeCentreFolder,
    KnowldgeCentreFile,
)
from process_management.models import Process, ProcessDepartment, ProcessDocument


REGION_NAME_MAP = {
    "HRE": "Harare Region",
    "WR": "Western Region",
    "SR": "Southern Region",
    "NR": "Northern Region",
}

DEPARTMENT_NAME_MAP = {
    "COMM": "Commercial",
    "COMMERCIAL": "Commercial",
    "TRANS": "Transport",
    "TRANSPORT": "Transport",
    "PROC": "Procurement",
    "PROCU": "Procurement",
    "PROCUREMENT": "Procurement",
    "RISK": "Risk Management",
    "OPS": "Operations",
    "OPERATIONS": "Operations",
    "OPS&MAINT": "Operations",
    "OPSMAINT": "Operations",
    "MAINT": "Operations",
    "MAINTENANCE": "Operations",
    "MANAGEMENT": "Management Processes",
    "MGMT": "Management Processes",
    "ICT": "Information Communication Technology",
    "IT": "Information Communication Technology",
    "HR": "Human Resources",
    "HUMAN": "Human Resources",
    "ADMIN": "Human Resources",
    "FIN": "Finance",
    "FINANCE": "Finance",
    "ENG": "Engineering",
    "ENGINEERING": "Engineering",
    "LEGAL": "Legal Services",
    "PYR": "Payroll",
    "PAY": "Payroll",
    "QA": "Quality Assurance",
    "QUALITY": "Quality Assurance",
}

DOCUMENT_TYPE_PATTERNS = {
    "process_map": [
        r"process\s*map",
        r"process\s*interaction",
        r"workflow",
        r"flow\s?chart",
        r"process\s*flow",
    ],
    "procedure": [
        r"procedure",
        r"standard\s*operating",
        r"work\s*instruction",
        r"sop",
        r"manual",
        r"guide",
    ],
    "risk_register": [
        r"risk\s*register",
        r"risk\s*assessment",
        r"opportunity\s*register",
        r"risk\s*matrix",
    ],
}


@dataclass
class ProcessMetadata:
    """Structured metadata extracted from Knowledge Centre filenames."""

    region_code: Optional[str]
    department_code: Optional[str]
    process_code: Optional[str]
    process_name: str
    department_name: Optional[str]
    region_name: Optional[str]
    search_prefix: str
    slug: str
    tokens: List[str] = field(default_factory=list)


class ProcessMapImporter:
    """
    Helper class for importing process map files from the Knowledge Centre
    into the Process Management application.
    """

    def __init__(self, dry_run: bool = False, logger: Optional[logging.Logger] = None):
        self.dry_run = dry_run
        self.logger = logger or logging.getLogger(__name__)
        self.stats = {
            "processed": 0,
            "created_processes": 0,
            "existing_processes": 0,
            "documents_created": 0,
            "documents_missing": 0,
            "related_documents": 0,
            "skipped": 0,
            "errors": 0,
        }

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def fetch_process_map_files(
        self,
        application_name: str = "PROCESSES AND PROCEDURES",
        application_id: Optional[int] = None,
        folder_name: str = "PROCESS MAPS",
        resume_after_id: Optional[int] = None,
    ):
        """
        Return queryset of Knowledge Centre files located under the specified
        application/folder hierarchy. The queryset is ordered by ascending ID
        to support checkpoint resumption.
        """
        app = None
        if application_id is not None:
            app = FolderApplication.objects.filter(id=application_id).first()

        if not app:
            app = FolderApplication.objects.filter(
                name__iexact=application_name
            ).first()

        if not app:
            alt_name = application_name.replace("AND", "&")
            app = FolderApplication.objects.filter(name__iexact=alt_name).first()

        if not app:
            app = FolderApplication.objects.filter(
                name__icontains=application_name.replace("AND", "").strip()
            ).first()

        if not app:
            app = FolderApplication.objects.filter(name__icontains="process").first()

        if not app:
            raise ValueError(
                f"Folder application '{application_name}' not found in Knowledge Centre"
            )

        base_folders = KnowledgeCentreFolder.objects.filter(
            folder_application=app, name__iexact=folder_name
        )
        if not base_folders.exists():
            # Fall back to partial match
            base_folders = KnowledgeCentreFolder.objects.filter(
                folder_application=app, name__icontains=folder_name
            )

        if not base_folders.exists():
            raise ValueError(
                f"No folders named like '{folder_name}' found in application '{app.name}'"
            )

        folder_ids = set()
        for folder in base_folders:
            folder_ids.update(self._collect_descendant_folder_ids(folder))

        qs = (
            KnowldgeCentreFile.objects.filter(folder_id__in=folder_ids, archived=False)
            .select_related("folder", "section", "region", "created_by")
            .order_by("id")
        )
        if resume_after_id:
            qs = qs.filter(id__gt=resume_after_id)
        return qs

    def import_file(
        self,
        kc_file: KnowldgeCentreFile,
        attach_related: bool = True,
    ) -> Dict[str, str]:
        """
        Import a single Knowledge Centre file as a Process and associated
        ProcessDocument. Returns a dict summarising the action.
        """
        self.stats["processed"] += 1
        try:
            metadata = self._parse_metadata(kc_file.filename or kc_file.name)
            if not metadata:
                self.stats["skipped"] += 1
                return {
                    "status": "skipped",
                    "reason": "unparsed_filename",
                    "message": f"Could not parse metadata from filename '{kc_file.filename}'",
                }

            if self.dry_run:
                self.logger.info(
                    "DRY-RUN: Would import process '%s' in department '%s'",
                    metadata.process_name,
                    metadata.department_name or metadata.department_code or "Unknown",
                )
                return {
                    "status": "dry_run",
                    "process_name": metadata.process_name,
                    "department": metadata.department_name,
                }

            with transaction.atomic():
                department = self._get_or_create_department(metadata)
                process, created = self._get_or_create_process(
                    department, metadata, kc_file
                )

                if created:
                    self.stats["created_processes"] += 1
                else:
                    self.stats["existing_processes"] += 1

                doc_result = self._create_process_document(
                    process,
                    kc_file,
                    metadata,
                    document_type="process_map",
                )

                if doc_result.get("status") == "missing_file":
                    self.stats["documents_missing"] += 1
                else:
                    self.stats["documents_created"] += 1

                related_summary = {}
                if attach_related:
                    related_summary = self._attach_related_documents(
                        process, metadata, kc_file
                    )
                    self.stats["related_documents"] += related_summary.get(
                        "created", 0
                    )

            result = {
                "status": "created",
                "process_id": str(process.id),
                "process_name": process.name,
                "department": department.name,
                "document": doc_result,
                "related": related_summary,
            }
            return result

        except Exception as exc:
            self.stats["errors"] += 1
            self.logger.exception(
                "Failed to import Knowledge Centre file id=%s (%s): %s",
                kc_file.id,
                kc_file.filename,
                exc,
            )
            return {
                "status": "error",
                "reason": "exception",
                "message": str(exc),
            }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _collect_descendant_folder_ids(self, folder: KnowledgeCentreFolder) -> List[int]:
        """Return list of IDs for the folder and all descendants."""
        ids = [folder.id]
        for subfolder in folder.subfolders.all():
            ids.extend(self._collect_descendant_folder_ids(subfolder))
        return ids

    def _parse_metadata(self, filename: str) -> Optional[ProcessMetadata]:
        """
        Parse filename into structured metadata according to the convention:
        ZETDC - <region> - <department> - <process code?> - <name>
        """
        if not filename:
            return None

        stem = Path(filename).stem
        normalized = stem.replace("–", "-").replace("—", "-")
        normalized = re.sub(r"(?<=\D)-(?=\D)", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        tokens = normalized.split(" ")

        if not tokens:
            return None

        if tokens[0].upper() == "ZETDC":
            tokens = tokens[1:]

        if not tokens:
            return None

        region_token = tokens.pop(0).upper()
        region_code = re.sub(r"[^A-Z]", "", region_token)[:3]
        region_name = REGION_NAME_MAP.get(region_code)

        department_code = None
        department_name = None
        if tokens:
            dept_token = tokens.pop(0)
            department_code = re.sub(r"[^A-Z]", "", dept_token.upper())
            department_name = DEPARTMENT_NAME_MAP.get(
                department_code, self._title_case_token(department_code)
            )

        process_code = None
        remaining_tokens: List[str] = []
        for token in tokens:
            if process_code is None and any(ch.isdigit() for ch in token):
                process_code = token
            else:
                remaining_tokens.append(token)

        process_tokens = []
        if process_code:
            process_tokens.append(process_code)
        process_tokens.extend(remaining_tokens)

        process_name = " ".join(process_tokens).strip()
        if not process_name:
            # Fallback to entire normalized string minus prefix
            process_name = " ".join(tokens).strip() or normalized

        search_prefix_parts = ["ZETDC"]
        if region_code:
            search_prefix_parts.append(region_code)
        if department_code:
            search_prefix_parts.append(department_code)
        if process_code:
            search_prefix_parts.append(process_code)
        search_prefix = " ".join(search_prefix_parts)

        slug = "|".join(
            part.lower()
            for part in [region_code or "", department_code or "", process_code or "", process_name.lower()]
        ).strip("|")

        return ProcessMetadata(
            region_code=region_code or None,
            department_code=department_code or None,
            process_code=process_code,
            process_name=process_name,
            department_name=department_name,
            region_name=region_name,
            search_prefix=search_prefix,
            slug=slug,
            tokens=[stem] + tokens,
        )

    def _title_case_token(self, token: Optional[str]) -> Optional[str]:
        if not token:
            return None
        if len(token) <= 3:
            return token.upper()
        return token.replace("_", " ").title()

    def _get_or_create_department(
        self,
        metadata: ProcessMetadata,
    ) -> ProcessDepartment:
        department_name = metadata.department_name or "General Operations"
        department, _ = ProcessDepartment.objects.get_or_create(
            name=department_name,
            defaults={
                "description": f"Imported from Knowledge Centre (code: {metadata.department_code})",
            },
        )
        return department

    def _get_or_create_process(
        self,
        department: ProcessDepartment,
        metadata: ProcessMetadata,
        kc_file: KnowldgeCentreFile,
    ) -> Tuple[Process, bool]:
        process = Process.objects.filter(
            department=department,
            name=metadata.process_name,
        ).first()

        if process:
            updated = False
            if not process.process_code and metadata.process_code:
                process.process_code = metadata.process_code
                updated = True
            if not process.ims_reference and metadata.process_code:
                process.ims_reference = metadata.process_code
                updated = True
            region = self._resolve_region(metadata, kc_file)
            if region and process.region != region:
                process.region = region
                updated = True
            if kc_file.section and process.section != kc_file.section:
                process.section = kc_file.section
                updated = True
            if kc_file.created_by and process.created_by != kc_file.created_by:
                process.created_by = kc_file.created_by
                updated = True
            if updated:
                process.save()
            return process, False

        process = Process(
            name=metadata.process_name,
            department=department,
            process_code=metadata.process_code or "",
            ims_reference=metadata.process_code or "",
            region=self._resolve_region(metadata, kc_file),
            section=kc_file.section if isinstance(kc_file.section, Sections) else None,
            description=f"Imported automatically from Knowledge Centre file ID {kc_file.id}",
            is_active=True,
            created_by=kc_file.created_by if isinstance(kc_file.created_by, UserProfile) else None,
        )
        process.save()
        return process, True

    def _resolve_region(
        self,
        metadata: ProcessMetadata,
        kc_file: KnowldgeCentreFile,
    ) -> Optional[Regions]:
        if kc_file.region:
            return kc_file.region

        if metadata.region_code:
            region = Regions.objects.filter(code__iexact=metadata.region_code).first()
            if region:
                return region
            region_name = REGION_NAME_MAP.get(metadata.region_code)
            if region_name:
                region = Regions.objects.filter(region__iexact=region_name).first()
                if region:
                    return region
        return None

    def _create_process_document(
        self,
        process: Process,
        kc_file: KnowldgeCentreFile,
        metadata: ProcessMetadata,
        document_type: str,
    ) -> Dict[str, str]:
        original_path = kc_file.file.name if kc_file.file else ""
        filename = kc_file.filename or kc_file.name or os.path.basename(original_path)
        sanitized_filename = self._sanitize_filename(filename)

        document_kwargs = {
            "process": process,
            "document_type": document_type,
            "filename": sanitized_filename,
            "original_filename": filename,
            "original_file_path": original_path or "",
            "file_path": original_path or "",
            "file_size": kc_file.file.size if kc_file.file else 0,
            "status": "accessible",
            "version": "1.0",
            "metadata": {
                "source": "knowledge_center",
                "source_file_id": kc_file.id,
                "folder_id": kc_file.folder_id,
                "region_code": metadata.region_code,
                "department_code": metadata.department_code,
                "imported_at": timezone.now().isoformat(),
            },
            "uploaded_by": kc_file.created_by
            if isinstance(kc_file.created_by, UserProfile)
            else None,
        }

        if not kc_file.file or not kc_file.file.name or not default_storage.exists(
            kc_file.file.name
        ):
            document_kwargs["status"] = "missing_file"
            document_kwargs["metadata"]["file_missing"] = True
            doc = ProcessDocument.objects.create(**document_kwargs)
            return {
                "status": "missing_file",
                "document_id": str(doc.id),
                "filename": sanitized_filename,
            }

        with default_storage.open(kc_file.file.name, "rb") as source:
            content = source.read()

        new_file_name = self._build_process_document_path(process, sanitized_filename)
        doc = ProcessDocument(**document_kwargs)
        doc.file.save(new_file_name, ContentFile(content), save=False)
        doc.file_path = doc.file.name
        doc.save()
        return {
            "status": "created",
            "document_id": str(doc.id),
            "filename": sanitized_filename,
        }

    def _build_process_document_path(self, process: Process, filename: str) -> str:
        safe_process = re.sub(r"[^A-Za-z0-9]+", "_", process.name.strip())[:60]
        return f"process_maps/{safe_process}/{filename}"

    def _attach_related_documents(
        self,
        process: Process,
        metadata: ProcessMetadata,
        primary_file: KnowldgeCentreFile,
    ) -> Dict[str, int]:
        search_q = Q(
            filename__istartswith=metadata.search_prefix
        ) | Q(name__istartswith=metadata.search_prefix)
        if metadata.process_code:
            search_q |= Q(filename__icontains=metadata.process_code) | Q(
                name__icontains=metadata.process_code
            )

        related_qs = (
            KnowldgeCentreFile.objects.filter(archived=False)
            .exclude(id=primary_file.id)
            .filter(search_q)
            .select_related("folder", "section", "region", "created_by")
        )

        created = 0
        skipped = 0
        for related in related_qs[:20]:
            if related.id == primary_file.id:
                continue

            rel_metadata = self._parse_metadata(related.filename or related.name)
            if not rel_metadata:
                skipped += 1
                continue
            if metadata.region_code and rel_metadata.region_code != metadata.region_code:
                continue
            if (
                metadata.department_code
                and rel_metadata.department_code != metadata.department_code
            ):
                continue

            doc_type = self._classify_document_type(related.filename or related.name)
            if doc_type == "process_map" or doc_type not in dict(
                ProcessDocument.DOCUMENT_TYPES
            ):
                skipped += 1
                continue

            existing = ProcessDocument.objects.filter(
                process=process,
                document_type=doc_type,
                original_file_path=related.file.name if related.file else "",
            ).exists()
            if existing:
                skipped += 1
                continue

            doc_result = self._create_process_document(process, related, metadata, doc_type)
            if doc_result.get("status") == "created":
                created += 1
            else:
                skipped += 1

        return {"created": created, "skipped": skipped}

    def _classify_document_type(self, filename: str) -> Optional[str]:
        lowercase = filename.lower()
        for doc_type, patterns in DOCUMENT_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, lowercase):
                    return doc_type
        return None

    def _sanitize_filename(self, filename: str) -> str:
        name, ext = os.path.splitext(filename)
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_") or "document"
        ext = re.sub(r"[^A-Za-z0-9.]+", "", ext)
        return f"{safe_name}{ext}"


