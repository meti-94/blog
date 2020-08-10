from django.db.models import Count
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage,\
                                  PageNotAnInteger
from django.core.mail import send_mail
from django.views.generic import ListView
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.contrib.postgres.search import TrigramSimilarity
from .models import Post, Comment
from .forms import EmailPostForm, CommentForm, SearchForm
from taggit.models import Tag
from django.http import HttpResponse

import json 
from django.contrib.auth.models import User
import random, string
from urllib.parse import unquote

def post_list(request, tag_slug=None):
    object_list = Post.published.all()
    tag = None
    # print("this is it!")
    if tag_slug:
        # print("tag slug!")
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])
    # print("Not tag slug!")
    paginator = Paginator(object_list, 3) # 3 posts in each page
    page = request.GET.get('page')
    all_posts = Post.objects.all()
    gau = [item.get_absolute_url() for item in all_posts]
    print(gau, len(gau))
    print(page)
    try:
        # print("we go here!")
        posts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer deliver the first page
        posts = paginator.page(1)
    # print("none of above!")
    except EmptyPage:
        # If page is out of range deliver last page of results
        posts = paginator.page(paginator.num_pages)
    # print("none of above!")
    return render(request,
                 'blog/post/list.html',
                 {'page': page,
                  'posts': posts,
                  'tag': tag})

def post_detail(request, post):
    post = get_object_or_404(Post, slug=post,
                                   status='published')

    # List of active comments for this post
    comments = post.comments.filter(active=True)

    new_comment = None

    if request.method == 'POST':
        # A comment was posted
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            # Create Comment object but don't save to database yet
            new_comment = comment_form.save(commit=False)
            # Assign the current post to the comment
            new_comment.post = post
            # Save the comment to the database
            new_comment.save()
    else:
        comment_form = CommentForm()

    # List of similar posts
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids)\
                                  .exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags'))\
                                .order_by('-same_tags','-publish')[:4]

    return render(request,
                  'blog/post/detail.html',
                  {'post': post,
                   'comments': comments,
                   'new_comment': new_comment,
                   'comment_form': comment_form,
                   'similar_posts': similar_posts})


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


def post_share(request, post_id):
    # Retrieve post by id
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False

    if request.method == 'POST':
        # Form was submitted
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Form fields passed validation
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read {post.title}"
            message = f"Read {post.title} at {post_url}\n\n" \
                      f"{cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'admin@myblog.com', [cd['to']])
            sent = True

    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post': post,
                                                    'form': form,
                                                    'sent': sent})


def post_search(request):
    form = SearchForm()
    query = None
    results = []
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            results = Post.published.annotate(
                similarity=TrigramSimilarity('title', query),
            ).filter(similarity__gt=0.1).order_by('-similarity')
    return render(request,
                  'blog/post/search.html',
                  {'form': form,
                   'query': query,
                   'results': results})

def update_users(request):
  random_email = lambda length:''.join(random.choice(string.ascii_letters) for x in range(length))
  with open('blog/chetor.json') as fin:
    data = json.load(fin)
  # create users 
  for article in data:
    try:  
      username = article['author'][0]
      email = random_email(10)+'@gmail.com'
      password = 'password'
      User.objects.create_superuser(username, email, 'password')
      print(username, email, password)
    except:
      pass
  # create posts
  counter = 0
  for article in data:
    temp_art = article
    try:
      temp_post = Post(title = temp_art['title'][0], 
                       slug=unquote(temp_art['slug'][0]), 
                       author=User.objects.get(username=temp_art['author'][0]), 
                       body = temp_art['body'][0], 
                       publish =temp_art['lastmodified'][0], 
                       status='published')
      temp_post.save()
      for tag in temp_art['tags']:
        temp_post.tags.add(f'"{tag}"')
      counter+=1
    except: 
         pass
  return 0
#      print(counter)
#  return 0
