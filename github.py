import http.server
import socketserver
import requests
import networkx as nx


def get_data(username, endpoint, page=1, per_page=100):
    url = f'https://api.github.com/users/{username}/{endpoint}?page={page}&per_page={per_page}'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_following(username):
    following = []
    page = 1

    while True:
        data = get_data(username, 'following', page)
        if not data:
            break

        for user in data:
            following.append(user['login'])

        page += 1

    return following

def fetch_user(username):
    followers = get_data(username, 'followers')
    followings = get_data(username, 'following')

    return username, followers, followings

def create_network(usernames):
    grph = nx.DiGraph()

    for username in usernames:
        try:
            print(f'Fetching user data for {username}')
            username, followers, followings = fetch_user(username)
            grph.add_node(username)

            for follower in followers:
                name = follower['login']
                grph.add_node(name)
                grph.add_edge(name, username)

            for following in followings:
                name = following['login']
                grph.add_node(name)
                grph.add_edge(username, name)

        except Exception as e:
            print(f'Error ~> {e}')

    return grph

def recommender(grph, user):
    grph = grph.to_undirected()
    rcmnds = {}

    for node in grph.nodes:
        if node == user or grph.has_edge(user, node):
            continue

        neighbors = len(list(nx.common_neighbors(grph, user, node)))

        if neighbors > 0:
            rcmnds[node] = neighbors

    final_list = sorted(rcmnds.items(), key=lambda item: item[1], reverse=True)
    return final_list

class ServerSetup(http.server.BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path == '/':

            print(f'Received request for recommendations for user: {USERNAME}')
            followings = get_following(USERNAME)
            grph = create_network(followings + [USERNAME])
            recommended = recommender(grph, USERNAME)

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            self.wfile.write(b"""<html>
                                <head>
                                <title>GitHub Recommendations</title>
                                <style>
                                body { background-color: #1a1a1a; color: #fff; font-family: Arial, sans-serif; }
                                .card { background-color: #333; padding: 15px; margin: 10px; border-radius: 5px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); }
                                .avatar { width: 50px; height: 50px; border-radius: 50%; }
                                </style>
                                </head>
                                <body>""")
            
            self.wfile.write(f'<h1 style="text-align: center;">Suggested for {USERNAME}</h1>'.encode('utf-8'))
            self.wfile.write(b'<div style="display: flex; flex-wrap: wrap; justify-content: center;">')
            
            for user, score in recommended:
                user_data = get_data(user, f'../{user}')
                profile_link = user_data['html_url']
                profile_pic = user_data['avatar_url']

                img = f'<img src="{profile_pic}" alt="{user}" class="avatar">'

                self.wfile.write(b'<div class="card">')
                self.wfile.write(f'<a href="{profile_link}" style="color: #fff; text-decoration: none;">'.encode('utf-8'))
                self.wfile.write(f'{img} {user}</a>'.encode('utf-8'))
                self.wfile.write(b'</div>')

            self.wfile.write(b'</div></body></html>')


        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Not found.')


USERNAME = input("> Enter your GitHub username: ")
TOKEN = input(""">Enter your github Personal Access Token :
(you can get your own token from https://github.com/settings/tokens)
""")

headers = {'Authorization': f'token {TOKEN}'}

PORT = 8002
Handler = ServerSetup

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Server started on port {PORT}")
    print(f"Open this URL ~>  http://127.0.0.1:{PORT}")
    httpd.serve_forever()

