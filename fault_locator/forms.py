from django import forms
from .models import Fault, FaultLocatorDevice, FaultLocatorTeam
from it.users.models import UserProfile, Depots
from django_select2.forms import Select2MultipleWidget

class FaultForm(forms.ModelForm):
    class Meta:
        model = Fault
        fields = ['description', 'depot']

class FaultLocatorDeviceForm(forms.ModelForm):
    class Meta:
        model = FaultLocatorDevice
        fields = ['serial_number', 'description']

class FaultLocatorTeamForm(forms.ModelForm):
    class Meta:
        model = FaultLocatorTeam
        fields = ['name', 'members']
        widgets = {
            'members': Select2MultipleWidget(attrs={'style': 'width: 100%;'}),
        }

class FaultLocatorTeamNameForm(forms.ModelForm):
    class Meta:
        model = FaultLocatorTeam
        fields = ['name']

class AddTeamMemberForm(forms.Form):
    member = forms.ModelChoiceField(
        queryset=UserProfile.objects.all(),
        label="Add Member"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply ACE-style classes
        self.fields['member'].widget.attrs.update({
            'class': "select2 block w-full rounded-md border-0 py-1.5 text-gray-900 "
                     "shadow-sm ring-1 ring-inset ring-gray-300 "
                     "placeholder:text-gray-400 focus:ring-2 focus:ring-inset "
                     "focus:ring-indigo-600 sm:text-sm sm:leading-6"
        })
        self.fields['member'].label_attrs = {'class': 'block text-sm font-medium leading-6 text-gray-900'}