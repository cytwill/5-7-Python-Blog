import os
import re
from string import letters

import webapp2
import jinja2

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

class MainPage(BlogHandler):
  def get(self):
      self.write('Hello, Udacity!')

# blog key defines the value of the blog's parent
# takes a name parameter (default) in case we're working with multiple blogs
def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)

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



###### Unit 2 HW's
class Rot13(BlogHandler):
    def get(self):
        self.render('rot13-form.html')

    def post(self):
        rot13 = ''
        text = self.request.get('text')
        if text:
            rot13 = text.encode('rot13')

        self.render('rot13-form.html', text = rot13)


USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)

class Signup(BlogHandler):

    def get(self):
        self.render("signup-form.html")

    def post(self):
        have_error = False
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        params = dict(username = username,
                      email = email)

        if not valid_username(username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif password != verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)
        else:
            self.redirect('/unit2/welcome?username=' + username)

class Welcome(BlogHandler):
    def get(self):
        username = self.request.get('username')
        if valid_username(username):
            self.render('welcome.html', username = username)
        else:
            self.redirect('/unit2/signup')

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/unit2/rot13', Rot13),
                               ('/unit2/signup', Signup),
                               ('/unit2/welcome', Welcome),
                               ('/blog/?', BlogFront),
                               ('/blog/([0-9]+)', PostPage),
                               ('/blog/newpost', NewPost),
                               ],
                              debug=True)
