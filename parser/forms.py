from django import forms

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return [single_file_clean(data, initial)]

class JDForm(forms.Form):       
    jd_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 6,
            'placeholder': ' ',
            'class':"peer h-full min-h-[100px] w-full resize-none rounded-[7px] border border-blue-gray-200 border-t-transparent bg-transparent px-3 py-2.5 font-sans text-sm font-normal text-blue-gray-700 outline outline-0 transition-all placeholder-shown:border placeholder-shown:border-green-200 placeholder-shown:border-t-blue-gray-200 focus:border-2 focus:border-green-500 focus:border-t-transparent focus:outline-0 disabled:resize-none disabled:border-0 disabled:bg-blue-gray-50"
    }),
        required=False,
        label=""
    )
    jd_file = forms.FileField(
        required=False,
        label="",
        widget=forms.ClearableFileInput(attrs={
            'accept': '.pdf,.doc,.docx',
            'class': 'block w-full text-sm text-gray-500 file:mr-4 file:rounded-md file:border-0 file:bg-blue-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-blue-700 hover:file:bg-blue-100'
        })
    )
    resume_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 6,
            'placeholder': '',
            'class': "peer h-full min-h-[100px] w-full resize-none rounded-[7px] border border-green-300 border-t-transparent bg-transparent px-3 py-2.5 font-sans text-sm font-normal text-blue-gray-700 outline outline-0 transition-all placeholder-shown:border placeholder-shown:border-green-300 placeholder-shown:border-t-green-300 focus:border-2 focus:border-green-500 focus:border-t-transparent focus:outline-0 disabled:resize-none disabled:border-0 disabled:bg-green-50"
        }),
        required=False,
        label="Paste Resume"
    )
    SOURCE_CHOICES = [
        ('upload', 'Upload Resumes'),
        # ('database', 'From Database')
    ]
    # source_choice = forms.ChoiceField(label="Choose an option for Resumes", widget=forms.Select(choices=SOURCE_CHOICES), required=True)
    source_choice=forms.ChoiceField(label="Choose the source for resumes",required=False,choices=SOURCE_CHOICES,widget=forms.Select(attrs={
        'class': 'block w-full px-4 py-2 border border-gray-300 bg-white text-gray-700 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
        'placeholder': 'Select source'
    }))
    resume_files = MultipleFileField(
        required=False,
        label="Upload Resumes",
        widget=MultipleFileInput(attrs={
            'multiple': True,
            'accept': '.pdf,.doc,.docx',
            'class': 'block w-full text-sm text-gray-500 file:mr-4 file:rounded-md file:border-0 file:bg-green-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-green-700 hover:file:bg-green-100'
        })
    )
    min_experience = forms.CharField(max_length=2,
                                    widget=forms.Textarea(attrs={'rows':2,
       'class': "rounded-md border border-green-300 focus:outline-none focus:ring focus:ring-green-500"
       }),required=False)
    must_have_skills = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2,
        'class':"rounded-md border border-green-300 focus:outline-none focus:ring focus:ring-green-500"
        }), required=False)
    nice_to_have_skills = forms.CharField(widget=forms.Textarea(attrs={'rows': 2,'class':"rounded-md border border-green-300 focus:outline-none focus:ring focus:ring-green-500"}), required=False)
    role_expectations = forms.CharField(widget=forms.Textarea(attrs={'rows': 2,'class':"rounded-md border border-green-300 focus:outline-none focus:ring focus:ring-green-500"}), required=False)

    def clean(self):
        cleaned_data = super().clean()
        jd_text = cleaned_data.get('jd_text')
        jd_file = cleaned_data.get('jd_file')
        resume_text = cleaned_data.get('resume_text')
        resume_files = cleaned_data.get('resume_files')
        if not jd_text and not jd_file:
            raise forms.ValidationError("Please provide a job description (either paste or upload).")
        if jd_text and jd_file:
            raise forms.ValidationError("Provide only one job description source.")
        if resume_text and resume_files:
            raise forms.ValidationError("Provide either pasted resume text or uploaded resume files, not both.")
        return cleaned_data
