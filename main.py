import aiosqlite  # tool to connect and talk to our database
from fastapi import FastAPI, Request, Form  # main framework, user request, form data
from fastapi.responses import HTMLResponse, RedirectResponse  # send html page or redirect user
from fastapi.staticfiles import StaticFiles  # serve our css file
from fastapi.templating import Jinja2Templates  # fill html pages with real data
from contextlib import asynccontextmanager  # run code when server starts

# name of our database file
DATABASE = "blog.db"

async def init_db():  # this function creates the database table
    async with aiosqlite.connect(DATABASE) as db:  # open the database file
        await db.execute("""
            CREATE TABLE IF NOT EXISTS posts (  -- create table only if it doesnt exist
                id INTEGER PRIMARY KEY AUTOINCREMENT,  -- unique number for each post, auto increases
                title TEXT NOT NULL,                   -- post title, cannot be empty
                content TEXT NOT NULL,                 -- post content, cannot be empty
                author TEXT NOT NULL,                  -- author name, cannot be empty
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- saves current date and time automatically
            )
        """)
        await db.commit()  # save the changes to database

@asynccontextmanager
async def lifespan(app: FastAPI):  # runs when server starts
    await init_db()  # create the table before anything else
    yield  # now keep the server running

app = FastAPI(lifespan=lifespan)  # create our web app and run init_db on startup
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")  # tell fastapi where css file is
templates = Jinja2Templates(directory="frontend/templates")  # tell fastapi where html files are

@app.get("/", response_class=HTMLResponse)  # when user visits home page
async def home(request: Request):
    async with aiosqlite.connect(DATABASE) as db:  # open database
        db.row_factory = aiosqlite.Row  # makes data readable like a dictionary
        cursor = await db.execute("SELECT * FROM posts ORDER BY created_at DESC")  # get all posts newest first
        posts = await cursor.fetchall()  # store all posts in variable
    return templates.TemplateResponse(request, "index.html", {"posts": posts})  # send posts to home page html

@app.get("/post/{post_id}", response_class=HTMLResponse)  # when user clicks on a specific post
async def view_post(request: Request, post_id: int):  # post_id comes from url eg /post/1
    async with aiosqlite.connect(DATABASE) as db:  # open database
        db.row_factory = aiosqlite.Row  # makes data readable like a dictionary
        cursor = await db.execute("SELECT * FROM posts WHERE id = ?", (post_id,))  # get only that one post
        post = await cursor.fetchone()  # store that single post
    if not post:  # if post doesnt exist
        return HTMLResponse("Post not found", status_code=404)  # show error message
    return templates.TemplateResponse(request, "post.html", {"post": post})  # send post to post page html

@app.get("/create", response_class=HTMLResponse)  # when user clicks new post button
async def create_page(request: Request):
    return templates.TemplateResponse(request, "create.html", {})  # just show the empty form, no database needed

@app.post("/create")  # when user submits the form
async def create_post(
    title: str = Form(...),    # get title from form
    content: str = Form(...),  # get content from form
    author: str = Form(...)    # get author from form
):
    async with aiosqlite.connect(DATABASE) as db:  # open database
        await db.execute(
            "INSERT INTO posts (title, content, author) VALUES (?, ?, ?)",  # add new row in database
            (title, content, author)  # fill with form data
        )
        await db.commit()  # save to database permanently
    return RedirectResponse("/", status_code=303)  # send user back to home page

@app.post("/delete/{post_id}")  # when user clicks delete button
async def delete_post(post_id: int):  # get the post id from url
    async with aiosqlite.connect(DATABASE) as db:  # open database
        await db.execute("DELETE FROM posts WHERE id = ?", (post_id,))  # remove that post from database
        await db.commit()  # save the change
    return RedirectResponse("/", status_code=303)  # send user back to home page