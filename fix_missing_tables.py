#!/usr/bin/env python
"""
Fix missing tables in fault_locator app
"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
sys.path.append('.')
django.setup()

from django.db import connection

def create_missing_tables():
    """Create missing tables manually"""
    cursor = connection.cursor()
    
    # Create FaultLocatorRole table
    role_table_sql = """
    CREATE TABLE IF NOT EXISTS `fault_locator_faultlocatorrole` (
        `id` bigint NOT NULL AUTO_INCREMENT,
        `role` varchar(20) NOT NULL,
        `assigned_at` datetime(6) NOT NULL,
        `is_active` tinyint(1) NOT NULL DEFAULT 1,
        `assigned_by_id` bigint DEFAULT NULL,
        `depot_id` int DEFAULT NULL,
        `user_id` bigint NOT NULL,
        PRIMARY KEY (`id`),
        UNIQUE KEY `fault_locator_faultlocato_user_id_role_depot_id_15a5e2c7_uniq` (`user_id`,`role`,`depot_id`),
        KEY `fault_locator_faultl_assigned_by_id_3e2b0ed1_fk_users_use` (`assigned_by_id`),
        KEY `fault_locator_faultl_depot_id_4c8f9e3a_fk_users_dep` (`depot_id`),
        CONSTRAINT `fault_locator_faultl_assigned_by_id_3e2b0ed1_fk_users_use` FOREIGN KEY (`assigned_by_id`) REFERENCES `users_userprofile` (`id`),
        CONSTRAINT `fault_locator_faultl_depot_id_4c8f9e3a_fk_users_dep` FOREIGN KEY (`depot_id`) REFERENCES `users_depots` (`id`),
        CONSTRAINT `fault_locator_faultl_user_id_0f2a7b1d_fk_users_use` FOREIGN KEY (`user_id`) REFERENCES `users_userprofile` (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
    """
    
    # Create TeamDeployment table
    deployment_table_sql = """
    CREATE TABLE IF NOT EXISTS `fault_locator_teamdeployment` (
        `id` bigint NOT NULL AUTO_INCREMENT,
        `deployed_at` datetime(6) NOT NULL,
        `recalled_at` datetime(6) DEFAULT NULL,
        `deployment_notes` longtext NOT NULL,
        `recall_notes` longtext NOT NULL,
        `deployed_by_id` bigint NOT NULL,
        `depot_id` int NOT NULL,
        `recalled_by_id` bigint DEFAULT NULL,
        `team_id` bigint NOT NULL,
        PRIMARY KEY (`id`),
        UNIQUE KEY `fault_locator_teamdeplo_team_id_depot_id_deploye_27c8f9c1_uniq` (`team_id`,`depot_id`,`deployed_at`),
        KEY `fault_locator_teamd_deployed_by_id_8b2f1a7c_fk_users_use` (`deployed_by_id`),
        KEY `fault_locator_teamd_depot_id_c1f5e4d2_fk_users_dep` (`depot_id`),
        KEY `fault_locator_teamd_recalled_by_id_9a3b6e1f_fk_users_use` (`recalled_by_id`),
        CONSTRAINT `fault_locator_teamd_deployed_by_id_8b2f1a7c_fk_users_use` FOREIGN KEY (`deployed_by_id`) REFERENCES `users_userprofile` (`id`),
        CONSTRAINT `fault_locator_teamd_depot_id_c1f5e4d2_fk_users_dep` FOREIGN KEY (`depot_id`) REFERENCES `users_depots` (`id`),
        CONSTRAINT `fault_locator_teamd_recalled_by_id_9a3b6e1f_fk_users_use` FOREIGN KEY (`recalled_by_id`) REFERENCES `users_userprofile` (`id`),
        CONSTRAINT `fault_locator_teamd_team_id_5d8a2c9e_fk_fault_loc` FOREIGN KEY (`team_id`) REFERENCES `fault_locator_faultlocatorteam` (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
    """
    
    try:
        print("Creating FaultLocatorRole table...")
        cursor.execute(role_table_sql)
        print("✓ FaultLocatorRole table created successfully")
        
        print("Creating TeamDeployment table...")
        cursor.execute(deployment_table_sql)
        print("✓ TeamDeployment table created successfully")
        
        print("All missing tables created successfully!")
        
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = create_missing_tables()
    if success:
        print("\nDatabase tables fixed successfully!")
        print("You can now run: python manage.py runserver")
    else:
        print("\nFailed to fix database tables.")
