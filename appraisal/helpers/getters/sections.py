from ..data.approval_stage import SectionStages

class SectionsStagesHandler:
    
    def get_sections_with_urls(self):
        return [
            {"section_name": section.value, "url": section.url()}
            for section in SectionStages
        ]
        
    def get_section_url_section_value(self, section_value: str):
        """
        Return the URL associated with the given section name (string value).
        Example input: "Personal Details"
        """
        for section in SectionStages:
            if section.value.lower() == section_value.lower():
                return section.url()
        return None