from app import create_app, db

app = create_app()

@app.route('/debug')
def debug():
    return "Flask is working!"

if __name__ == '__main__':
    with app.app_context():
        try:
            # Проверим подключение к БД
            from app.models import Employee
            db.create_all()
            print("Database tables created successfully")
        except Exception as e:
            print(f"Database error: {e}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)