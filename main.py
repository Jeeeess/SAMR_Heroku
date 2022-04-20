import datetime
import nltk
import mysql.connector
import os

from flask import Flask, render_template, request, session, redirect
from nltk.corpus import stopwords
from textblob import TextBlob

nltk.download('stopwords')
set(stopwords.words('english'))
app = Flask(__name__)
app.secret_key = os.urandom(24)

try:
    conn = mysql.connector.connect(
        host="127.0.0.1", user="root js", password="jsadmin@22", database="web application")
    cursor = conn.cursor()
except:
    print("An exception occurred")


# --------------------------------------------------
# Authentication Module
@app.route('/')
def mainpage():
    cursor.execute("""SELECT * FROM movie AS m JOIN sentimentreview AS s on m.MovieName = s.movieName WHERE label='1' GROUP BY s.movieName ORDER BY COUNT(label) DESC LIMIT 4""")
    recommend_movies = cursor.fetchall()
    cursor.execute("""SELECT * FROM movie ORDER BY YearReleased DESC LIMIT 4""")
    movies = cursor.fetchall()
    cursor.execute("""SELECT * FROM movie ORDER BY MovieRating DESC LIMIT 4""")
    high_rating_movies = cursor.fetchall()
    return render_template('home.html', recommend_movies=recommend_movies, movies=movies, high_rating_movies=high_rating_movies)


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/login_validation', methods=['POST'])
def login_validation():
    email = request.form.get('email')
    password = request.form.get('password')
    cursor.execute("""SELECT * from user WHERE email = %s AND password = %s""", (email, password))
    user = cursor.fetchone()
    if user:
        session['user_id'] = user[1]
        session['user_email'] = user[0]
        return redirect('/home')
    else:
        msg = "You have entered wrong email or password!"
        return render_template('login.html', wrong_msg=msg, email=email, password=password)


@app.route('/home')
def home():
    if 'user_id' in session:
        cursor.execute("""SELECT * FROM movie AS m JOIN sentimentreview AS s on m.MovieName = s.movieName WHERE label='1' GROUP BY s.movieName ORDER BY COUNT(label) DESC LIMIT 4""")
        recommend_movies = cursor.fetchall()
        cursor.execute("""SELECT * FROM movie ORDER BY YearReleased DESC LIMIT 4""")
        movies = cursor.fetchall()
        cursor.execute("""SELECT * FROM movie ORDER BY MovieRating DESC LIMIT 4""")
        high_rating_movies = cursor.fetchall()
        return render_template('user_home.html', recommend_movies=recommend_movies, movies=movies, high_rating_movies=high_rating_movies)
    else:
        return redirect('/')


@app.route('/account')
def account():
    if 'user_id' in session:
        cursor.execute("""SELECT * FROM user WHERE username = %s""", (session['user_id'],))
        user = cursor.fetchone()
        return render_template('account.html', user=user)


@app.route('/add_user', methods=['POST'])
def add_user():
    name = request.form.get('username')
    email = request.form.get('uemail')
    password = request.form.get('upassword')
    cursor.execute("""SELECT * from user WHERE email = %s""", (email,))
    user = cursor.fetchone()
    if user:
        msg = "This email is already registered!"
        return render_template('register.html', msg_email=msg, username=name, uemail=email, upassword=password)
    else:
        cursor.execute("""SELECT * from user WHERE username = %s""", (name,))
        user_name = cursor.fetchone()
        if user_name:
            msg_name = "This username is taken by someone!"
            return render_template('register.html', msg_name=msg_name, username=name, uemail=email, upassword=password)
        else:
            cursor.execute(
                """INSERT INTO user(email,username,password,lastName,firstName,gender,genre) VALUES (%s,%s,%s,'-','-','-','-')""",
                (email, name, password))
            cursor.execute("""SELECT * from user WHERE email = %s""", (email,))
            user = cursor.fetchone()
            session['user_id'] = user[1]
            return redirect('/home')


@app.route('/edit')
def edit():
    if 'user_id' in session:
        cursor.execute("""SELECT * FROM user WHERE username = %s""", (session['user_id'],))
        user = cursor.fetchone()
        return render_template('edit_user.html', user=user)


@app.route('/edit_user', methods=['POST'])
def edit_user():
    username = request.form.get('username')
    lastName = request.form.get('lastname')
    firstName = request.form.get('firstname')
    gender = request.form.get('gender')
    email = request.form.get('email')
    password = request.form.get('password')
    genre = request.form.get('genre')
    cursor.execute(
        """UPDATE user SET username = %s, lastName = %s, firstName = %s, gender = %s, email = %s, password = %s, genre = %s WHERE username = %s""",
        (username, lastName, firstName, gender, email, password, genre, session['user_id'],))
    conn.commit()
    return redirect('/account')


@app.route('/logout')
def logout():
    session.pop('user_id')
    return redirect('/')


# --------------------------------------------------
# Movie Module


@app.route('/movie')
def movie():
    cursor.execute("""SELECT * FROM movie ORDER BY MovieName""")
    movies = cursor.fetchall()
    if 'user_id' in session:
        return render_template('user_movie.html', movies=movies)
    else:
        return render_template('movie.html', movies=movies)


@app.route('/movieDetail')
def movieDetail():
    if 'view' in request.args:
        movie_id = request.args['view']
        cursor.execute("""SELECT * FROM movie WHERE MovieName = %s""", (movie_id,))
        target_movie = cursor.fetchone()
        cursor.execute("""SELECT r.* FROM movie AS m JOIN moviereview AS r ON m.MovieName = r.movieName WHERE m.MovieName = %s ORDER BY r.date DESC""",(movie_id,))
        reviews = cursor.fetchall()
        if 'user_id' in session:
            return render_template('user_view_details.html', movie=target_movie, reviews=reviews)
        else:
            return render_template('view_details.html', movie=target_movie, reviews=reviews)


@app.route('/search', methods=['POST'])
def search_movie():
    movieName = request.form['movieName']
    likeString = "%" + movieName + "%"
    cursor.execute("""SELECT * FROM movie WHERE MovieName LIKE %s""", (likeString,))
    movie_match = cursor.fetchall()
    if 'user_id' in session:
        return render_template('user_movie.html', movies=movie_match)
    else:
        return render_template('movie.html', movies=movie_match)


@app.route('/mostRecommended')
def recommended():
    msg = ' / Browse By'
    value = 'Most Recommended'
    cursor.execute("""SELECT * FROM movie AS m JOIN sentimentreview AS s on m.MovieName = s.movieName WHERE label='1' GROUP BY s.movieName ORDER BY COUNT(label) DESC""")
    movie_match = cursor.fetchall()
    if 'user_id' in session:
        return render_template('user_movie.html', movies=movie_match, msg1=msg, msg2=value)
    else:
        return render_template('movie.html', movies=movie_match, msg1=msg, msg2=value)


@app.route('/recentReleased')
def recentReleased():
    msg = ' / Browse By'
    value = 'Recently Released'
    cursor.execute("""SELECT * FROM movie ORDER BY YearReleased DESC""")
    movie_match = cursor.fetchall()
    if 'user_id' in session:
        return render_template('user_movie.html', movies=movie_match, msg1=msg, msg2=value)
    else:
        return render_template('movie.html', movies=movie_match, msg1=msg, msg2=value)


@app.route('/IMDBrating')
def imdbRating():
    msg = ' / Browse By'
    value = 'IMDB Rating'
    cursor.execute("""SELECT * FROM movie ORDER BY MovieRating DESC""")
    movie_match = cursor.fetchall()
    if 'user_id' in session:
        return render_template('user_imdb_filter.html', movies=movie_match, msg1=msg, msg2=value)
    else:
        return render_template('imdb_filter.html', movies=movie_match, msg1=msg, msg2=value)


@app.route('/action')
def action():
    msg = ' / Genre'
    value = 'Action'
    cursor.execute("""SELECT * FROM movie WHERE MovieGenre = %s""", (value,))
    movie_match = cursor.fetchall()
    if 'user_id' in session:
        return render_template('user_movie.html', movies=movie_match, msg1=msg, msg2=value)
    else:
        return render_template('movie.html', movies=movie_match, msg1=msg, msg2=value)


@app.route('/adventure')
def adventure():
    msg = ' / Genre'
    value = 'Adventure'
    cursor.execute("""SELECT * FROM movie WHERE MovieGenre = %s""", (value,))
    movie_match = cursor.fetchall()
    if 'user_id' in session:
        return render_template('user_movie.html', movies=movie_match, msg1=msg, msg2=value)
    else:
        return render_template('movie.html', movies=movie_match, msg1=msg, msg2=value)


@app.route('/animation')
def animation():
    msg = ' / Genre'
    value = 'Animation'
    cursor.execute("""SELECT * FROM movie WHERE MovieGenre = %s""", (value,))
    movie_match = cursor.fetchall()
    if 'user_id' in session:
        return render_template('user_movie.html', movies=movie_match, msg1=msg, msg2=value)
    else:
        return render_template('movie.html', movies=movie_match, msg1=msg, msg2=value)


@app.route('/biography')
def biography():
    msg = ' / Genre'
    value = 'Biography'
    cursor.execute("""SELECT * FROM movie WHERE MovieGenre = %s""", (value,))
    movie_match = cursor.fetchall()
    if 'user_id' in session:
        return render_template('user_movie.html', movies=movie_match, msg1=msg, msg2=value)
    else:
        return render_template('movie.html', movies=movie_match, msg1=msg, msg2=value)


@app.route('/comedy')
def comedy():
    msg = ' / Genre'
    value = 'Comedy'
    cursor.execute("""SELECT * FROM movie WHERE MovieGenre = %s""", (value,))
    movie_match = cursor.fetchall()
    if 'user_id' in session:
        return render_template('user_movie.html', movies=movie_match, msg1=msg, msg2=value)
    else:
        return render_template('movie.html', movies=movie_match, msg1=msg, msg2=value)


@app.route('/crime')
def crime():
    msg = ' / Genre'
    value = 'Crime'
    cursor.execute("""SELECT * FROM movie WHERE MovieGenre = %s""", (value,))
    movie_match = cursor.fetchall()
    if 'user_id' in session:
        return render_template('user_movie.html', movies=movie_match, msg1=msg, msg2=value)
    else:
        return render_template('movie.html', movies=movie_match, msg1=msg, msg2=value)


@app.route('/drama')
def drama():
    msg = ' / Genre'
    value = 'Drama'
    cursor.execute("""SELECT * FROM movie WHERE MovieGenre = %s""", (value,))
    movie_match = cursor.fetchall()
    if 'user_id' in session:
        return render_template('user_movie.html', movies=movie_match, msg1=msg, msg2=value)
    else:
        return render_template('movie.html', movies=movie_match, msg1=msg, msg2=value)


@app.route('/horror')
def horror():
    msg = ' / Genre'
    value = 'Horror'
    cursor.execute("""SELECT * FROM movie WHERE MovieGenre = %s""", (value,))
    movie_match = cursor.fetchall()
    if 'user_id' in session:
        return render_template('user_movie.html', movies=movie_match, msg1=msg, msg2=value)
    else:
        return render_template('movie.html', movies=movie_match, msg1=msg, msg2=value)


@app.route('/romance')
def romance():
    msg = ' / Genre'
    value = 'Romance'
    cursor.execute("""SELECT * FROM movie WHERE MovieGenre = %s""", (value,))
    movie_match = cursor.fetchall()
    if 'user_id' in session:
        return render_template('user_movie.html', movies=movie_match, msg1=msg, msg2=value)
    else:
        return render_template('movie.html', movies=movie_match, msg1=msg, msg2=value)


@app.route('/year1')
def year1():
    msg = '/ Year Released'
    value = '2020 - 2022'
    cursor.execute("""SELECT * FROM movie WHERE YearReleased IN ('2020','2021','2022')""")
    movie_match = cursor.fetchall()
    if 'user_id' in session:
        return render_template('user_movie.html', movies=movie_match, msg1=msg, msg2=value)
    else:
        return render_template('movie.html', movies=movie_match, msg1=msg, msg2=value)


@app.route('/year2')
def year2():
    msg = '/ Year Released'
    value = '2015 - 2019'
    cursor.execute("""SELECT * FROM movie WHERE YearReleased IN ('2019','2018','2017','2016','2015')""")
    movie_match = cursor.fetchall()
    if 'user_id' in session:
        return render_template('user_movie.html', movies=movie_match, msg1=msg, msg2=value)
    else:
        return render_template('movie.html', movies=movie_match, msg1=msg, msg2=value)


@app.route('/year3')
def year3():
    msg = '/ Year Released'
    value = '2010 - 2014'
    cursor.execute("""SELECT * FROM movie WHERE YearReleased IN ('2014','2013','2012','2011','2010')""")
    movie_match = cursor.fetchall()
    if 'user_id' in session:
        return render_template('user_movie.html', movies=movie_match, msg1=msg, msg2=value)
    else:
        return render_template('movie.html', movies=movie_match, msg1=msg, msg2=value)


@app.route('/year4')
def year4():
    msg = '/ Year Released'
    value = '2005 - 2009'
    cursor.execute("""SELECT * FROM movie WHERE YearReleased IN ('2009','2008','2007','2006','2005')""")
    movie_match = cursor.fetchall()
    if 'user_id' in session:
        return render_template('user_movie.html', movies=movie_match, msg1=msg, msg2=value)
    else:
        return render_template('movie.html', movies=movie_match, msg1=msg, msg2=value)


# --------------------------------------------------
# Watchlist Module
@app.route('/watchlist')
def watchlist():
    if 'user_id' in session:
        cursor.execute(
            """SELECT DISTINCT m.* FROM watchlist AS w JOIN movie AS m ON w.movieName = m.MovieName WHERE username = %s""",
            (session['user_id'],))
        movies = cursor.fetchall()
        return render_template('user_watchlist.html', movies=movies)
    else:
        return render_template('watchlist.html')


@app.route('/watchlistAdd')
def watchlist_add():
    if 'view' in request.args:
        if 'user_id' in session:
            movie_id = request.args['view']
            cursor.execute("""INSERT INTO watchlist(username,movieName) VALUES (%s,%s)""",
                           (session['user_id'], movie_id,))
            conn.commit()
            msg = "Added to watchlist successfully!"
            cursor.execute("""SELECT * FROM movie WHERE MovieName = %s""", (movie_id,))
            target_movie = cursor.fetchone()
            cursor.execute("""SELECT r.* FROM movie AS m JOIN moviereview AS r ON m.MovieName = r.movieName WHERE m.MovieName = %s ORDER BY r.date DESC""",(movie_id,))
            reviews = cursor.fetchall()
            return render_template('user_view_details.html', msg=msg, movie=target_movie, reviews=reviews)
        else:
            movie_id = request.args['view']
            msg = "Please login firstly!"
            cursor.execute("""SELECT * FROM movie WHERE MovieName = %s""", (movie_id,))
            target_movie = cursor.fetchone()
            cursor.execute("""SELECT r.* FROM movie AS m JOIN moviereview AS r ON m.MovieName = r.movieName WHERE m.MovieName = %s ORDER BY r.date DESC""",(movie_id,))
            reviews = cursor.fetchall()
            return render_template('view_details.html', msg=msg, movie=target_movie, reviews=reviews)


@app.route('/movieDetailRemove')
def watchlist_remove_detail():
    if 'view' in request.args:
        movie_id = request.args['view']
        cursor.execute("""SELECT * FROM movie WHERE MovieName = %s""", (movie_id,))
        target_movie = cursor.fetchone()
        cursor.execute("""SELECT r.* FROM movie AS m JOIN moviereview AS r ON m.MovieName = r.movieName WHERE m.MovieName = %s ORDER BY r.date DESC""",(movie_id,))
        reviews = cursor.fetchall()
        if 'user_id' in session:
            return render_template('user_watchlist_remove.html', movie=target_movie, reviews=reviews)


@app.route('/addComment',methods=['POST'])
def add_comment():
    if request.method == 'POST' and 'view' in request.args:
        movie_id = request.args['view']
        cursor.execute("""SELECT * FROM movie WHERE MovieName = %s""", (movie_id,))
        target_movie = cursor.fetchone()
        cursor.execute("""SELECT r.* FROM movie AS m JOIN moviereview AS r ON m.MovieName = r.movieName WHERE m.MovieName = %s ORDER BY r.date DESC""",(movie_id,))
        reviews = cursor.fetchall()
        warning_msg = "Please login firstly!"
        return render_template('view_details.html', movie=target_movie, reviews=reviews, warning_msg=warning_msg)


@app.route('/userAddComment',methods=['POST'])
def user_add_comment():
    if request.method == 'POST' and 'view' in request.args:
        name = request.form.get('username')
        comment = request.form.get('comment')
        movie_id = request.args['view']
        now = datetime.datetime.today()
        cursor.execute("""SELECT * FROM movie WHERE MovieName = %s""", (movie_id,))
        target_movie = cursor.fetchone()
        cursor.execute("""SELECT r.* FROM movie AS m JOIN moviereview AS r ON m.MovieName = r.movieName WHERE m.MovieName = %s ORDER BY r.date DESC""",(movie_id,))
        reviews = cursor.fetchall()
        cursor.execute("""SELECT * FROM moviereview WHERE username = %s AND movieName = %s""",(name,movie_id,))
        user_comment = cursor.fetchall()
        if user_comment:
            warning_msg = "You have reviewed this movie!"
            return render_template('user_view_details.html', movie=target_movie, reviews=reviews,warning_msg=warning_msg)
        else:
            cursor.execute("""INSERT INTO moviereview(username,movieName,Review,date) VALUES (%s,%s,%s,%s)""",
                           (name, movie_id, comment, now,))
            conn.commit()
            warning_msg = "Your review has been saved!! "
            return render_template('user_view_details.html', movie=target_movie, reviews=reviews, warning_msg=warning_msg)


@app.route('/userWatchlistAddComment1',methods=['POST'])
def user_watchlist_add_comment1():
    if request.method == 'POST' and 'view' in request.args:
        name = request.form.get('name')
        comment = request.form.get('comment')
        movie_id = request.args['view']
        now = datetime.datetime.today()
        cursor.execute("""SELECT * FROM movie WHERE MovieName = %s""", (movie_id,))
        target_movie = cursor.fetchone()
        cursor.execute("""SELECT r.* FROM movie AS m JOIN moviereview AS r ON m.MovieName = r.movieName WHERE m.MovieName = %s ORDER BY r.date DESC""",(movie_id,))
        reviews = cursor.fetchall()
        cursor.execute("""SELECT * FROM moviereview WHERE username = %s AND movieName = %s""",(name,movie_id,))
        user_comment = cursor.fetchall()
        if user_comment:
            warning_msg = "You have reviewed this movie!"
            return render_template('user_watchlist_remove.html', movie=target_movie, reviews=reviews, warning_msg=warning_msg)
        else:
            cursor.execute("""INSERT INTO moviereview(username,movieName,Review,date) VALUES (%s,%s,%s,%s)""",
                           (name, movie_id, comment, now,))
            conn.commit()
            warning_msg = "Thank you for your review! Your review has been saved!! "
            return render_template('user_watchlist_remove.html', movie=target_movie, reviews=reviews, warning_msg=warning_msg)


@app.route('/userWatchlistAddComment2',methods=['POST'])
def user_watchlist_add_comment2():
    if request.method == 'POST' and 'view' in request.args:
        name = request.form.get('name')
        comment = request.form.get('comment')
        movie_id = request.args['view']
        now = datetime.datetime.today()
        cursor.execute("""SELECT * FROM movie WHERE MovieName = %s""", (movie_id,))
        target_movie = cursor.fetchone()
        cursor.execute("""SELECT r.* FROM movie AS m JOIN moviereview AS r ON m.MovieName = r.movieName WHERE m.MovieName = %s ORDER BY r.date DESC""",(movie_id,))
        reviews = cursor.fetchall()
        cursor.execute("""SELECT * FROM moviereview WHERE username = %s AND movieName = %s""",(name,movie_id,))
        user_comment = cursor.fetchall()
        if user_comment:
            warning_msg = "You have reviewed this movie!"
            return render_template('redirect_watchlist.html', movie=target_movie, reviews=reviews, warning_msg=warning_msg)
        else:
            cursor.execute("""INSERT INTO moviereview(username,movieName,Review,date) VALUES (%s,%s,%s,%s)""",
                           (name, movie_id, comment, now,))
            conn.commit()
            warning_msg = "Thank you for your review! Your review has been saved!! "
            return render_template('redirect_watchlist.html', movie=target_movie, reviews=reviews, warning_msg=warning_msg)


@app.route('/watchlistRemove1')
def watchlist_remove1():
    if 'view' in request.args:
        if 'user_id' in session:
            movie_id = request.args['view']
            cursor.execute("""DELETE FROM watchlist WHERE username = %s AND MovieName = %s""",
                           (session['user_id'], movie_id,))
            conn.commit()
            cursor.execute(
                """SELECT m.* FROM watchlist AS w JOIN movie AS m ON w.movieName = m.MovieName WHERE username = %s""",
                (session['user_id'],))
            movies = cursor.fetchall()
            return render_template('user_watchlist.html', movies=movies)


@app.route('/watchlistRemove2')
def watchlist_remove2():
    if 'view' in request.args:
        if 'user_id' in session:
            movie_id = request.args['view']
            cursor.execute("""DELETE FROM watchlist WHERE username = %s AND MovieName = %s""",
                           (session['user_id'], movie_id,))
            conn.commit()
            msg = "Removed from watchlist successfully!"
            cursor.execute("""SELECT * FROM movie WHERE MovieName = %s""", (movie_id,))
            target_movie = cursor.fetchone()
            cursor.execute("""SELECT r.* FROM movie AS m JOIN moviereview AS r ON m.MovieName = r.movieName WHERE m.MovieName = %s ORDER BY r.date DESC""",(movie_id,))
            reviews = cursor.fetchall()
            return render_template('redirect_watchlist.html', msg=msg, movie=target_movie, reviews=reviews)

# --------------------------------------------------
# Sentiment Module
@app.route('/sentiment')
def sentiment():
    if 'user_id' in session:
        return render_template('user_sentiment.html')
    else:
        return render_template('sentiment.html')


@app.route('/sentiment', methods=['POST'])
def sentiment_post():
    text = request.form['review'].lower()
    stop_words = stopwords.words('english')
    processed_text = ' '.join([word for word in text.split() if word not in stop_words])
    score = TextBlob(processed_text).polarity

    if (score > 0):
        label = "This movie review is positive"
    elif (score == 0):
        label = "This movie review is neutral"
        score = '0'
    else:
        label = "This movie review is negative"

    if 'user_id' in session:
        return render_template('user_sentiment.html', final=score, variable=label)
    else:
        return render_template('sentiment.html', final=score, variable=label)


# --------------------------------------------------
# Feedback Module
@app.route('/feedback_get', methods=['POST'])
def feedback_post():
    email = request.form.get('email')
    feedbackType = request.form.get('feedbackType')
    description = request.form.get('description')
    cursor.execute("""INSERT INTO feedback (email, feedbackType, description) VALUES (%s,%s,%s)""",
                   (email, feedbackType, description))
    conn.commit()
    if 'user_id' in session:
        return render_template('user_home.html')
    else:
        return render_template('home.html')


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1')

