import os
import re
from string import letters

import webapp2
import jinja2
import hashlib

from google.appengine.ext import db

# Templates below: create the directory for templates, place templates in there
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

# main hanlder, with 3 convenience functions
class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

def render_post(response, post):
    response.out.write('<b>' + post.subject + '</b><br>')
    response.out.write(post.content)

# blog key defines the value of the blog's parent
# takes a name parameter (default) in case we're working with multiple blogs
def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)

def hash_str(s) 
    return hashlib.md5(s).hexdigest()

# takes a string a returns a string of the format: s, HASH
def make_secure_val(s): 
    return "%s|%s" % (s, hash_str(s))

# take a string of the format s,HASH and returns s if hash_str(s) == HASH, otherwise None
def check_secure_val(h): 
    # here we're splitting s,HASH and taking the first part of it (e.g. val = s)
    # then we check to see if the value we're passing == s, HASH (which is what make_secure_val(val) returns)
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val

class MainPage(BlogHandler):
    def get(self):
        # set content type to text so we don't have to deal with html
        self.response.headers['Content-Type'] = 'text/plain'
        # visits is the actual visits count, which is by default 0
        visits = 0
         # request object (which is on self) has a cookies object. Call the function get
        # GET checks whether a value is in a dictionary; if it is we get it; otherwise return none if that cookie doesn't exist at all
        visit_cookie_str = self.request.cookies.get('visits')
        if visit_cookie_val:
            cookie_val = check_secure_val(visit_cookie_str)
            # remember this function returns none if not valid. If it IS valid, convert to int and store in visits
            if cookie_val: 
                visits = int(cookie_val)
        
        visits += 1

        new_cookie_val = make_secure_val(str(visits))
        
        # use a header to set a cookie
        self.response.headers.add_header('Set-Cookie', 'visits=%s' % new_cookie_val) 

        if visits > 1000: 
            self.write("You are the best ever!")
        else: 
            self.write("You've been here %s times!" % visits)

# The properties that a blog has. String vs text property? 
# Remember that string has limit, while text does not. Strings can be indexed, and text cannot
# Text can also have newlines in it
class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    # two time properties below. 
    # auto now add automatically includes time of creation, so we don't have to manually add
    created = db.DateTimeProperty(auto_now_add = True)
    # last modified updates the 'created' property whenever we update
    last_modified = db.DateTimeProperty(auto_now = True)

    # renders blog entry
    def render(self):
        # this line replaces all new lines with line breaks 
        # otherwise when we leave blank lines, html wouldn't know that we intend those to be line breaks
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p = self)

class BlogFront(BlogHandler):
    def get(self):
        # looks at all of the posts orderd by creation time
        posts = db.GqlQuery("select * from Post order by created desc limit 10")
        # renders the result of the query above in the variable 'posts'
        self.render('front.html', posts = posts)

# renders the page for any one particular post
class PostPage(BlogHandler):
    def get(self, post_id):
        # here, we're looking up in the data store, a POST ID whose parent is BLOG KEY
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        # look up the item KEY and store it in POST
        post = db.get(key)

        # if there's not a post with that id, return error
        # if there is, return the permalink with the post
        if not post:
            self.error(404)
            return

        self.render("permalink.html", post = post)
        # At the very bottom, where it says app = webapp2, blog/0-9+ denotes what happens when
        # you enter the url "blog/0-9+" -- it takes you to the PostPage class, and passes the number
        # you entered as a variable into post_id

class NewPost(BlogHandler):
    # this renders the new post
    def get(self):
        self.render("newpost.html")

    # this posts the new post
    # first, we get the subject and content parameters out of the post
    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')

        # if we don't have subject/content, we render the form again with error messages
        # if there is subject + content, we create a new post. Set PARENT (not required)
        if subject and content:
            p = Post(parent = blog_key(), subject = subject, content = content)
            # p.put() stores data in database
            p.put()
            # redirect user to the blog page of the new blog, where p.key().id() 
            # is how you get the new blog's id out of datastore
            self.redirect('/blog/%s' % str(p.key().id()))
        else:
            error = "subject and content, please!"
            self.render("newpost.html", subject=subject, content=content, error=error)

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/blog/?', BlogFront),
                               ('/blog/([0-9]+)', PostPage),
                               ('/blog/newpost', NewPost),
                               ],
                              debug=True)
