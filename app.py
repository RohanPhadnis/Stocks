import os
import pickle
import time
import yfinance as yf
from bson import ObjectId
from flask import *
from flask_pymongo import PyMongo
from util import *

app = Flask('app')
app.config['MONGO_URI'] = 'mongodb+srv://anyone:xyz@flask.ngjrl.mongodb.net/Stocks?retryWrites=true&w=majority'
mongo = PyMongo(app)
LOCK = 15 * 60
ADMIN_PASS = 'XYZ'


@app.route('/', methods=['GET'])
def home():
    if request.method == 'GET':
        user = list(mongo.db.session.find({'ip': request.remote_addr}))
        if len(user) > 0:
            identity = user[0]['_id']
        else:
            identity = 'null'
        return render_template('home.html', identity=identity)


def format_data(raw):
    raw_open, raw_close, raw_high, raw_low = raw['Open'], raw['Close'], raw['High'], raw['Low']
    data = []
    i = 0
    for key in raw_open.keys():
        data.append({
            'index': i,
            'day': key.day,
            'month': key.month,
            'year': key.year,
            'open': raw_open[key],
            'close': raw_close[key],
            'high': raw_high[key],
            'low': raw_low[key]
        })
        i += 1
    return data


@app.route('/view/<identity>', methods=['GET', 'POST'])
def view(identity):
    if request.method == 'GET':
        if identity == 'null':
            return redirect('/login')
        user = list(mongo.db.session.find({'_id': ObjectId(identity)}))
        if len(user) == 0:
            return redirect('/login')
        elif time.time() - user[0]['time'] > LOCK:
            return redirect('/login')
        else:
            return render_template('view.html', identity=identity, symbol='null', data=[])
    elif request.method == 'POST':
        form = dict(request.form)
        form['symbol'] = form['symbol'].upper()
        files = os.listdir()
        ticker = yf.Ticker(form['symbol'])
        if 'longName' not in list(ticker.get_info().keys()):
            return render_template('view.html', identity=identity, data=[], msg='could not find symbol', display=True)
        else:
            raw = dict(ticker.history(period='max'))
            if form['symbol'] not in files:
                os.mkdir(form['symbol'])
                open('{}/data.txt'.format(form['symbol']), 'x')
            with open('{}/data.txt'.format(form['symbol']), 'wb') as file:
                pickle.dump(raw, file)
            data = format_data(raw)
            return render_template('view.html', identity=identity, symbol=form['symbol'], data=data, name=ticker.get_info()['longName'], display=False)


@app.route('/predict/<identity>/<symbol>', methods=['GET'])
def predict_request(identity, symbol):
    if request.method == 'GET':
        user = list(mongo.db.session.find({'_id': ObjectId(identity)}))
        if len(user) == 0:
            return redirect('/login')
        user = user[0]
        if time.time() - user['time'] > LOCK:
            return redirect('/login')
        files = os.listdir()
        if symbol in files:
            mongo.db.predict.insert_one({'symbol': symbol})
        return redirect('/view/{}'.format(identity))


@app.route('/forum/<identity>', methods=['GET', 'POST'])
def forum(identity):
    if request.method == 'GET':
        if identity == 'null':
            return redirect('/login')
        user = list(mongo.db.session.find({'_id': ObjectId(identity)}))
        if len(user) == 0:
            return redirect('/login')
        elif time.time() - user[0]['time'] > LOCK:
            mongo.db.session.delete_one({'_id': identity})
            return redirect('/login')
        else:
            t = list(mongo.db.threads.find({}))
            return render_template('forum.html', identity=identity, data=t)
    elif request.method == 'POST':
        user = list(mongo.db.session.find({'_id': ObjectId(identity)}))[0]['user']
        form = dict(request.form)
        tf = TimeForm(time.time())
        tf = tf.cumulative()
        obj = {'text': form['comment'], 'user': user, 'time': time.time(), 'is_sub': False, 'subs': [], 'likes': 0, 'dislikes': 0, 'container': None, 'date_time': '{}-{}-{} {}:{}{}'.format(tf['month'], tf['day'], tf['year'], tf['hour'], tf['minute'], tf['clock'])}
        mongo.db.comments.insert_one(obj)
        i = list(mongo.db.comments.find(obj))[0]['_id']
        obj = {'title': form['title'], 'comments': [i], 'num': 1, 'date_time': '{}-{}-{} {}:{}{}'.format(tf['month'], tf['day'], tf['year'], tf['hour'], tf['minute'], tf['clock'])}
        mongo.db.threads.insert_one(obj)
        t = list(mongo.db.threads.find(obj))[0]
        mongo.db.comments.update_one({'container': None}, {'$set': {'container': t['_id']}})
        return redirect('/forum/{}'.format(identity))


@app.route('/thread/<identity>/<key>', methods=['GET', 'POST'])
def view_thread(identity, key):
    if request.method == 'GET':
        if identity == 'null':
            return redirect('/login')
        user = list(mongo.db.session.find({'_id': ObjectId(identity)}))
        if len(user) == 0:
            return redirect('/login')
        elif time.time() - user[0]['time'] > LOCK:
            mongo.db.session.delete_one({'_id': identity})
            return redirect('/login')
        else:
            t = list(mongo.db.threads.find({'_id': ObjectId(key)}))[0]
            data = []
            for c in t['comments']:
                comm = list(mongo.db.comments.find({'_id': c}))[0]
                comm['_id'] = str(comm['_id'])
                data.append(comm)
                if not comm['is_sub'] and len(comm['subs']) > 0:
                    for c2 in comm['subs']:
                        comm2 = list(mongo.db.comments.find({'_id': c2}))[0]
                        comm2['_id'] = str(comm2['_id'])
                        data.append(comm2)
            print(data)
            return render_template('thread.html', identity=identity, thread=t, data=data)
    elif request.method == 'POST':
        resp = dict(request.form)
        t = list(mongo.db.threads.find({'_id': ObjectId(key)}))[0]
        user = list(mongo.db.session.find({'_id': ObjectId(identity)}))[0]
        tf = TimeForm(time.time())
        tf = tf.cumulative()
        obj = {'text': resp['comment'], 'user': user['user'], 'time': time.time(), 'is_sub': False, 'subs': [], 'likes': 0, 'dislikes': 0, 'date_time': '{}-{}-{} {}:{}{}'.format(tf['month'], tf['day'], tf['year'], tf['hour'], tf['minute'], tf['clock'])}
        mongo.db.comments.insert_one(obj)
        comm = list(mongo.db.comments.find(obj))[0]
        t['comments'].append(comm['_id'])
        mongo.db.threads.update_one({'_id': t['_id']}, {'$set': {'num': t['num'] + 1, 'comments': t['comments']}})
        return redirect('/thread/{}/{}'.format(identity, key))


@app.route('/sub/<identity>/<thread_key>/<key>', methods=['POST'])
def sub_handler(identity, thread_key, key):
    if request.method == 'POST':
        resp = dict(request.form)
        user = list(mongo.db.session.find({'_id': ObjectId(identity)}))[0]
        tf = TimeForm(time.time())
        tf = tf.cumulative()
        obj = {'user': user['user'], 'time': time.time(), 'is_sub': True, 'subs': [], 'likes': 0, 'dislikes': 0, 'text': resp['text'], 'container': ObjectId(key), 'date_time': '{}-{}-{} {}:{}{}'.format(tf['month'], tf['day'], tf['year'], tf['hour'], tf['minute'], tf['clock'])}
        mongo.db.comments.insert_one(obj)
        comm = list(mongo.db.comments.find({'_id': ObjectId(key)}))[0]
        comm2 = list(mongo.db.comments.find(obj))[0]
        comm['subs'].append(comm2['_id'])
        mongo.db.comments.update_one({'_id': comm['_id']}, {'$set': {'subs': comm['subs']}})
        t = list(mongo.db.threads.find({'_id': ObjectId(thread_key)}))[0]
        mongo.db.threads.update_one({'_id': t['_id']}, {'$set': {'num': t['num'] + 1}})
        return redirect('/thread/{}/{}'.format(identity, thread_key))


@app.route('/like/<identity>/<thread_key>/<key>', methods=['GET'])
def like(identity, thread_key, key):
    if request.method == 'GET':
        comm = list(mongo.db.comments.find({'_id': ObjectId(key)}))[0]
        mongo.db.comments.update_one({'_id': comm['_id']}, {'$set': {'likes': comm['likes'] + 1}})
        return redirect('/thread/{}/{}'.format(identity, thread_key))


@app.route('/dislike/<identity>/<thread_key>/<key>', methods=['GET'])
def dislike(identity, thread_key, key):
    if request.method == 'GET':
        comm = list(mongo.db.comments.find({'_id': ObjectId(key)}))[0]
        mongo.db.comments.update_one({'_id': comm['_id']}, {'$set': {'dislikes': comm['dislikes'] + 1}})
        return redirect('/thread/{}/{}'.format(identity, thread_key))


@app.route('/access/<identity>', methods=['GET', 'POST'])
def access(identity):
    if request.method == 'GET':
        if identity == 'null':
            return redirect('/login')
        user = list(mongo.db.session.find({'_id': ObjectId(identity)}))
        if len(user) == 0:
            return redirect('/login')
        user = user[0]
        if time.time() - user['time'] > LOCK:
            return redirect('/login')
        if user['admin']:
            return redirect('/admin/{}'.format(identity))
        return render_template('access.html', identity=identity, display=False)
    elif request.method == 'POST':
        form = dict(request.form)
        if form['pass'] == ADMIN_PASS:
            mongo.db.session.update_one({'_id': ObjectId(identity)}, {'$set': {'admin': True}})
            return redirect('/admin/{}'.format(identity))
        return render_template('access.html', msg='incorrect password', identity=identity, display=True)


@app.route('/admin/<identity>', methods=['GET'])
def admin(identity):
    if request.method == 'GET':
        if identity == 'null':
            return redirect('/login')
        user = list(mongo.db.session.find({'_id': ObjectId(identity)}))
        if len(user) == 0:
            return redirect('/login')
        user = user[0]
        if time.time() - user['time'] > LOCK:
            return redirect('/login')
        if not user['admin']:
            return redirect('/access/{}'.format(identity))
        users = list(mongo.db.user.find({}))
        sessions = list(mongo.db.session.find({}))
        threads = list(mongo.db.threads.find({}))
        comments = list(mongo.db.comments.find({}))
        new_comments = []
        for i, t in enumerate(threads):
            threads[i]['index'] = i + 1
            c_num = 1
            for j, comm in enumerate(t['comments']):
                for k, comm2 in enumerate(comments):
                    if comm2['_id'] == comm:
                        comments[k]['index'] = c_num
                        comments[k]['thread_index'] = i + 1
                        new_comments.append(comments[k])
                        c_num += 1
                        for sub in comments[k]['subs']:
                            for l, comm3 in enumerate(comments):
                                if comm3['_id'] == sub:
                                    comments[l]['index'] = c_num
                                    comments[l]['thread_index'] = i + 1
                                    new_comments.append(comments[l])
                                    c_num += 1
        pred = mongo.db.predict.find({})
        return render_template('admin.html', identity=identity, users=users, sessions=sessions, threads=threads, comments=new_comments, predict=pred)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', identity='null', display=False)
    elif request.method == 'POST':
        form = dict(request.form)
        user = list(mongo.db.user.find({'user': form['user']}))
        if len(user) == 0:
            return render_template('login.html', identity='null', msg='could not find username', display=True)
        else:
            user = user[0]
            if user['pass'] != form['pass']:
                return render_template('login.html', identity='null', msg='username and password do not match', display=True)
            else:
                mongo.db.session.delete_many({'user': form['user']})
                mongo.db.session.insert_one({'user': form['user'], 'time': time.time(), 'ip': request.remote_addr, 'admin': False})
                identity = list(mongo.db.session.find({'user': form['user']}))[0]['_id']
                return redirect('/view/{}'.format(identity))


@app.route('/tennis', methods=['GET'])
def tennis():
    return render_template('tennis.html')


@app.route('/reg', methods=['GET', 'POST'])
def reg():
    if request.method == 'GET':
        return render_template('reg.html', identity='null', display=False)
    elif request.method == 'POST':
        form = dict(request.form)
        users = list(mongo.db.user.find({'user': form['user']}))
        if len(users) > 0:
            return render_template('reg.html', identity='null', msg='username already exists', display=True)
        mongo.db.user.insert_one(form)
        mongo.db.session.insert_one({'user': form['user'], 'time': time.time(), 'ip': request.remote_addr, 'admin': False})
        identity = list(mongo.db.session.find({'user': form['user']}))[0]['_id']
        return redirect('/view/{}'.format(identity))


@app.route('/delete/<identity>/<col>/<key>', methods=['GET'])
def delete(identity, col, key):
    if request.method == 'GET':
        if identity == 'null':
            return redirect('/login')
        user = list(mongo.db.session.find({'_id': ObjectId(identity)}))
        if len(user) == 0:
            return redirect('/login')
        user = user[0]
        if time.time() - user['time'] > LOCK:
            return redirect('/login')
        if not user['admin']:
            return redirect('/access/{}'.format(identity))
        if col == 'comments':
            comm = list(mongo.db.comments.find({'_id': ObjectId(key)}))[0]
            if comm['is_sub']:
                comm_container = list(mongo.db.comments.find({'_id': comm['container']}))[0]
                comm_container['subs'].remove(comm['_id'])
                mongo.db.comments.update_one({'_id': comm_container['_id']}, {'$set': {'subs': comm_container['subs']}})
                thread = list(mongo.db.threads.find({'_id': comm_container['container']}))[0]
                thread['comments'].remove(comm['_id'])
                mongo.db.threads.update_one({'_id': thread['_id']}, {'$set': {'comments': thread['comments']}})
            else:
                thread = list(mongo.db.threads.find({'_id': comm['container']}))[0]
                thread['comments'].remove(comm['_id'])
                mongo.db.threads.update_one({'_id': thread['_id']}, {'$set': {'comments': thread['comments']}})
        exec("mongo.db."+ col +".delete_one({'_id': ObjectId('" + key + "')})")
        return redirect('/admin/{}'.format(identity))


if __name__ == '__main__':
    app.run(debug=True)
