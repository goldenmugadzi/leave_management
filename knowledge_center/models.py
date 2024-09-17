from django.db import models

from it.users.models import CostCenter, Regions, Sections, UserProfile

class FolderApplication(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class KnowledgeCentreFolder(models.Model):
    name = models.CharField(max_length=255)
    folder_application = models.ForeignKey(FolderApplication, on_delete=models.DO_NOTHING, related_name='folders')
    cover = models.ImageField(upload_to='uploads/knowledge_center/', null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='subfolders', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class KnowldgeCentreFile(models.Model):
    filename = models.CharField(max_length=400)
    archived = models.BooleanField(default=False) 
    section = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, null=True, blank=True, default=None)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.DO_NOTHING, null=True, blank=True, default=None)
    region = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, null=True, blank=True, default=None)
    created_on = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_on = models.DateTimeField(auto_now=True, null=True, blank=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING, null=True, blank=True, default=None)
    folder = models.ForeignKey(KnowledgeCentreFolder, on_delete=models.DO_NOTHING, related_name='files')
    file = models.FileField(upload_to='uploads/knowledge_center/')
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Filetype(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class First_Category(models.Model):
    file_type  = models.ForeignKey (Filetype,on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Secondary_Category(models.Model):
    file  = models.ForeignKey (Filetype,on_delete=models.CASCADE,related_name='category')
    category  = models.ForeignKey (First_Category,on_delete=models.CASCADE,related_name='file')
    name = models.CharField(max_length=100)

    @staticmethod
    def migrate_duplicates():
        # Get all unique combinations of file, category, and name
        unique_combinations = Secondary_Category.objects.values('file', 'category', 'name').distinct()
        for combination in unique_combinations:
            # Find all items matching the current combination
            matching_items = Secondary_Category.objects.filter(
                file=combination['file'], category=combination['category'], name=combination['name']
            ).order_by('id')
            # If there are duplicates, delete all but the first one
            if matching_items.count() > 1:
                matching_items.exclude(id=matching_items.first().id).delete()
                knowledge_centers = KnowledgeCenter.objects.filter(subsubtype__in=matching_items)
                for kc in knowledge_centers:
                    kc.subsubtype = matching_items.first()
                    kc.save()

    def __str__(self):
        return self.name
    
class KnowledgeCenter(models.Model):
    filename = models.CharField(max_length=100)
    file_type = models.CharField(max_length=100)
    file_type_id = models.ForeignKey(Filetype, on_delete=models.CASCADE, null=True, blank=True, default=None)
    sub_category_1 = models.CharField(max_length=100)
    subtype = models.ForeignKey(First_Category, on_delete=models.CASCADE, null=True, blank=True, default=None)
    sub_category_2 = models.CharField(max_length=100)
    subsubtype = models.ForeignKey(Secondary_Category, on_delete=models.CASCADE, null=True, blank=True, default=None)
    filepath = models.CharField(max_length=400)
    archived = models.BooleanField(default=False)
    section = models.CharField(max_length=100, null=True, blank=True, default=None)
    region = models.CharField(max_length=100, null=True, blank=True, default=None)
    section_id = models.ForeignKey(Sections, on_delete=models.CASCADE, null=True, blank=True, default=None)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE, null=True, blank=True, default=None)
    region_id = models.ForeignKey(Regions, on_delete=models.CASCADE, null=True, blank=True, default=None)
    created_at = models.DateField(null=True, blank=True, default=None)
    created_on = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_on = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_at = models.DateField(null=True, blank=True, default=None)
    created_by = models.CharField(max_length=50)
    done_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True, blank=True, default=None)
    
    def migrate_keys_dates():
        k_cs = KnowledgeCenter.objects.all()
        for kc in k_cs:
            try:
                _section = int(kc.section) if kc.section else 0
                section_ = Sections.objects.get(code=_section)
                kc.section_id = section_
            except Sections.DoesNotExist:
                section_ = None
            except ValueError:
                _section = None
            try:
                cost_center_ = CostCenter.objects.get(code=_section) if _section else None
                kc.cost_center = cost_center_ if cost_center_ else None
            except CostCenter.DoesNotExist:
                cost_center_ = None
            
            try:    
                _region = int(kc.region) if kc.region else 0
                region_ = Regions.objects.get(id=_region)
                if region_:
                    kc.region_id = region_
            except Regions.DoesNotExist:
                region_ = None
            except ValueError:
                _region = None
            
            try:
                kc.created_on = kc.created_at
                kc.updated_on = kc.updated_at
            except:
                pass

            kc.save()  
    
    def migrate_users():
        k_cs = KnowledgeCenter.objects.all()
        for kc in k_cs:
            try:
                user_ = UserProfile.objects.get(username=kc.created_by) if kc.created_by else None
                kc.done_by = user_ if user_ else None
                kc.save()
            except UserProfile.DoesNotExist:
                pass 
    
    def migrate_filetypes():
        k_cs = KnowledgeCenter.objects.all()
        for kc in k_cs:
            try:
                filetype_ = Filetype.objects.get(name=kc.file_type) if kc.file_type else None
                kc.file_type_id = filetype_ if filetype_ else None
                kc.save()
            except Filetype.DoesNotExist:
                filetype_ = None
            
            try:
                subytype_ = First_Category.objects.get(file_type=filetype_, name=kc.sub_category_1) if kc.sub_category_1 else None
                kc.subtype = subytype_ if subytype_ else None
                kc.save()
            except First_Category.DoesNotExist:
                subytype_ = None
            
            try:
                subsubtype_ = Secondary_Category.objects.get(file=filetype_, category=subytype_, name=kc.sub_category_2) if kc.sub_category_2 else None
                kc.subsubtype = subsubtype_ if subsubtype_ else None
                kc.save()
            except Secondary_Category.DoesNotExist:
                pass
            
    def __str__(self):
        return self.filename      

class Categories(models.Model):
   file_type = models.CharField(max_length=100)
   cat_1 = models.CharField(max_length=100)
   cat_2 = models.CharField(max_length=100)