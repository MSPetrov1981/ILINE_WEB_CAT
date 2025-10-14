from app import create_app, db
from app.models import User, Employee

app = create_app()

@app.cli.command("create-admin")
def create_admin():
    """Создание администратора"""
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Администратор создан: admin / admin123")

if __name__ == '__main__':
    with app.app_context():
        # Создаем таблицы
        db.create_all()
        
        # Создаем администратора если нет пользователей
        if User.query.count() == 0:
            admin = User(username='admin', email='admin@example.com')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Администратор по умолчанию создан: admin / admin123")
    
    app.run(debug=True, host='0.0.0.0', port=5000)