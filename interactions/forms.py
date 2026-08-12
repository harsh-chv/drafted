from django import forms
from .models import Comment


class CommentForm(forms.ModelForm):
    """Form for adding/editing comments."""
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'bg-transparent border-none outline-none focus:ring-0 w-full text-[17px] text-[#0F1419] dark:text-[#E7E9EA] placeholder-[#536471] dark:placeholder-[#71767B] resize-none',
                'rows': 3,
                'placeholder': 'Write your comment...',
                'required': True,
            }),
        }
        labels = {
            'content': '',
        }
