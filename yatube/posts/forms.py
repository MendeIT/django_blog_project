from django import forms

from posts.models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        widgets = {
            'text': forms.Textarea(
                attrs={'cols': 45, 'rows': 5}
            )
        }
        help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост'
        }

    def clean_text(self):
        ''' Валидатор текста при создании поста'''
        data = self.cleaned_data['text']
        if data == '':
            raise forms.ValidationError('Пусто, добавьте текст!')
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {
            'text': 'Введите комментарий',
        }
        widgets = {
            'text': forms.Textarea(
                attrs={'cols': 45, 'rows': 2}
            )
        }

    def clean_text(self):
        ''' Валидатор текста при создании комментария'''
        data = self.cleaned_data['text']
        if data == '':
            raise forms.ValidationError('Пусто, добавьте текст!')
        return data
