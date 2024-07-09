from django.db import models

from it.users.models import CostCenter, Regions, Sections, UserProfile


class File_Type(models.Model):
    name = models.CharField(max_length = 100)
    
    def __str__(self):
        return self.name
    
class FileSubType(models.Model):
    filetype_id = models.ForeignKey(File_Type,on_delete=models.CASCADE,related_name='subtype')
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name 

class SubSubType(models.Model):
    file_subtype_id = models.ForeignKey(FileSubType,on_delete=models.CASCADE,related_name='subsubtype')
    file_type_id = models.ForeignKey(File_Type,on_delete=models.CASCADE,related_name='filetype')
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name  

class Processes(models.Model):
    filename = models.CharField(max_length=200, blank=True, null=True)
    filetype = models.CharField(max_length=100, blank=True, null=True)
    filetype_id = models.ForeignKey(File_Type,on_delete=models.CASCADE,related_name='filetype_process', null=True, blank=True, default=None)
    department = models.CharField(max_length=100, blank=True, null=True)
    filesubtype_id = models.ForeignKey(FileSubType,on_delete=models.CASCADE,related_name='filesubtype_process', null=True, blank=True, default=None)
    sub_category = models.CharField(max_length=100, blank=True, null=True)
    subsubtype_id = models.ForeignKey(SubSubType,on_delete=models.CASCADE, related_name='subsubtype_process', null=True, blank=True, default=None)
    filepath = models.CharField(max_length=400, blank=True, null=True)
    section = models.CharField(max_length=100, blank=True, null=True)
    section_id = models.ForeignKey(Sections,on_delete=models.CASCADE,related_name='section_process', null=True, blank=True, default=None)
    cost_center = models.ForeignKey(CostCenter,on_delete=models.CASCADE,related_name='costcenter_process', null=True, blank=True, default=None)
    region = models.CharField(max_length=100, blank=True, null=True)
    region_id = models.ForeignKey(Regions,on_delete=models.CASCADE,related_name='region_process', null=True, blank=True, default=None)
    archived = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_on = models.DateTimeField(auto_now=True, null=True, blank=True)
    done_by = models.ForeignKey(UserProfile,on_delete=models.CASCADE,related_name='doneby_process', null=True, blank=True, default=None)
    created_at = models.DateField(null=True, blank=True, default=None)
    updated_at = models.DateField(null=True, blank=True, default=None)
    created_by = models.CharField(max_length=50, null=True, blank=True)
    
    def migrate_fields():
        processes = Processes.objects.all()
            
        for process in processes:
            try:
                _section = str(process.section) if process.section else ""
                section_ = Sections.objects.get(section=_section)
                print("section_: ", section_)
                process.section_id = section_
            except Sections.DoesNotExist:
                section_ = None
                
            try:
                cost_center_ = CostCenter.objects.get(code=section_.code) if section_ else None
                process.cost_center = cost_center_ if cost_center_ else None
            except CostCenter.DoesNotExist:
                cost_center_ = None
            
            try:    
                _region = int(process.region) if process.region else 0
                region_ = Regions.objects.get(id=_region)
                if region_:
                    process.region_id = region_
            except Regions.DoesNotExist:
                region_ = None
            except ValueError:
                _region = None
            
            try:
                process.created_on = process.created_at
                process.updated_on = process.updated_at
            except:
                pass
    
            try:
                user_ = UserProfile.objects.get(username=process.created_by)
                process.done_by = user_ if user_ else None
            except UserProfile.DoesNotExist:
                pass
            
            process.save()
    
    @staticmethod    
    def migrate_duplicates():
        try:
            # Get all unique combinations of file, category, and name
            unique_combinations = SubSubType.objects.values('file_subtype_id', 'file_type_id', 'name').distinct()
            for combination in unique_combinations:
                # Find all items matching the current combination
                matching_items = SubSubType.objects.filter(
                    file_subtype_id=combination['file_subtype_id'], file_type_id=combination['file_type_id'], name=combination['name']
                ).order_by('id')
                # If there are duplicates, delete all but the first one
                if matching_items.count() > 1:
                    matching_items.exclude(id=matching_items.first().id).delete()
                    processes = Processes.objects.filter(subsubtype_id=matching_items)
                    for pc in processes:
                        pc.subsubtype = matching_items.first()
                        pc.save()
        except Exception as e:
            print(e)
            
    def migrate_filetypes():
        processes = Processes.objects.all()
        for process in processes:
            try:
                filetype_ = File_Type.objects.get(name=process.filetype) if process.filetype else None
                process.filetype_id = filetype_ if filetype_ else None
            
            except File_Type.DoesNotExist:
                filetype_ = None
            
            try:
                subytype_ = FileSubType.objects.get(filetype_id=filetype_, name=process.department) if process.department else None
                process.filesubtype_id = subytype_ if subytype_ else None
            
            except FileSubType.DoesNotExist:
                subytype_ = None
            
            try:
                subsubtype_ = SubSubType.objects.get(file_subtype_id=subytype_, file_type_id=filetype_, name=process.sub_category) if process.sub_category else None
                process.subsubtype_id = subsubtype_ if subsubtype_ else None
                
            except SubSubType.DoesNotExist:
                pass
            
            process.save()
   
    def __str__(self):
        return self.filename
     
class Processes_Procedures(models.Model):
    filename = models.CharField(max_length=100)
    file_type = models.CharField(max_length=100)
    sub_category_1 = models.CharField(max_length=100)
    sub_category_2 = models.CharField(max_length=100)
    filepath = models.CharField(max_length=400)
    section = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    created_at = models.DateField()
    updated_at = models.DateField()
    created_by = models.CharField(max_length=50)

class Process_maps(models.Model):
    filename = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    sub_category = models.CharField(max_length=100, null=True)
    filepath = models.CharField(max_length=400)
    section = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    created_at = models.DateField()
    updated_at = models.DateField()
    created_by = models.CharField(max_length=50)
   
    def __str__(self):
        return self.filename

class First_Category(models.Model):
    name = models.CharField(max_length=100)
    file_type_id  = models.ForeignKey (File_Type,on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name
    
class Second_Category(models.Model):
    file_type_id  = models.ForeignKey (File_Type,on_delete=models.CASCADE,related_name='category')
    first_cat_id = models.ForeignKey (First_Category,on_delete=models.CASCADE,related_name='category')
    category  = models.ForeignKey (First_Category,on_delete=models.CASCADE,related_name='file')
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
