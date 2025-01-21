from ..types.kra import KraRolesType, KraRolesActionsType

KRA_ROLES = [
            {
                "role": KraRolesActionsType.read.value,
                "name": KraRolesType.appraisee.value,
                "description": "Appraisee KRA roles",
            },
            {
                "role": KraRolesActionsType.read.value,
                "name": KraRolesType.appraiser.value,
                "description": "Appraiser KRA roles",
            },
            {
                "role": KraRolesActionsType.create.value,
                "name": KraRolesType.hod.value,
                "description": "Section Head KRA roles",
            },
            {
                "role": KraRolesActionsType.read.value,
                "name": KraRolesType.hr.value,
                "description": "HR KRA roles",
            },
        ]

KRA_ACTIVITY_ROLES = [
            {
                "role": KraRolesActionsType.read.value,
                "name": KraRolesType.appraisee.value,
                "description": "Appraisee KRA Activity roles",
            },
            {
                "role": KraRolesActionsType.read.value,
                "name": KraRolesType.appraiser.value,
                "description": "Appraiser KRA Activity roles",
            },
            {
                "role": KraRolesActionsType.create.value,
                "name": KraRolesType.hod.value,
                "description": "Section Head KRA Activity roles",
            },
            {
                "role": KraRolesActionsType.read.value,
                "name": KraRolesType.hr.value,
                "description": "HR KRA Activity roles",
            },
        ]

ACTIVITY_TARGETS_ROLES = [
            {
                "role": KraRolesActionsType.read.value,
                "name": KraRolesType.appraisee.value,
                "description": "Appraisee KRA Activity Targets roles",
            },
            {
                "role": KraRolesActionsType.create.value,
                "name": KraRolesType.appraiser.value,
                "description": "Appraiser KRA Activity Targets roles",
            },
            {
                "role": KraRolesActionsType.read.value,
                "name": KraRolesType.hod.value,
                "description": "Section Head KRA Activity Targets roles",
            },
            {
                "role": KraRolesActionsType.read.value,
                "name": KraRolesType.hr.value,
                "description": "HR KRA Activity Targets roles",
            },
        ]

TARGETS_SCORE_ROLES = [
            {
                "role": KraRolesActionsType.read.value,
                "name": KraRolesType.appraisee.value,
                "description": "Appraisee KRA Targets Score roles",
            },
            {
                "role": KraRolesActionsType.create.value,
                "name": KraRolesType.appraiser.value,
                "description": "Appraiser KRA Targets Score roles",
            },
            {
                "role": KraRolesActionsType.read.value,
                "name": KraRolesType.hod.value,
                "description": "Section Head KRA Targets Score roles",
            },
            {
                "role": KraRolesActionsType.read.value,
                "name": KraRolesType.hr.value,
                "description": "HR KRA Targets Score roles",
            },
        ]
