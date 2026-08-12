from django import forms
from django.utils.text import slugify
from .models import Post, Category, Tag


class PostForm(forms.ModelForm):
    """Form for creating and editing blog posts."""

    # Allow entering new tags as comma-separated text
    tag_names = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Add a tag...',
            'id': 'tagInput',
            'autocomplete': 'off',
        }),
        help_text='Enter tags separated by commas.',
    )

    class Meta:
        model = Post
        fields = ['title', 'content', 'cover_image', 'category', 'status', 'featured']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your post title...',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': 'Write your post content here...',
            }),
            'cover_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.HiddenInput(),
            'featured': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Default status to 'published' so posts appear immediately
        if not self.instance.pk:
            self.fields['status'].initial = 'published'
        # Featured defaults to False — only admins would change this
        self.fields['featured'].initial = False
        # Make these non-required so the hidden fields don't block submission
        self.fields['status'].required = False
        self.fields['featured'].required = False
        # Pre-fill tag_names for editing
        if self.instance.pk:
            self.fields['tag_names'].initial = ', '.join(
                tag.name for tag in self.instance.tags.all()
            )

    def save(self, commit=True):
        post = super().save(commit=commit)
        if commit:
            self._save_tags(post)
        return post

    def _save_tags(self, post):
        """Parse tag_names field and create/assign Tag objects."""
        tag_names_str = self.cleaned_data.get('tag_names', '')
        # Support both comma and space-separated tags, strip # prefix
        raw_names = [
            name.strip().lower().lstrip('#').strip()
            for name in tag_names_str.replace('#', ' ').split(',')
        ]
        # Deduplicate while preserving order
        seen = set()
        tag_names = []
        for name in raw_names:
            if name and name not in seen:
                seen.add(name)
                tag_names.append(name)

        tags = []
        for name in tag_names:
            if not name:
                continue
            # Look up by name, let models.py handle generating a unique slug
            try:
                tag = Tag.objects.get(name__iexact=name)
            except Tag.DoesNotExist:
                tag = Tag.objects.create(name=name)
            tags.append(tag)
        post.tags.set(tags)


class CategoryForm(forms.ModelForm):
    """Form for creating categories (admin use)."""
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category name',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Category description...',
            }),
        }
