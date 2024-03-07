def group_user_roles(user_roles):
    custom_user_roles = {
        "non_conformity": [],
        "remittance_advice": [],
        "pettycash": [],
        "adjudication": [],
        "tokens": [],
        "tenders": [],
        "ace": [],
        "users": [],
        "rfq": [],
        "dashboards": []
    }
    
    for role in user_roles:
        print(role.application)
        if role.application == "users":
            custom_role = {
                "id": role.id,
                "role": role.role,
                "name": role.name,
                "description": role.description,
                "application": role.application
            }
            
            custom_user_roles["users"].append(custom_role)
        
        if role.application == "non_conformity":
            custom_role = {
                "id": role.id,
                "role": role.role,
                "name": role.name,
                "description": role.description,
                "application": role.application
            }
            
            custom_user_roles["non_conformity"].append(custom_role)
            
        if role.application == "remittance_advice":
            custom_role = {
                "id": role.id,
                "role": role.role,
                "name": role.name,
                "description": role.description,
                "application": role.application
            }
            
            custom_user_roles['remittance_advice'].append(custom_role)
        
        if role.application == "pettycash":
            custom_role = {
                "id": role.id,
                "role": role.role,
                "name": role.name,
                "description": role.description,
                "application": role.application
            }
            
            custom_user_roles['pettycash'].append(custom_role)

        if role.application == "adjudication":
            custom_role = {
                "id": role.id,
                "role": role.role,
                "name": role.name,
                "description": role.description,
                "application": role.application
            }
            
            custom_user_roles['adjudication'].append(custom_role)
            
        if role.application == "tokens":
            custom_role = {
                "id": role.id,
                "role": role.role,
                "name": role.name,
                "description": role.description,
                "application": role.application
            }
            
            custom_user_roles['tokens'].append(custom_role)

        if role.application == "tenders":
            custom_role = {
                "id": role.id,
                "role": role.role,
                "name": role.name,
                "description": role.description,
                "application": role.application
            }
            
            custom_user_roles['tenders'].append(custom_role)

        if role.application == "ace":
            custom_role = {
                "id": role.id,
                "role": role.role,
                "name": role.name,
                "description": role.description,
                "application": role.application
            }
            
            custom_user_roles['ace'].append(custom_role)

        if role.application == "rfq":
            custom_role = {
                "id": role.id,
                "role": role.role,
                "name": role.name,
                "description": role.description,
                "application": role.application
            }
            
            custom_user_roles['rfq'].append(custom_role)

        if role.application == "dashboards":
            custom_role = {
                "id": role.id,
                "role": role.role,
                "name": role.name,
                "description": role.description,
                "application": role.application
            }
            
            custom_user_roles['dashboards'].append(custom_role)

    # print(custom_user_roles)            
    return custom_user_roles


def get_user_groups(user_groups):
    
    network_development = {
        "key": "",
        "name": ""
    }
    
    section = {
        "key": "",
        "name": ""
    }
    
    admin = {
        "key": "",
        "name": ""
    }
    
    # user groups, apps, section, admin_status
    if 'app_network_development' in user_groups:
        
        if 'network_development_technical_clerk' in user_groups:
            network_development['key'] = 'network_development_technical_clerk' 
            network_development['name'] = 'Technical Clerk'
        
        elif 'network_development_snr_eng_planning_design' in user_groups:
            network_development['key'] = 'network_development_snr_eng_planning_design'
            network_development['name'] = 'Senior Eng Planning & Design'
        
        elif 'network_development_planning_technician' in user_groups:
            network_development['key'] = 'network_development_planning_technician'
            network_development['name'] = 'Planning Technician'
        
        elif 'network_development_ptech_do' in user_groups:
            network_development['key'] = 'network_development_ptech_do'
            network_development['name'] = 'PTECH DO'
        
        elif 'network_development_draughts_person' in user_groups:
            network_development['key'] = 'network_development_draughts_person'
            network_development['name'] = 'Draughts Person'
            
        elif 'network_development_nde' in user_groups:
            network_development['key'] = 'network_development_nde'
            network_development['name'] = 'NDE'
            
    if 'superuser' in user_groups:
        admin['key'] = 'admin'
        admin['name'] = 'Admin'
    else:
        admin['key'] = 'normal'
        admin['name'] = 'Normal User'
            
    if 'sec_makoni_depot' in user_groups:
        section['key'] = 'sec_makoni_depot'
        section['name'] = 'Makoni Depot'
    elif 'sec_zengeza_depot' in user_groups:
        section['key'] = 'sec_zengeza_depot'
        section['name'] = 'Zengeza Depot'
    elif 'sec_kuwadzana_depot' in user_groups:
        section['key'] = 'sec_kuwadzana_depot'
        section['name'] = 'Kuwadzana Depot'
    elif 'sec_mabelreign_depot' in user_groups:
        section['key'] = 'sec_mabelreign_depot'
        section['name'] = 'Mabelreign Depot'
    elif 'sec_warrenpark_depot' in user_groups:
        section['key'] = 'sec_warrenpark_depot'
        section['name'] = 'Warren Park Depot'
    elif 'sec_glenview_depot' in user_groups:
        section['key'] = 'sec_glenview_depot'
        section['name'] = 'Glen View Depot'  
    elif 'sec_waterfalls_depot' in user_groups:
        section['key'] = 'sec_waterfalls_depot'
        section['name'] = 'Waterfalls Depot'  
    elif 'sec_southerton_depot' in user_groups:
        section['key'] = 'sec_southerton_depot'
        section['name'] = 'Southerton Depot'
    elif 'sec_cbd_depot' in user_groups:
        section['key'] = 'sec_cbd_depot'
        section['name'] = 'CBD Depot'
    elif 'sec_borrowdale_depot' in user_groups:
        section['key'] = 'sec_borrowdale_depot'
        section['name'] = 'Borrowdale Depot' 
    elif 'sec_mabvuku_depot' in user_groups:
        section['key'] = 'sec_mabvuku_depot'
        section['name'] = 'Mabvuku Depot' 
    elif 'sec_ruwa_depot' in user_groups:
        section['key'] = 'sec_ruwa_depot'
        section['name'] = 'Ruwa Depot' 
    elif 'sec_chitungwiza_district' in user_groups:
        section['key'] = 'sec_chitungwiza_district'
        section['name'] = 'Chitungwiza District' 
    elif 'sec_north_district' in user_groups:
        section['key'] = 'sec_north_district'
        section['name'] = 'North District ' 
    elif 'sec_south_district' in user_groups:
        section['key'] = 'sec_south_district'
        section['name'] = 'South District' 
    elif 'sec_east_district' in user_groups:
        section['key'] = 'sec_east_district'
        section['name'] = 'East District' 
    elif 'sec_gm_office' in user_groups:
        section['key'] = 'sec_gm_office'
        section['name'] = 'GM Office' 
    elif 'sec_finance' in user_groups:
        section['key'] = 'sec_finance'
        section['name'] = 'Finance' 
    elif 'sec_stores' in user_groups:
        section['key'] = 'sec_stores'
        section['name'] = 'Stores' 
    elif 'sec_procurement' in user_groups:
        section['key'] = 'sec_procurement'
        section['name'] = 'Procurement' 
    elif 'sec_humanresource' in user_groups:
        section['key'] = 'sec_humanresource'
        section['name'] = 'Human Resource' 
    elif 'sec_engineering' in user_groups:
        section['key'] = 'sec_engineering'
        section['name'] = 'Engineering' 
    elif 'sec_networkdevelopment' in user_groups:
        section['key'] = 'sec_networkdevelopment'
        section['name'] = 'Network Development' 
    elif 'sec_transport' in user_groups:
        section['key'] = 'sec_transport'
        section['name'] = 'Transport' 
    elif 'sec_operationmantenance' in user_groups:
        section['key'] = 'sec_operationmantenance'
        section['name'] = 'Operations and Maintenance' 
    elif 'sec_commercial' in user_groups:
        section['key'] = 'sec_commercial'
        section['name'] = 'Commercial' 
    elif 'sec_riskmanagement' in user_groups:
        section['key'] = 'sec_riskmanagement'
        section['name'] = 'Risk Management'
    elif 'sec_it' in user_groups:
        section['key'] = 'sec_it'
        section['name'] = 'Information Technology' 
    elif 'sec_transportyard' in user_groups:
        section['key'] = 'sec_transportyard'
        section['name'] = 'Transport Yard' 
        
    return {
        "section": section, 
        "network_development": network_development, 
        "admin": admin
        }

def get_kc_dict(kcs):
    
    file_dict = {
        "legislation": [
            {
                "electricity_acts": [],
                "general_legislation": [],
                "statutory_instruments": []
            }
        ],
        "publication": [],
        "policies": [
            {
                "commercial": [],
                "hr": [],
                "engineering": [],
                "finance": [],
                "ict": [],
                "risk": []
            }
        ],
        "engineering": [
            {
                "1-10": [
                    {
                        "reports": [],
                        "protection": [],
                        "earthing": [],
                        "transformers": [],
                        "fuses": [],
                        "instruments": [],
                        "gaskets": [],
                        "switchgear": [],
                        "regulations": [],
                        "insulating_oils": []
                    }
                ],
                "11-20": [
                    
                    {
                        "clearance_distance": [],
                        "mines": [],
                        "interuptions": [],
                        "water_samples": [],
                        "cables": [],
                        "capital_works": [],
                        "gvt_planning": [],
                        "phase_rotation": [],
                        "insulators": [],
                        "locks": []
                    }
                ],
                "21-30": [
                    
                    {
                        "poles": [],
                        "substations": [],
                        "fire_fighting": [],
                        "defective": [],
                        "services": [],
                        "consumer_equipments": [],
                        "lift_equipments": [],
                        "transport": [],
                        "lighting_protection": [],
                        "insulation": []
                    }
                ],
                "31-45": [
                    
                    {
                        "cable_jointing": [],
                        "capacitors": [],
                        "explosives": [],
                        "standard_stock": [],
                        "cradles": [],
                        "standard_11kv": [],
                        "conductors": [],
                        "road_rail": [],
                        "regulations": [],
                        "power_stations": [],
                        "substation_batteries": [],
                        "safety_rules": [],
                        "high_mast": [],
                        "planning_policy": [],
                        "procurement": [],
                        
                    }
                ],
            }
        ],
        "user_manual": [
            {
                "commercial": [],
                "hr": [],
                "engineering": [],
                "finance": [],
                "ict": [],
                "risk": []
            }
        ],
        "drawings": [
            {
                "drawings": [],
                "standards": [],
                "specifications": []
            }
        ],
        "knowledge_base": [
            {
                "commercial": [
                    {
                        "client_risk": [],
                        "payment_risk": [],
                        "revenue_risk": []
                    }
                ],
                "hr": [],
                "engineering": [
                    {
                        "maintainance": [],
                        "drone_tech": []
                    }
                ],
                "finance": [],
                "ict": [
                    {
                        "user_support": [],
                        "network_support": [],
                        "ict_audit": [],
                        "trending_tect": []
                    }
                ],
                "risk": []
            }
        ]
    }
    
    for kc in kcs:
        if kc.file_type == "LEGISLATION":
            if kc.sub_category_1 == "Electricity Acts":
                file_dict['legislation'][0]['electricity_acts'].append({
                    "id": kc.id,
                    "filename": kc.filename
                })
            if kc.sub_category_1 == "General Legislation":
                file_dict['legislation'][0]['general_legislation'].append({
                    "id": kc.id,
                    "filename": kc.filename
                })
            if kc.sub_category_1 == "Statutory Instruments":
                file_dict['legislation'][0]['statutory_instruments'].append({
                    "id": kc.id,
                    "filename": kc.filename
                })

    return file_dict
    
def get_processes(kcs):
    
    file_dict = {
        "process_map": [
            {
                "hr": [],
                "engineering": [
                    {
                        "planning": [],
                        "ops_maintenance": [],
                        "network_development": [],
                        "drones": [],
                        "project": [],
                        "transport": [],
                    }
                ],
                "finance": [
                    {
                        "client_interactions": [],
                        "procurement_stores": [],
                        "revenue_assurance": []
                    }
                ],
                "ict": [],
                "risk": [],
                "districts": []
            }
        ],
        "processes_risk": [
            {
                "commercial": [
                    {
                        "client_interaction_risk": [],
                        "payment_risks": [],
                        "revenue_risk": [],
                    }
                ],
                "hr": [],
                "engineering": [
                    {
                        "gis": [],
                        "maintenance": [],
                        "projects": []
                    }
                ],
                "finance": [],
                "ict": [],
                "risk": []
            }
        ],
        "procedures_work_instructions": [
            {
                "commercial": [
                    {
                        "client_interaction": [],
                        "payment": [],
                        "revenue": [],
                    }
                ],
                "hr": [],
                "engineering": [
                    {
                        "planning": [],
                        "maintenance": [],
                        "projects": []
                    }
                    
                ],
                "finance": [],
                "ict": [
                    {
                        "planning": []
                    }
                ],
                "risk": []
            }
        ],
        "forms": [
            {
                "commercial": [],
                "hr": [],
                "engineering": [],
                "finance": [],
                "ict": [],
                "risk": []
            }
        ],
        "knowledge_base": [
            {
                "commercial": [],
                "risk": [],
                "engineering": [
                    {
                        "drone": []
                    }
                ],
            }
        ]
    }
    
    for kc in kcs:
        if kc.file_type == "MAPS":
            if kc.sub_category_1 == "HR":
                file_dict['process_map'][0]['hr'].append({
                    "id": kc.id,
                    "filename": kc.filename
                })
            
            if kc.sub_category_1 == "ENGINEERING":
                if kc.sub_category_2 == "PLANNING":
                    file_dict['process_map'][0]['engineering'][0]['planning'].append({
                        "id": kc.id,
                        "filename": kc.filename
                    })
                if kc.sub_category_2 == "OPERATION-MAINTENANCE":
                    file_dict['process_map'][0]['engineering'][0]['ops_maintenance'].append({
                        "id": kc.id,
                        "filename": kc.filename
                    })
                if kc.sub_category_2 == "NETWORK-DEVELOPMENT":
                    file_dict['process_map'][0]['engineering'][0]['network_development'].append({
                        "id": kc.id,
                        "filename": kc.filename
                    })
                if kc.sub_category_2 == "DRONES":
                    file_dict['process_map'][0]['engineering'][0]['drones'].append({
                        "id": kc.id,
                        "filename": kc.filename
                    })
                if kc.sub_category_2 == "PROJECTS":
                    file_dict['process_map'][0]['engineering'][0]['projects'].append({
                        "id": kc.id,
                        "filename": kc.filename
                    })
                if kc.sub_category_2 == "TRANSPORT":
                    file_dict['process_map'][0]['engineering'][0]['transport'].append({
                        "id": kc.id,
                        "filename": kc.filename
                    })
            
            if kc.sub_category_1 == "FINANCE":
                if kc.sub_category_2 == "CLIENT-INTERACTIONS":
                    file_dict['process_map'][0]['finance'][0]['client_interactions'].append({
                        "id": kc.id,
                        "filename": kc.filename
                    })
                if kc.sub_category_2 == "PROCUREMENT-STORES":
                    file_dict['process_map'][0]['finance'][0]['procurement_stores'].append({
                        "id": kc.id,
                        "filename": kc.filename
                    })
                if kc.sub_category_2 == "REVENUE-ASSURANCE":
                    file_dict['process_map'][0]['finance'][0]['revenue_assurance'].append({
                        "id": kc.id,
                        "filename": kc.filename
                    })
            
            if kc.sub_category_1 == "ICT":
                file_dict['process_map'][0]['ict'].append({
                    "id": kc.id,
                    "filename": kc.filename
                })
                
            if kc.sub_category_1 == "RISK":
                file_dict['process_map'][0]['risk'].append({
                    "id": kc.id,
                    "filename": kc.filename
                })
                
            if kc.sub_category_1 == "DISTRICTS":
                file_dict['process_map'][0]['districts'].append({
                    "id": kc.id,
                    "filename": kc.filename
                })

        if kc.file_type == "WORK-INSTRUCTIONS":
            if kc.sub_category_1 == "HR":
                file_dict['procedures_work_instructions'][0]['hr'].append({
                    "id": kc.id,
                    "filename": kc.filename
                })
            
            if kc.sub_category_1 == "ENGINEERING":
                if kc.sub_category_2 == "PLANNING":
                    file_dict['procedures_work_instructions'][0]['engineering'][0]['planning'].append({
                        "id": kc.id,
                        "filename": kc.filename
                    })
                if kc.sub_category_2 == "MAINTENANCE":
                    file_dict['procedures_work_instructions'][0]['engineering'][0]['maintenance'].append({
                        "id": kc.id,
                        "filename": kc.filename
                    })
                if kc.sub_category_2 == "PROJECTS":
                    file_dict['procedures_work_instructions'][0]['engineering'][0]['projects'].append({
                        "id": kc.id,
                        "filename": kc.filename
                    })
            
            if kc.sub_category_1 == "FINANCE":
                file_dict['procedures_work_instructions'][0]['finance'].append({
                    "id": kc.id,
                    "filename": kc.filename
                })
            
            if kc.sub_category_1 == "ICT":
                if kc.sub_category_2 == "PLANNING":
                    file_dict['procedures_work_instructions'][0]['ict'][0]['planning'].append({
                        "id": kc.id,
                        "filename": kc.filename
                    })
                
            if kc.sub_category_1 == "RISK":
                file_dict['procedures_work_instructions'][0]['risk'].append({
                    "id": kc.id,
                    "filename": kc.filename
                })

        if kc.file_type == "FORMS":
            if kc.sub_category_1 == "HR":
                file_dict['forms'][0]['hr'].append({
                    "id": kc.id,
                    "filename": kc.filename
                })
            
            if kc.sub_category_1 == "ENGINEERING":
                file_dict['forms'][0]['engineering'].append({
                    "id": kc.id,
                    "filename": kc.filename
                })
            
            if kc.sub_category_1 == "FINANCE":
                file_dict['forms'][0]['finance'].append({
                    "id": kc.id,
                    "filename": kc.filename
                })
            
            if kc.sub_category_1 == "ICT":
                file_dict['forms'][0]['ict'].append({
                    "id": kc.id,
                    "filename": kc.filename
                })
                
            if kc.sub_category_1 == "RISK":
                file_dict['forms'][0]['risk'].append({
                    "id": kc.id,
                    "filename": kc.filename
                })

        if kc.file_type == "KNOWLEDGE-BASE":
            if kc.sub_category_1 == "ENGINEERING":
                if kc.sub_category_2 == "drone":
                    file_dict['knowledge_base'][0]['engineering'][0]['drone'].append({
                        "id": kc.id,
                        "filename": kc.filename
                    })
            
            if kc.sub_category_1 == "commercial":
                file_dict['knowledge_base'][0]['commercial'].append({
                    "id": kc.id,
                    "filename": kc.filename
                })
                
            if kc.sub_category_1 == "RISK":
                file_dict['knowledge_base'][0]['risk'].append({
                    "id": kc.id,
                    "filename": kc.filename
                })

    return file_dict
        