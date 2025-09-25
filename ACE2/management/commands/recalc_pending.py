from django.core.management.base import BaseCommand
from django.db.models import Sum
from ACE2.models import AssetBudget, Ace2, Asset_budget_Virament

class Command(BaseCommand):
    help = "Recalculate AssetBudget.to_be_withdrawn from current pending ACEs and pending outgoing virements"

    def add_arguments(self, parser):
        parser.add_argument('--region', type=int, help='Region ID to limit recalculation')
        parser.add_argument('--period', type=int, help='Budget period/year to limit recalculation')
        parser.add_argument('--dry-run', action='store_true', help='Show changes without saving')

    def handle(self, *args, **options):
        qs = AssetBudget.objects.all()
        if options.get('region'):
            qs = qs.filter(region_id=options['region'])
        if options.get('period'):
            qs = qs.filter(period=options['period'])

        updated = 0
        for budget in qs:
            # Compute pending ACEs for this budget (exclude rejected, exclude fully approved)
            aces = Ace2.objects.filter(budget_id=budget).select_related('process')
            pending_ace_total = 0
            for ace in aces:
                process = getattr(ace, 'process', None)
                if not process:
                    # Drafts count as pending
                    pending_ace_total += ace.amount or 0
                    continue
                approvals = process.approval_set.all()
                if approvals.filter(approved='Rejected').exists():
                    continue  # excluded
                if approvals.exists():
                    last = approvals.last()
                    total_steps = process.workflow.step_set.count() if process.workflow else 0
                    if approvals.count() == total_steps and getattr(last, 'approved', '') == 'Approved':
                        continue  # fully approved, not pending
                    # otherwise, in_progress is pending
                    pending_ace_total += ace.amount or 0
                else:
                    # no approvals yet => pending
                    pending_ace_total += ace.amount or 0

            # Compute pending outgoing virements from this budget as source
            virements = Asset_budget_Virament.objects.filter(from_budget=budget).select_related('process')
            pending_virement_total = 0
            for v in virements:
                process = getattr(v, 'process', None)
                if not process:
                    pending_virement_total += v.amount or 0
                    continue
                approvals = process.approval_set.all()
                if approvals.filter(approved='Rejected').exists():
                    continue
                if approvals.exists():
                    last = approvals.last()
                    total_steps = process.workflow.step_set.count() if process.workflow else 0
                    if approvals.count() == total_steps and getattr(last, 'approved', '') == 'Approved':
                        continue
                    pending_virement_total += v.amount or 0
                else:
                    pending_virement_total += v.amount or 0

            pending_total = (pending_ace_total or 0) + (pending_virement_total or 0)
            old_val = budget.to_be_withdrawn or 0
            # Clamp to non-negative
            pending_total = max(0, pending_total)
            if old_val != pending_total:
                self.stdout.write(self.style.WARNING(
                    f"Budget {budget.budget_id} ({budget.budget_name}): to_be_withdrawn {old_val} -> {pending_total}"
                ))
                if not options.get('dry_run'):
                    budget.to_be_withdrawn = pending_total
                    budget.save(update_fields=['to_be_withdrawn'])
                    updated += 1
        self.stdout.write(self.style.SUCCESS(f"Recalculation complete. Budgets updated: {updated}"))
