from django import forms
from django.contrib.auth.models import User
from .models import *
from django.forms import formset_factory
from it.users.models import UserProfile, Regions, Sections, Designations
from .models import AssetBudget
from .utils import determine_ace_type  # Removed convert_to_usd import


class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = ['quotation_file']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make quotation file optional
        self.fields['quotation_file'].required = False


QuotationFormSet = formset_factory(QuotationForm, extra=1, min_num=0, validate_min=False)


class AceForm(forms.ModelForm):
    class Meta:
        model = Ace2
        fields = '__all__'
        exclude = ['process', 'allocation_code_of_expenditure', 'requested_by', 'date_created'
            , 'Ace_id2', 'Ace_id', 'asset_number', 'designation', 'region', 'ace_type', 'usd_equivalent'  # Keep excluding usd_equivalent since we don't use it anymore
                   # exclude the project items
            , 'capital_estimated', 'capital_sanctioned', 'capital_contribution', 'materials', 'labour',
                   'connection_fee', 'transport', 'present_tariff', 'present_fmc', 'total_connection_fee'
                   ]

    def __init__(self, *args, **kwargs):

        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)


        if user:
            # Accept either a Django User or our UserProfile
            user_profile = user if isinstance(user, UserProfile) else UserProfile.objects.filter(username=getattr(user, 'username', None)).first()
            if user_profile:
                region = user_profile.region
                # Regions.region is CharField; fall back safely if lookup fails
                region_obj = None
                if region:
                    region_obj = Regions.objects.filter(id=getattr(region, 'id', None)).first() or \
                                 Regions.objects.filter(region=str(region)).first()

                # Budgets limited to year and region when possible
                if region:
                    self.fields['budget_id'].queryset = AssetBudget.objects.filter(period=2026, region=region)
                # Sections limited to region; if lookup fails, fall back to all
                if region_obj:
                    self.fields['section'].queryset = Sections.objects.filter(region_id=str(region_obj.id))
                if not self.fields['section'].queryset.exists():
                    self.fields['section'].queryset = Sections.objects.all().order_by('section')

                # Set section initial value to user's section and hide the field
                if getattr(user_profile, 'section', None):
                    self.fields['section'].initial = user_profile.section.pk
                    self.fields['section'].widget = forms.HiddenInput()

                # Cost center filtering hierarchy:
                # 1) If user has a cost_center, allow it and its descendants
                from it.users.models import CostCenter
                cc_qs = CostCenter.objects.none()
                if getattr(user_profile, 'cost_center', None):
                    try:
                        base_cc = user_profile.cost_center
                        cc_qs = CostCenter.objects.filter(pk=base_cc.pk) | base_cc.get_decendance()
                    except Exception:
                        cc_qs = CostCenter.objects.none()
                # 2) Else, if user has a section, try name-based match on CC name/parent name
                if not cc_qs.exists() and user_profile.section:
                    sec_name = user_profile.section.section
                    cc_qs = CostCenter.objects.filter(parent__name__icontains=sec_name) | \
                            CostCenter.objects.filter(name__icontains=sec_name)
                # 3) Final fallback: show all cost centers (ordered)
                if not cc_qs.exists():
                    cc_qs = CostCenter.objects.all().order_by('name')
                self.fields['cost_center'].queryset = cc_qs

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset "
                         "ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 "
                         "sm:text-sm sm:leading-6",
            })

            if (field_name == 'id_from_budget') or (field_name == 'section') or (field_name == 'id_to_budget') or (
                    field_name == 'budget_id') or (field_name == 'designation') or (field_name == 'classification') or (field_name == 'cost_center'):
                field.widget.attrs.update({
                    'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset "
                             "ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:max-w-xs sm:text-sm "
                             "sm:leading-6",
                })

            if field_name == 'section' or field_name == 'budget_id' or field_name == 'cost_center':
                field.widget.attrs.update({
                    'class': "select2 block w-full rounded-md border-0 py-1.5 text-gray-900 "
                             "shadow-sm ring-1 ring-inset ring-gray-300 "
                             "placeholder:text-gray-400 focus:ring-2 focus:ring-inset "
                             "focus:ring-indigo-600 sm:text-sm sm:leading-6", })

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        currency = cleaned_data.get('currency', 'ZWL')

        if amount:
            # Determine ACE type based on ZWL amount
            ace_type, zwl_amount = determine_ace_type(amount, currency)
            cleaned_data['ace_type'] = ace_type
            # No longer setting usd_equivalent

            # Show warning for high-value ACEs
            if ace_type == 'high_value':
                self.add_error(None, f"⚠️ HIGH VALUE ACE: This ACE is worth {zwl_amount:,.2f} ZWL and will require extended approval workflow.")

        return cleaned_data

    # quotation_form.fields['quotation_file'].label = self.get_quotation_label(i + 1)

    # if field is budget display the balnce and name

    def humanize_field_name(self, field_name):
        words = field_name.split('_')
        capitalized_words = [word.capitalize() for word in words]
        return ' '.join(capitalized_words)

    def get_quotation_label(self, quotation_number):
        suffix = 'ACE' if 11 <= quotation_number <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(quotation_number % 10, 'th')
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

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None:
            raise forms.ValidationError("Amount is required.")
        if amount < 0:
            raise forms.ValidationError("Amount cannot be negative.")
        return amount

    def clean(self):
        cleaned_data = super().clean()
        required_fields = ['details_of_expenditure', 'budget_id', 'section']
        for field in required_fields:
            if not cleaned_data.get(field):
                self.add_error(field, f"{field.replace('_', ' ').capitalize()} is required.")

        # Warn if budget is close to exhausted
        budget = cleaned_data.get('budget_id')
        amount = cleaned_data.get('amount')
        if budget and amount is not None:
            # Use available_balance to consider to_be_withdrawn amounts
            remaining = budget.available_balance - amount
            threshold = budget.available_balance * 0.1  # 10% of available balance
            if remaining < threshold:
                self.add_error('amount', f"Warning: This will leave less than 10% of the available budget remaining (only {remaining:,.2f} left).")

            if amount > budget.available_balance:
                self.add_error('amount', 
                    f"Amount exceeds available budget. "
                    f"Available: {budget.available_balance:,.2f} "
                    f"(Balance: {budget.balance:,.2f}, "
                    f"To be withdrawn: {budget.to_be_withdrawn or 0:,.2f})"
                )

        return cleaned_data


class ProjectDetailForm(forms.ModelForm):
    class Meta:
        model = Ace2
        fields = '__all__'
        exclude = ['process', 'allocation_code_of_expenditure', 'requested_by', 'date_created', 'Ace_id', 'asset_number'
            , 'designation', 'region', 'amount', 'budget_id', 'currency', 'classification', 'Ace_id2',
                   'details_of_expenditure', 'quantity', 'total_connection_fee', 'section', 'cost_center', 'ace_type', 'usd_equivalent'
                   # include the project items
                   ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
    # 2: 'nd', 3: 'rd'}.get(quotation_number % 10, 'th') return f"{quotation_number}{suffix} Quotation"

    def clean(self):
        cleaned_data = super().clean()
        quotation_files = set()

        for quotation_form in cleaned_data.get('quotations', []):
            quotation_file = quotation_form.cleaned_data.get('quotation_file')
            if quotation_file in quotation_files:
                raise forms.ValidationError('Each quotation file must be distinct.')
            quotation_files.add(quotation_file)

        return cleaned_data

    def humanize_field_name(self, field_name):
        words = field_name.split('_')
        capitalized_words = [word.capitalize() for word in words]
        return ' '.join(capitalized_words)


class ViramentForm(forms.ModelForm):
    class Meta:
        model = Asset_budget_Virament
        fields = '__all__'
        exclude = ['process', 'requested_by', 'virament_id', 'date_created', 'region'
                   ]

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None:
            raise forms.ValidationError("Amount is required.")
        if amount <= 0:
            raise forms.ValidationError("Amount must be positive.")
        return amount

    def clean(self):
        cleaned_data = super().clean()
        from_budget = cleaned_data.get('from_budget')
        to_budget = cleaned_data.get('to_budget')
        amount = cleaned_data.get('amount')

        # Check if from_budget and to_budget are the same
        if from_budget and to_budget and from_budget == to_budget:
            raise forms.ValidationError("Source and destination budgets cannot be the same.")

        # Check if source budget has sufficient available balance (considering to_be_withdrawn)
        if from_budget and amount is not None:
            # Use available_balance property which considers to_be_withdrawn
            if amount > from_budget.available_balance:
                raise forms.ValidationError(
                    f"Insufficient available balance in source budget. "
                    f"Available: {from_budget.available_balance:,.2f} "
                    f"(Balance: {from_budget.balance:,.2f}, "
                    f"To be withdrawn: {from_budget.to_be_withdrawn or 0:,.2f})"
                )
            
            # Warn if transfer would use more than 80% of available balance
            if amount > (from_budget.available_balance * 0.8):
                self.add_error('amount', 
                    f"Warning: This transfer uses {(amount/from_budget.available_balance)*100:.1f}% "
                    f"of available budget balance."
                )

        return cleaned_data

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
                self.fields['to_budget'].queryset = AssetBudget.objects.filter(period=2026, region=region)
                self.fields['from_budget'].queryset = AssetBudget.objects.filter(period=2026, region=region)
                self.fields['section'].queryset = Sections.objects.filter(region_id=str(region_id.id))

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
    # 2: 'nd', 3: 'rd'}.get(quotation_number % 10, 'th') return f"{quotation_number}{suffix} Quotation"


class AceReportForm(forms.ModelForm):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    budget_id = forms.ModelChoiceField(
        queryset=AssetBudget.objects.none(),  # Set initially empty, populated in __init__
        required=False,
        empty_label="All Budgets"
    )
    # Removed cost_center field to simplify reporting

    # period = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    class Meta:
        model = Ace2
        # add end date to fields

        fields = '__all__'
        exclude = ['process', 'requested_by', 'Ace_id', 'asset_number', 'designation', 'Ace_id2',
                   'details_of_expenditure', 'quantity', 'total_connection_fee', 'capital_estimated',
                   'capital_sanctioned',
                   'present_tariff', 'present_fmc', 'capital_contribution', 'materials', 'connection_fee', 'labour',
                   'transport'
            , 'classification', 'currency', 'amount', 'allocation_code_of_expenditure', 'section','usd_equivalent'
                   # include the project items
                   ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        print("user", user)

        if user:
            # Handle both UserProfile and User objects
            if isinstance(user, UserProfile):
                user_profile = user
            else:
                user_profile = UserProfile.objects.filter(username=user.username).first()

            if user_profile and user_profile.region:
                # Get budgets for user's region (without period restriction)
                self.fields['budget_id'].queryset = AssetBudget.objects.filter(
                    region=user_profile.region
                ).order_by('-period', 'budget_name')
                
                # Store the region for form validation
                self.user_region = user_profile.region
            else:
                self.fields['budget_id'].queryset = AssetBudget.objects.none()

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

            if field_name == 'section':
                field.widget.attrs.update({
                    'class': "select2 block w-full rounded-md border-0 py-1.5 text-gray-900 "
                             "shadow-sm ring-1 ring-inset ring-gray-300 "
                             "placeholder:text-gray-400 focus:ring-2 focus:ring-inset "
                             "focus:ring-indigo-600 sm:text-sm sm:leading-6", })

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
    # 2: 'nd', 3: 'rd'}.get(quotation_number % 10, 'th') return f"{quotation_number}{suffix} Quotation"

    def humanize_field_name(self, field_name):
        words = field_name.split('_')
        capitalized_words = [word.capitalize() for word in words]
        return ' '.join(capitalized_words)


class ReportForm(forms.Form):
    attribute = forms.ChoiceField(choices=[(field.name, field.name) for field in Ace2._meta.fields])
    value = forms.CharField(max_length=100)
