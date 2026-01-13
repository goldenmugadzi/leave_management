#!/bin/bash

# Git Branch Cleanup Script
# Remove or comment out the branches you want to KEEP
# Then run this script to delete all uncommented branches

# Branches to delete (remove lines for branches you want to keep)
branches=(
    "+feat-competence-manage-x3KAQ"
    "+feat-competence-table-c3RmR"
    "+feat-handle-invalid-data-N3uWT"
    "+feat-handle-invalid-records-TydPS"
    "+feat-sections-change-request-3EgZw"
    "+fix-delatee-input-shrink-E9MWy"
)

# Get current branch
current_branch=$(git branch --show-current)
echo "Current branch: $current_branch"
echo ""

# Delete branches
deleted=0
skipped=0
failed=0

for branch in "${branches[@]}"; do
    # Skip if it's the current branch
    if [ "$branch" == "$current_branch" ]; then
        echo "⚠️  Skipping current branch: $branch"
        ((skipped++))
        continue
    fi
    
    # Check if branch exists
    if git show-ref --verify --quiet refs/heads/"$branch"; then
        echo "Deleting branch: $branch"
        if git branch -d "$branch" 2>/dev/null; then
            echo "  ✓ Deleted: $branch"
            ((deleted++))
        else
            # Try force delete if regular delete fails
            if git branch -D "$branch" 2>/dev/null; then
                echo "  ✓ Force deleted: $branch"
                ((deleted++))
            else
                echo "  ✗ Failed to delete: $branch"
                ((failed++))
            fi
        fi
    else
        echo "  ⊘ Branch does not exist: $branch"
        ((skipped++))
    fi
done

echo ""
echo "Summary:"
echo "  Deleted: $deleted"
echo "  Skipped: $skipped"
echo "  Failed: $failed"