from django.shortcuts import render
from django.views import View



def view_competence(request):
        
        url_path = request.path.split("/")
        url_path = request.path.split("/")
        return render(request, 'competence_building/competence.html', {
                      "url_path": url_path})

def view_charts(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/charts.html', {
                      "url_path": url_path})

def view_headoffice(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/headoffice.html', {
                      "url_path": url_path})

def view_regionaloffice(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/regionaloffice.html', {
                      "url_path": url_path})

def view_jobdescription(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/jobdescription.html', {
                      "url_path": url_path})

def view_IT(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/IT.html', {
                      "url_path": url_path})

def view_finance(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/finance.html', {
                      "url_path": url_path})
   
def view_humanresource(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/humanresource.html', {
                      "url_path": url_path})

def view_losscontrol(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/losscontrol.html', {
                      "url_path": url_path})

def view_engineering(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/engineering.html', {
                      "url_path": url_path})

def view_commercial(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/commercial.html', {
                      "url_path": url_path})

def view_district(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/district.html', {
                      "url_path": url_path})

def view_sales(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/sales.html', {
                      "url_path": url_path})

def view_networkdevelopment(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/networkdevelopment.html', {
                      "url_path": url_path})

def view_operations(request):
        
        url_path = request.path.split("/")
        return render(request, 'competence_building/operations.html', {
                      "url_path": url_path})
        return render(request, 'competence_building/operations.html')

def view_suplies(request):
        return render(request, 'competence_building/suplies.html')

def view_southdistrict(request):
        return render(request, 'competence_building/southdistrict.html')

def view_southglenview(request):
        return render(request, 'competence_building/southglenview.html')

def view_southwaterfalls(request):
        return render(request, 'competence_building/southwaterfalls.html')

def view_southsales(request):
        return render(request, 'competence_building/southsales.html')

def view_northdistrict(request):
        return render(request, 'competence_building/northditrict.html')

def view_northkuwadzana(request):
        return render(request, 'competence_building/northkuwadzana.html')

def view_northmabelreign(request):
        return render(request, 'competence_building/northmabelreign.html')

def view_northwarrenpark(request):
        return render(request, 'competence_building/northwarrenpark.html')

def view_northsales(request):
        return render(request, 'competence_building/northsales.html')

def view_eastdistrict(request):
        return render(request, 'competence_building/eastdistrict.html')

def view_eastcbd(request):
        return render(request, 'competence_building/eastcbd.html')

def view_eastborrowdale(request):
        return render(request, 'competence_building/borrowdale.html')

def view_eastmabvuku(request):
        return render(request, 'competence_building/eastmabvuku.html')

def view_eastruwa(request):
        return render(request, 'competence_building/eastruwa.html')

def view_chitownsales(request):
        return render(request, 'competence_building/chitownsales.html')

def view_eastsales(request):
        return render(request, 'competence_building/eastsales.html')

def view_chitownseke(request):
        return render(request, 'competence_building/chitownseke.html')

def view_chitownzengeza(request):
        return render(request, 'competence_building/chitownzengeza.html')

def view_chitowndistrict(request):
        return render(request, 'competence_building/chitowndistrict.html')

def view_itjobdescription(request):
        return render(request, 'competence_building/itjobdescription.html')

def view_hrjobdescription(request):
        return render(request, 'competence_building/hrjobdescription.html')

def view_srjobdescription(request):
        return render(request, 'competence_building/srjobdescription.html')

def view_riskjobdescription(request):
        return render(request, 'competence_building/riskjobdescription.html')

def view_procjobdescription(request):
        return render(request, 'competence_building/procjobdescription.html')

def view_legaljobdescription(request):
        return render(request, 'competence_building/legaljobdescription.html')

def view_finjobdescription(request):
        return render(request, 'competence_building/finjobdescription.html')

def view_engjobdescription(request):
        return render(request, 'competence_building/engjobdescription.html')

def view_comjobdescription(request):
        return render(request, 'competence_building/comjobdescription.html')

def view_infojobdescription(request):
        return render(request, 'competence_building/infojobdescription.html')

def view_eastengineering(request):
        return render(request, 'competence_building/eastengineering.html')

