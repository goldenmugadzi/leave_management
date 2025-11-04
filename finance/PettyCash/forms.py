from decimal import Decimal
from django import forms
from .models import Pettycash


class CashierDisbursementForm(forms.Form):
    payment_mode = forms.ChoiceField(
        choices=Pettycash.PAYMENT_MODE_CHOICES,
        required=True,
        label="Payment mode"
    )
    amount_disbursed = forms.DecimalField(
        required=True,
        min_value=Decimal("0.01"),
        max_digits=12,
        decimal_places=2,
        label="Amount disbursed"
    )

    def __init__(self, *args, pettycash: Pettycash, **kwargs):
        super().__init__(*args, **kwargs)
        self.pettycash = pettycash

        # Helpful default for cashier: start at requested amount
        if not self.is_bound:
            self.initial.setdefault("amount_disbursed", Decimal(str(self.pettycash.amount)))

        # Apply consistent styling to widgets
        self.fields["payment_mode"].widget.attrs.update({
            'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 bg-white shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-indigo-600 sm:text-sm",
        })
        self.fields["amount_disbursed"].widget = forms.NumberInput()
        self.fields["amount_disbursed"].widget.attrs.update({
            'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 bg-white shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-indigo-600 sm:text-sm",
            'step': '0.01',
            'min': '0.01',
            'inputmode': 'decimal',
        })

    def clean_amount_disbursed(self):
        amt = self.cleaned_data["amount_disbursed"]
        try:
            max_amt = Decimal(str(self.pettycash.amount))
        except Exception:
            max_amt = Decimal("0")
        if amt > max_amt:
            raise forms.ValidationError(f"Amount disbursed cannot exceed requested amount ({max_amt}).")
        return amt


from django import forms
from django.contrib.auth.models import User
from django.db.models import Q

from ACE2.models import AssetBudget
from it.users.models import UserProfile, Regions, Sections
from .models import Pettycash, Quotation
from django.forms import formset_factory


class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = ['quotation_file']


QuotationFormSet = formset_factory(QuotationForm, extra=0, min_num=1, validate_min=True)


class PettycashForm(forms.ModelForm):
    class Meta:
        model = Pettycash
        fields = '__all__'
        exclude = ['process', 'requested_by', 'pettycash_id', 'date_created', 'petty_id', 'payment_mode',
                   'amount_disbursed', 'receipt_file', 'old_version', 'amount_used']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        print("user", user)

        # Handle user parameter - can be either Django User or UserProfile
        user_profile = None
        if user:
            if hasattr(user, 'username'):
                # It's a Django User, get the UserProfile
                if hasattr(user, 'id'):
                    user_profile = UserProfile.objects.filter(id=user.id).first()
                else:
                    user_profile = UserProfile.objects.filter(username=user.username).first()
            else:
                # Assume it's already a UserProfile
                user_profile = user

        if user_profile:
            # Robust cost_center filtering with fallbacks
            from it.users.models import CostCenter
            
            if user_profile.cost_center:
                # Primary: Use user's cost center and its descendants
                cost_center_queryset = CostCenter.objects.filter(
                    id__in=user_profile.cost_center.get_decendance()
                ).order_by('name')
            elif user_profile.section:
                # Secondary: Filter by section name matching
                section_name = user_profile.section.section if hasattr(user_profile.section, 'section') else str(user_profile.section)
                cost_center_queryset = CostCenter.objects.filter(
                    Q(parent__name__icontains=section_name) | Q(name__icontains=section_name)
                ).order_by('name')
            else:
                # Fallback: Show all cost centers
                cost_center_queryset = CostCenter.objects.all().order_by('name')
            
            self.fields['cost_center'].queryset = cost_center_queryset
            
            # Robust section filtering with fallbacks
            if user_profile.region:
                region_obj = None
                if hasattr(user_profile.region, 'id'):
                    region_obj = user_profile.region
                else:
                    region_obj = Regions.objects.filter(region=user_profile.region).first()
                
                if region_obj:
                    section_queryset = Sections.objects.filter(region_id=region_obj.id)
                    if not section_queryset.exists():
                        # Fallback to all sections if region-based query returns nothing
                        section_queryset = Sections.objects.all()
                else:
                    section_queryset = Sections.objects.all()
            else:
                section_queryset = Sections.objects.all()
                
            self.fields['section'].queryset = section_queryset

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset "
                         "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 "
                         "sm:text-sm sm:leading-6",
            })

            if field_name == 'currency':
                choices = [(currency, currency) for currency in ['ZIG']]
                field.choices = choices
                field.widget.attrs.update({'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm '
                                                    'ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 '
                                                    'focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm '
                                                    'sm:leading-6'})
            if field_name == 'amount':
                field.widget.attrs.update({'type': 'number'})
                field.widget.attrs.update({'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm '
                                                    'ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 '
                                                    'focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm '
                                                    'sm:leading-6'
                                           })
                # set maximum to 2600
                field.widget.attrs.update({'max': '5000'})
            if field_name == 'section' or field_name == 'cost_center':
                field.widget.attrs.update({
                    'class': "select2 block w-full rounded-md border-0 py-1.5 text-gray-900 "
                             "shadow-sm ring-1 ring-inset ring-gray-300 "
                             "placeholder:text-gray-400 focus:ring-2 focus:ring-inset "
                             "focus:ring-indigo-600 sm:text-sm sm:leading-6", })

            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})

            field.label = field.label or self.humanize_field_name(field_name)
            field.label_attrs = {'class': 'block text-sm font-medium leading-6 text-gray-900'}

        self.formset = QuotationFormSet(*args, **kwargs)

        for i, quotation_form in enumerate(self.formset.forms):
            quotation_form.fields['quotation_file'].widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 bg-white shadow-sm ring-1 ring-inset "
                         "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 "
                         "sm:text-sm sm:leading-6",
            })
            quotation_form.fields['quotation_file'].label = self.get_quotation_label(i + 1)

    def humanize_field_name(self, field_name):
        words = field_name.split('_')
        capitalized_words = [word.capitalize() for word in words]
        return ' '.join(capitalized_words)

    def get_quotation_label(self, quotation_number):
        suffix = 'pc' if 11 <= quotation_number <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(quotation_number % 10, 'th')
        return f"{quotation_number}{suffix} Quotation"

    def clean(self):
        cleaned_data = super().clean()
        quotation_files = set()

        for quotation_form in cleaned_data.get('quotations', []):
            quotation_file = quotation_form.cleaned_data.get('quotation_file')
            if quotation_file in quotation_files:
                raise forms.ValidationError('Each quotation file must be distinct.')
            quotation_files.add(quotation_file)

        return cleaned_data


class PettycashReportForm(forms.ModelForm):
    start_date = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))

    # period = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    class Meta:
        model = Pettycash
        # add end date to fields

        fields = '__all__'
        exclude = ['process', 'requested_by', 'designation',
                   'details_of_expenditure', 'currency', 'amount', 'amount_disbursed', 'receipt_file', 'amount_used',
                   'amount', 'pettycash_id', 'old_version', 'petty_id', 'payment_mode', 'payee', 'reason_for_supplier'
                   # include the project items
                   ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        print("user", user)

        if user:
            user_profile = UserProfile.objects.filter(username=user.username).first()
            if user_profile:
                region = user_profile.region
                region_id = Regions.objects.filter(region=region).first()

                print("region", region)
                # self.fields['budget_id'].queryset = AssetBudget.objects.filter(period=2024, region=region)
                self.fields['section'].queryset = Sections.objects.filter(region_id=region_id.id)
                #

        for field_name, field in self.fields.items():
            # for the field budget, I want it to display its balance attribute when it selected

            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset "
                         "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset "
                         "focus:ring-indigo-600"
                         "sm:text-sm sm:leading-6",
            })
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})

            field.label = field.label or self.humanize_field_name(field_name)
            field.label_attrs = {'class': 'block text-sm font-medium leading-6 text-gray-900'}

            if (field_name == 'budget_id') or (field_name == 'section'):
                field.widget.attrs.update({
                    'class': "select2 block w-full rounded-md border-0 py-1.5 text-gray-900 "
                             "shadow-sm ring-1 ring-inset ring-gray-300 "
                             "placeholder:text-gray-400 focus:ring-2 focus:ring-inset "
                             "focus:ring-indigo-600 sm:text-sm sm:leading-6", })
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})

        # self.formset = QuotationForm(*args, **kwargs)
        #
        # for i, quotation_form in enumerate(self.formset.forms):
        #     quotation_form.fields['quotation_file'].widget.attrs.update({
        #         'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 bg-white shadow-sm ring-1 "
        #                  "ring-inset"
        #                  "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset "
        #                  "focus:ring-indigo-600"
        #                  "sm:text-sm sm:leading-6",
        #     })
        # quotation_form.fields['quotation_file'].label = self.get_quotation_label(i + 1)

    # def get_quotation_label(self, quotation_number): suffix = 'ACE' if 11 <= quotation_number <= 13 else {1: 'st',
    # 2: 'nd', 3: 'rd'}.get(quotation_number % 10, 'th')
    def humanize_field_name(self, field_name):
        words = field_name.split('_')
        capitalized_words = [word.capitalize() for word in words]
        return ' '.join(capitalized_words)


class RequesterClearForm(forms.Form):
    receipt_file = forms.FileField(required=True, label="Receipt")
    amount_used = forms.DecimalField(
        required=True,
        min_value=Decimal("0.01"),
        max_digits=12,
        decimal_places=2,
        label="Amount used"
    )

    def __init__(self, *args, pettycash: Pettycash, **kwargs):
        super().__init__(*args, **kwargs)
        self.pettycash = pettycash
        # Helpful default: set to amount_disbursed if present, else requested
        default_amt = self.pettycash.amount_disbursed if self.pettycash.amount_disbursed is not None else self.pettycash.amount
        if not self.is_bound and default_amt is not None:
            self.initial.setdefault("amount_used", Decimal(str(default_amt)))

        # Apply consistent styling to widgets
        self.fields["receipt_file"].widget.attrs.update({
            'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 bg-white shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-indigo-600 sm:text-sm",
        })
        self.fields["amount_used"].widget = forms.NumberInput()
        self.fields["amount_used"].widget.attrs.update({
            'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 bg-white shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-indigo-600 sm:text-sm",
            'step': '0.01',
            'min': '0.01',
            'inputmode': 'decimal',
        })

    def clean_amount_used(self):
        used = self.cleaned_data["amount_used"]
        try:
            cap = self.pettycash.amount_disbursed if self.pettycash.amount_disbursed is not None else self.pettycash.amount
            cap_dec = Decimal(str(cap))
        except Exception:
            cap_dec = Decimal("0")
        if used > cap_dec:
            raise forms.ValidationError(f"Amount used cannot exceed {cap_dec}.")
        return used
