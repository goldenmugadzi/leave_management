from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from it.users.models import UserProfile, Application, Roles
from fault_locator.models import FaultLocatorRole, FaultLocatorTeam
from fault_locator.central_roles import FaultLocatorRoleManager, migrate_legacy_roles

import csv
import sys


ANOMALY_DEFINITIONS = {
    'MULTIPLE_CENTRAL_ROLES': 'User has more than one central fault locator role (only first is used).',
    'LEGACY_AND_CENTRAL': 'User has both legacy and central role assignments.',
    'LEGACY_ACTIVE': 'User still relies on legacy FaultLocatorRole (should migrate).',
    'DEPOT_FOREPERSON_WITHOUT_DEPOT': 'Depot foreperson role but user.depot is not set.',
    'TEAM_LEADER_NO_ROLE': 'Team leader without explicit central role.',
    'TEAM_MEMBER_NO_ROLE': 'Team member without explicit central role.',
    'INFERRED_ONLY': 'Role inferred from designation / structure but no explicit central role.',
}


def compute_effective_role(user_profile, central_roles, legacy_roles, team_leader_team, member_teams, designation_role):
    """Determine effective role following precedence rules."""
    if central_roles:
        return central_roles[0].role
    if legacy_roles:
        return legacy_roles[0].role
    if team_leader_team:
        return 'team_leader'
    if member_teams:
        return 'team_member'
    if designation_role:
        return designation_role
    return None


def infer_designation_role(user_profile):
    """Replicates designation inference similar to legacy helpers."""
    try:
        if not user_profile.designation:
            return None
        desc = (user_profile.designation.description or '').lower()
        if 'senior' in desc and ('foreman' in desc or 'foreperson' in desc):
            return 'senior_foreman'
        if ('foreman' in desc or 'foreperson' in desc) and 'senior' not in desc:
            return 'depot_foreperson'
    except Exception:
        return None
    return None


class Command(BaseCommand):
    help = 'Audit Fault Locator user roles (central, legacy, inferred) and detect anomalies.'

    def add_arguments(self, parser):
        parser.add_argument('--csv', dest='csv_path', help='Optional path to write CSV output.')
        parser.add_argument('--json', action='store_true', help='Output JSON instead of table.')
        parser.add_argument('--migrate-legacy', action='store_true', help='Attempt migration of active legacy roles first.')
        parser.add_argument('--limit', type=int, help='Limit number of users processed (for debugging).')

    def handle(self, *args, **options):
        start = timezone.now()
        migrate = options.get('migrate_legacy')
        csv_path = options.get('csv_path')
        json_out = options.get('json')
        limit = options.get('limit')

        # Safely handle missing tables
        try:
            application = Application.objects.filter(name=FaultLocatorRoleManager.APPLICATION_NAME).first()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Database not ready (missing tables): {e}"))
            self.stdout.write(self.style.WARNING("Run 'python manage.py migrate' or ensure custom app migrations are applied."))
            application = None

        if migrate:
            migrated, errors = migrate_legacy_roles()
            self.stdout.write(self.style.WARNING(f"Legacy migration attempted: migrated={migrated}, errors={len(errors)}"))
            for err in errors[:5]:
                self.stdout.write(self.style.ERROR(f"  MIGRATION_ERROR: {err}"))

        qs = UserProfile.objects.all().order_by('id')
        if limit:
            qs = qs[:limit]

        rows = []
        anomaly_counts = {k: 0 for k in ANOMALY_DEFINITIONS.keys()}

        for user in qs:
            central_roles = []
            if application:
                try:
                    central_roles = list(user.roles.filter(app_id=application))
                except Exception:
                    # Handle missing roles table gracefully
                    pass

            try:
                legacy_roles = list(FaultLocatorRole.objects.filter(user=user, is_active=True))
            except Exception:
                legacy_roles = []
            
            try:
                team_leader_team = FaultLocatorTeam.objects.filter(team_leader=user).first()
            except Exception:
                team_leader_team = None
            
            try:
                member_teams = list(user.fault_locator_teams.all())
            except Exception:
                member_teams = []
            designation_role = infer_designation_role(user)

            effective_role = compute_effective_role(
                user, central_roles, legacy_roles, team_leader_team, member_teams, designation_role
            )

            anomalies = []
            if len(central_roles) > 1:
                anomalies.append('MULTIPLE_CENTRAL_ROLES')
            if central_roles and legacy_roles:
                anomalies.append('LEGACY_AND_CENTRAL')
            if legacy_roles and not central_roles:
                anomalies.append('LEGACY_ACTIVE')
            if (effective_role == 'depot_foreperson' or any(r.role == 'depot_foreperson' for r in central_roles + legacy_roles)) and not user.depot:
                anomalies.append('DEPOT_FOREPERSON_WITHOUT_DEPOT')
            if team_leader_team and not central_roles and not legacy_roles:
                anomalies.append('TEAM_LEADER_NO_ROLE')
            if member_teams and not team_leader_team and not central_roles and not legacy_roles:
                anomalies.append('TEAM_MEMBER_NO_ROLE')
            if designation_role and not central_roles and not legacy_roles:
                anomalies.append('INFERRED_ONLY')

            for a in anomalies:
                anomaly_counts[a] += 1

            rows.append({
                'user_id': user.id,
                'username': user.username,
                'name': f"{user.last_name} {user.first_name}".strip(),
                'depot': getattr(user.depot, 'code', None) if user.depot else None,
                'central_role': central_roles[0].role if central_roles else None,
                'central_roles_count': len(central_roles),
                'legacy_roles': ','.join({lr.role for lr in legacy_roles}) or None,
                'team_leader': bool(team_leader_team),
                'teams_member_count': len(member_teams),
                'designation_role': designation_role,
                'effective_role': effective_role,
                'anomalies': '|'.join(anomalies) if anomalies else ''
            })

        # Output
        if json_out:
            import json
            payload = {
                'summary': {
                    'total_users': len(rows),
                    'anomalies': anomaly_counts,
                    'duration_ms': (timezone.now() - start).total_seconds() * 1000,
                },
                'rows': rows,
            }
            self.stdout.write(json.dumps(payload, indent=2, default=str))
        else:
            # Tabular output (truncate for readability)
            header = [
                'user_id', 'username', 'central_role', 'legacy_roles', 'team_leader',
                'teams_member_count', 'designation_role', 'effective_role', 'anomalies'
            ]
            self.stdout.write(' | '.join(header))
            self.stdout.write('-' * 120)
            for r in rows[:500]:  # safety cap display
                line = [
                    str(r['user_id']), r['username'], r['central_role'] or '-', r['legacy_roles'] or '-',
                    'Y' if r['team_leader'] else '-', str(r['teams_member_count']),
                    r['designation_role'] or '-', r['effective_role'] or '-', r['anomalies'] or '-'
                ]
                self.stdout.write(' | '.join(line))
            if len(rows) > 500:
                self.stdout.write(self.style.WARNING(f"(Truncated display to 500 of {len(rows)} users)"))

            self.stdout.write('\nAnomaly Counts:')
            for key, count in anomaly_counts.items():
                if count:
                    self.stdout.write(f"  {key}: {count}")

        if csv_path:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
                writer.writeheader()
                for r in rows:
                    writer.writerow(r)
            self.stdout.write(self.style.SUCCESS(f"CSV written to {csv_path}"))

        self.stdout.write(self.style.SUCCESS('Audit complete'))
