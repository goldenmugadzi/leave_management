import logging
from datetime import datetime
from typing import Optional

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from process_management.models import MigrationCheckpoint
from process_management.process_map_importer import ProcessMapImporter


class Command(BaseCommand):
    help = (
        "Import processes into the Process Management module using Knowledge Centre "
        "files located under the 'Process Maps' hierarchy."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulate the import without writing any database or file changes.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit the number of Knowledge Centre files to process.",
        )
        parser.add_argument(
            "--resume",
            type=str,
            help="Resume from a previous migration checkpoint by providing its migration_id.",
        )
        parser.add_argument(
            "--application",
            type=str,
            default="PROCESSES AND PROCEDURES",
            help="Knowledge Centre application name (default: 'PROCESSES AND PROCEDURES').",
        )
        parser.add_argument(
            "--application-id",
            type=int,
            default=None,
            help="Knowledge Centre application ID (overrides --application when provided).",
        )
        parser.add_argument(
            "--folder",
            type=str,
            default="PROCESS MAPS",
            help="Root folder name that holds process maps (default: 'PROCESS MAPS').",
        )
        parser.add_argument(
            "--no-related",
            action="store_true",
            help="Skip searching for and attaching related documents (procedures, risk registers, etc.).",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options["limit"]
        resume_id = options["resume"]
        application_name = options["application"]
        application_id = options["application_id"]
        folder_name = options["folder"]
        attach_related = not options["no_related"]

        if resume_id and dry_run:
            raise CommandError("Cannot combine --resume with --dry-run.")

        logger = self._configure_logger()
        importer = ProcessMapImporter(dry_run=dry_run, logger=logger)

        checkpoint = self._initialise_checkpoint(
            resume_id, dry_run, application_name, application_id, folder_name, limit
        )

        resume_after_id: Optional[int] = (
            int(checkpoint.last_processed_item_id)
            if checkpoint.last_processed_item_id
            else None
        )

        try:
            files_qs = importer.fetch_process_map_files(
                application_name=application_name,
                application_id=application_id,
                folder_name=folder_name,
                resume_after_id=resume_after_id,
            )
        except ValueError as exc:
            checkpoint.mark_failed(str(exc))
            raise CommandError(str(exc))

        total_remaining = files_qs.count()
        if limit:
            total_remaining = min(total_remaining, limit)

        if not resume_id:
            checkpoint.total_items = total_remaining
            checkpoint.save(update_fields=["total_items"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Starting process map import "
                f"(dry-run={dry_run}, attach_related={attach_related}, total={total_remaining})"
            )
        )

        processed = 0

        for kc_file in files_qs.iterator():
            if limit and processed >= limit:
                break

            result = importer.import_file(kc_file, attach_related=attach_related)
            processed += 1
            self._update_checkpoint_after_file(checkpoint, kc_file.id, result)

            if result["status"] == "error":
                self.stdout.write(
                    self.style.ERROR(
                        f"[{kc_file.id}] Failed: {result.get('message', 'Unknown error')}"
                    )
                )
            elif result["status"] == "skipped":
                self.stdout.write(
                    f"[{kc_file.id}] Skipped: {result.get('message', result.get('reason', 'unparsed'))}"
                )
            elif result["status"] == "created":
                document_info = result.get("document", {})
                doc_status = document_info.get("status")
                doc_id = document_info.get("document_id")
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[{kc_file.id}] Imported process '{result['process_name']}' "
                        f"(document status: {doc_status}{', id=' + doc_id if doc_id else ''})"
                    )
                )
            elif result["status"] == "dry_run":
                self.stdout.write(
                    f"[{kc_file.id}] DRY-RUN would import '{result['process_name']}'"
                )

        self._finalise_checkpoint(checkpoint, importer)
        self._display_summary(importer, processed, total_remaining, dry_run)

    # ------------------------------------------------------------------
    # Checkpoint handling
    # ------------------------------------------------------------------

    def _initialise_checkpoint(
        self,
        resume_id: Optional[str],
        dry_run: bool,
        application_name: str,
        application_id: Optional[int],
        folder_name: str,
        limit: Optional[int],
    ) -> MigrationCheckpoint:
        if resume_id:
            checkpoint = MigrationCheckpoint.objects.filter(
                migration_id=resume_id
            ).first()
            if not checkpoint:
                raise CommandError(
                    f"Migration checkpoint '{resume_id}' not found. "
                    "Use --resume with a valid migration_id."
                )
            if not checkpoint.can_resume():
                raise CommandError(
                    f"Migration checkpoint '{resume_id}' cannot be resumed "
                    f"(status: {checkpoint.status})."
                )
            checkpoint.status = "in_progress"
            checkpoint.last_updated = timezone.now()
            checkpoint.save(update_fields=["status", "last_updated"])
            return checkpoint

        migration_id = f"process_map_import_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        checkpoint = MigrationCheckpoint.objects.create(
            migration_id=migration_id,
            status="started" if not dry_run else "in_progress",
            total_items=0,
            processed_items=0,
            successful_items=0,
            failed_items=0,
            skipped_items=0,
            batch_size=limit or 50,
            migration_config={
                "dry_run": dry_run,
                "application": application_name,
                "application_id": application_id,
                "folder": folder_name,
                "limit": limit,
            },
        )
        self.stdout.write(
            f"Created migration checkpoint '{checkpoint.migration_id}' (status={checkpoint.status})"
        )
        return checkpoint

    def _update_checkpoint_after_file(
        self, checkpoint: MigrationCheckpoint, file_id: int, result: dict
    ):
        checkpoint.processed_items += 1
        checkpoint.last_processed_item_id = str(file_id)
        checkpoint.last_updated = timezone.now()

        status = result.get("status")
        if status == "created":
            checkpoint.successful_items += 1
        elif status == "error":
            checkpoint.failed_items += 1
        else:
            checkpoint.skipped_items += 1

        checkpoint.save(
            update_fields=[
                "processed_items",
                "successful_items",
                "failed_items",
                "skipped_items",
                "last_processed_item_id",
                "last_updated",
            ]
        )

    def _finalise_checkpoint(
        self, checkpoint: MigrationCheckpoint, importer: ProcessMapImporter
    ):
        if importer.stats["errors"] == 0:
            checkpoint.mark_completed()
        else:
            checkpoint.mark_failed(
                f"{importer.stats['errors']} errors occurred during import."
            )

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------

    def _configure_logger(self) -> logging.Logger:
        logger = logging.getLogger("process_management.import_process_maps")
        if not logger.handlers:
            handler = logging.StreamHandler(self.stdout)
            handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _display_summary(
        self,
        importer: ProcessMapImporter,
        processed: int,
        total_expected: int,
        dry_run: bool,
    ):
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Import Summary"))
        self.stdout.write(f"  Dry-run: {dry_run}")
        self.stdout.write(f"  Processed files: {processed} / {total_expected}")
        self.stdout.write(f"  Processes created: {importer.stats['created_processes']}")
        self.stdout.write(f"  Existing processes updated: {importer.stats['existing_processes']}")
        self.stdout.write(f"  Documents created: {importer.stats['documents_created']}")
        self.stdout.write(f"  Documents missing: {importer.stats['documents_missing']}")
        self.stdout.write(f"  Related documents attached: {importer.stats['related_documents']}")
        self.stdout.write(f"  Skipped files: {importer.stats['skipped']}")
        self.stdout.write(f"  Errors: {importer.stats['errors']}")


