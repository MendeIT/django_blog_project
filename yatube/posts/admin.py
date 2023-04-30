from django.contrib import admin

from posts.models import Group
from posts.models import Follow
from posts.models import Comment
from posts.models import Post


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'pub_date', 'author', 'group')
    search_fields = ('text',)
    list_filter = ('pub_date',)
    list_editable = ('group',)
    empty_value_display = '-пусто-'


class CommentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'post', 'created', 'text', 'author')
    search_fields = ('text', 'post',)
    list_filter = ('created',)
    empty_value_display = '-пусто-'


class FollowAdmin(admin.ModelAdmin):
    list_display = ('author', 'user')
    search_fields = ('author',)
    list_filter = ('author',)
    list_editable = ('user',)
    empty_value_display = '-пусто-'


admin.site.register(Post, PostAdmin)

admin.site.register(Group)

admin.site.register(Comment, CommentAdmin)

admin.site.register(Follow, FollowAdmin)
