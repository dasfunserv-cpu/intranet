import os
import json
import shutil
from app import create_app, db
from app.models import User, Sector, Category, Document
from datetime import datetime

def migrate_data():
    app = create_app()
    with app.app_context():
        # 1. Create all tables
        db.create_all()
        
        # 2. Get all directories in app/recados
        base_src = os.path.join('app', 'recados')
        if not os.path.exists(base_src):
            print(f"Erro: Pasta de origem {base_src} não encontrada.")
            return

        directories = [d for d in os.listdir(base_src) if os.path.isdir(os.path.join(base_src, d))]
        
        sector_map = {}
        for s_name in directories:
            sector = Sector.query.filter_by(name=s_name).first()
            if not sector:
                sector = Sector(name=s_name)
                db.session.add(sector)
                db.session.commit()
            sector_map[s_name] = sector.id
            
        # 3. Create a default admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@funserv.com', role='admin')
            admin.set_password('admin123') 
            db.session.add(admin)
            db.session.commit()
            
        # 4. Migrate files from app/recados to uploads/
        base_dest = app.config['UPLOAD_FOLDER']
        if not os.path.exists(base_dest):
            os.makedirs(base_dest)
        
        for sector_name in directories:
            sector_path = os.path.join(base_src, sector_name)
            s_id = sector_map[sector_name]
            
            # Load metadata
            meta_path = os.path.join(sector_path, 'metadados.json')
            metadata = {}
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                except Exception as e:
                    print(f"Erro ao ler metadados em {sector_path}: {e}")
            
            for filename in os.listdir(sector_path):
                if filename == 'metadados.json':
                    continue
                    
                src_file = os.path.join(sector_path, filename)
                if os.path.isdir(src_file):
                    continue

                # Avoid name collisions
                safe_filename = f"{int(datetime.now().timestamp())}_{filename}"
                dest_file = os.path.join(base_dest, safe_filename)
                
                try:
                    shutil.copy2(src_file, dest_file)
                    
                    # Add to DB
                    doc = Document(
                        title=filename,
                        filename=safe_filename,
                        original_filename=filename,
                        description=metadata.get(filename, ''),
                        sector_id=s_id,
                        user_id=admin.id
                    )
                    db.session.add(doc)
                    print(f"Migrado: {filename} ({sector_name})")
                except Exception as e:
                    print(f"Erro ao migrar {filename}: {e}")
            
        db.session.commit()
        print("\nMigração concluída com sucesso!")

if __name__ == '__main__':
    migrate_data()
