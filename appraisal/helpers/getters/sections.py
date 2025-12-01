from ..data.approval_stage import SectionStages

class SectionsStagesHandler:
    
    def get_sections_with_urls(self):
        return [
            {"section_name": section.value, "url": section.url()}
            for section in SectionStages
        ]