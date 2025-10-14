from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "The command that creates all Training and Dev Needs related to the given appraisal pk."
    
    def add_arguments(self, parser):
        parser.add_argument("--appraisal_pk", type=int, help='The appraisal pk.')
        
    def handle(self, *args, **options):
        import sys
        from loguru import logger
        
        from appraisal.repository.training import TrainingAndDevelopmentRepository
        from appraisal.services.training import TrainingAndDevelopmentService
        from appraisal.repository.appraisal import AppraisalRepository
        from appraisal.models.helpers import YearQuarter
        
        training_development_repo_handler = TrainingAndDevelopmentRepository()
        training_development_service_handler = TrainingAndDevelopmentService(training_dev_repo=training_development_repo_handler)
        
        appraisal_id = options["appraisal_pk"]
        if appraisal_id is not None and isinstance(appraisal_id, int):
            try:
                appraisal_repo = AppraisalRepository()
                appraisal_obj = appraisal_repo.get_appraisal_by_pk(appraisal_id=appraisal_id)
                
                if appraisal_obj is None:
                    logger.error(f"[TrainingAndDev] custom command set_appraisal_training_dev_needs for appraisal pk:{appraisal_id}, appraisal not found")
                    return None
                
                logger.info(f"[TrainingAndDev] custom command set_appraisal_training_dev_needs for appraisal pk:{appraisal_id} initialized ...")
                
                year_quarter_qr = YearQuarter.objects.filter(year=appraisal_obj.created_date.year)
            
                year_quarters_count = year_quarter_qr.count()
                total_year_quarters_count = 4
                
                if year_quarters_count != total_year_quarters_count:
                    raise ValueError(f"year quarters: {year_quarters_count} is not {total_year_quarters_count}")
                
                training_development_service_handler.create_for_all_quarters(
                            appraisal_object=appraisal_obj,
                            year_quarter_qr=year_quarter_qr
                        )
                
                
            except Exception as e:
                logger.error(f"[TrainingAndDev] custom command set_appraisal_training_dev_needs for appraisal pk:{appraisal_id}, failed with error: {e}")
                return None
        else:
            self.stdout.write(
                    self.style.ERROR("Please specify`--appraisal_pk` and should be integer. Example `--appraisal_pk=1`")
                )       
        sys.exit()        
        