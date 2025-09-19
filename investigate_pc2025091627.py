#!/usr/bin/env python
"""
Investigate PC2025091627 approval history
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

from finance.PettyCash.models import Pettycash
from approve.models import Process, Approval

def investigate_pc2025091627():
    """Investigate the specific petty cash case"""
    print("Investigating PC2025091627...")

    # Find the specific petty cash item
    pc = Pettycash.objects.filter(petty_id='PC2025091627').first()
    if pc:
        print(f'Found petty cash: {pc.petty_id}')
        print(f'Process ID: {pc.process.id}')
        print(f'Process workflow: {pc.process.workflow.name}')

        # Get all approvals for this process with more details
        approvals = pc.process.approval_set.all().order_by('approved_at')
        print(f'Total approvals: {approvals.count()}')

        for i, approval in enumerate(approvals, 1):
            print(f'{i}. Approval ID: {approval.id}')
            print(f'   Step: {approval.step.step} - {approval.step.to}')
            print(f'   Approved status: "{approval.approved}"')
            print(f'   User: {approval.user.username} ({approval.user.get_full_name()})')
            print(f'   Timestamp: {approval.approved_at}')
            if approval.comment:
                print(f'   Comment: "{approval.comment}"')
            else:
                print('   No comment')
            print()

        # Check the approval model fields
        print('Approval model field values:')
        for approval in approvals:
            print(f'  ID {approval.id}: approved="{approval.approved}", comment="{approval.comment}"')

        # Check if there are any approvals with 'Rejected' status in the database
        all_rejected = Approval.objects.filter(process=pc.process, approved='Rejected')
        print(f'\nRejected approvals in database: {all_rejected.count()}')
        for rej in all_rejected:
            print(f'  - {rej.id}: {rej.approved} by {rej.user.username}')

        # Check for any approval with 'Rejected' in comment or other patterns
        possible_rejections = Approval.objects.filter(process=pc.process).exclude(approved='Approved')
        print(f'\nNon-approved statuses: {possible_rejections.count()}')
        for appr in possible_rejections:
            print(f'  - {appr.id}: status="{appr.approved}", comment="{appr.comment}"')

    else:
        print('Petty cash PC2025091627 not found')

if __name__ == "__main__":
    investigate_pc2025091627()