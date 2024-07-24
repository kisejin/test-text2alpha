from flask import Flask

app = Flask(__name__)

# to connect redis
# use host "redis_app"
# use port "6379"
# use password "add_password_here"


@app.route("/")
def hello():
    return "Hello NGINX reverse proxy"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
