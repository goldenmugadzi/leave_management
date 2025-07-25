from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "The command that creates Historical Lead Schedule."
    
    def add_arguments(self, parser):
        parser.add_argument("--appraisal_pk", type=int, help='The appraisal pk.')
        
    def handle(self, *args, **options):
        import sys
        from loguru import logger
        
        from appraisal.services.kra import AppraisalDependanciesInitialisationService
        from appraisal.repository.kra import AppraisalDepartmentOutputRepository, AppraisalOutPutPerformanceDimensionScoreRepository, YearQuarterRepository
        from appraisal.repository.departmental_workplan import OutPutPerformanceDimensionRepository, DepartmentalOutRepository
        from appraisal.repository.appraisal import AppraisalRepository
        
        appraisal_id = options["appraisal_pk"]
        if appraisal_id is not None and isinstance(appraisal_id, int):
            try:
                appraisal_repo = AppraisalRepository()
                appraisal_obj = appraisal_repo.get_appraisal_by_pk(appraisal_id=appraisal_id)
                
                if appraisal_obj is None:
                    logger.error(f"[AppraisalInitDependency] custom command set_appraisal_dependencies - Setting Appraisal Dependencies for appraisal pk:{appraisal_id} not found")
                    return None
                
                logger.info(f"[AppraisalInitDependency] custom command set_appraisal_dependencies - Setting Appraisal Dependencies for appraisal pk:{appraisal_id} initialized ...")
                
                service_handler = AppraisalDependanciesInitialisationService(
                    appraisal_department_output_repo=AppraisalDepartmentOutputRepository(),
                    appraisal_output_perf_dimension_repo=AppraisalOutPutPerformanceDimensionScoreRepository(),
                    appraisal_repo=AppraisalRepository(),
                    year_quarter_repo=YearQuarterRepository(),
                    performance_dimension_repo=OutPutPerformanceDimensionRepository(),
                    department_output_repo=DepartmentalOutRepository()
                )
                
                appraisal_created_year = appraisal_obj.created_date.year
                
                if service_handler.create_all_dependencies(appraisal_id=appraisal_id, year=appraisal_created_year): 
                    logger.success(f"[AppraisalInitDependency] custom command set_appraisal_dependencies - Setting Appraisal Dependencies for appraisal pk: {appraisal_id} successfully completed")
                else:
                    logger.warning(f"[AppraisalInitDependency] custom command set_appraisal_dependencies - Setting Appraisal Dependencies for appraisal pk:{appraisal_id} not set")
            except Exception as e:
                logger.error(f"[AppraisalInitDependency] custom command set_appraisal_dependencies - Setting Appraisal Dependencies for appraisal pk:{appraisal_id}, failed with error: {e}")
                return None
        else:
            self.stdout.write(
                    self.style.ERROR("Please specify`--appraisal_pk` and should be integer. Example `--appraisal_pk=1`")
                )       
        sys.exit()        
        