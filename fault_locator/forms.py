from django import forms
from .models import Fault, FaultLocatorDevice, FaultLocatorTeam,FaultLocatorDeviceAssignment, FaultAssignment
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

class AssignDeviceToTeamForm(forms.ModelForm):
    class Meta:
        model = FaultLocatorDeviceAssignment
        fields = ['device', 'team']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show devices not already assigned
        assigned_devices = FaultLocatorDeviceAssignment.objects.values_list('device_id', flat=True)
        self.fields['device'].queryset = FaultLocatorDevice.objects.exclude(id__in=assigned_devices)

    def clean_device(self):
        device = self.cleaned_data['device']
        if FaultLocatorDeviceAssignment.objects.filter(device=device).exists():
            raise forms.ValidationError("This device is already assigned to a team.")
        return device

class AssignFaultForm(forms.ModelForm):
    class Meta:
        model = FaultAssignment
        fields = ['fault', 'team']  # Remove 'device' from the form