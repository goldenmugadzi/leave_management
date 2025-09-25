from django.core.management.base import BaseCommand
from django.db.models import Sum, Q
from ACE2.models import AssetBudget, Ace2
from ACE2.views import ace_phase

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
            # Compute pending ACEs for this budget (exclude rejected/approved)
            aces = Ace2.objects.filter(budget_id=budget)
            pending_total = 0
            for ace in aces.select_related('process'):
                phase = 'unknown'
                try:
                    # reuse same logic as views to classify status
                    from ACE2.views import ace_phase as _ace_phase  # lazy import
                    phase = _ace_phase(ace)
                except Exception:
                    phase = 'unknown'
                if phase in ('pending', 'in_progress', 'draft'):
                    pending_total += ace.amount or 0

            old_val = budget.to_be_withdrawn or 0
            if old_val != pending_total:
                self.stdout.write(self.style.WARNING(
                    f"Budget {budget.budget_id} ({budget.budget_name}): to_be_withdrawn {old_val} -> {pending_total}"
                ))
                if not options.get('dry_run'):
                    budget.to_be_withdrawn = pending_total
                    budget.save(update_fields=['to_be_withdrawn'])
                    updated += 1
        self.stdout.write(self.style.SUCCESS(f"Recalculation complete. Budgets updated: {updated}"))
