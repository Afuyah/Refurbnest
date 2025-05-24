from app import create_app, db

app = create_app()

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=1000,
        debug=True,
        ssl_context='adhoc'  # This enables HTTPS with a temporary cert
    )
