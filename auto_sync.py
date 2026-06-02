import os
import time
from app import create_app, db
from app.models import Document, Sector, User
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class SyncHandler(FileSystemEventHandler):
    def __init__(self, sector_id, admin_id, upload_folder):
        self.sector_id = sector_id
        self.admin_id = admin_id
        self.upload_folder = upload_folder

    def on_created(self, event):
        if not event.is_directory:
            filename = os.path.basename(event.src_path)
            if filename.startswith('.') or filename == 'metadados.json':
                return
            
            # Simple sync logic: if a file is dropped in a monitored folder, 
            # we move it to the secure upload folder and register in DB.
            unique_filename = f"sync_{int(time.time())}_{filename}"
            dest_path = os.path.join(self.upload_folder, unique_filename)
            
            try:
                os.rename(event.src_path, dest_path)
                
                with create_app().app_context():
                    doc = Document(
                        title=filename,
                        filename=unique_filename,
                        original_filename=filename,
                        description="Sincronizado automaticamente.",
                        sector_id=self.sector_id,
                        user_id=self.admin_id
                    )
                    db.session.add(doc)
                    db.session.commit()
                print(f"Sincronizado: {filename}")
            except Exception as e:
                print(f"Erro ao sincronizar {filename}: {e}")

def start_sync():
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("Erro: Usuário admin não encontrado. Execute migrate_to_db.py primeiro.")
            return

        sectors = Sector.query.all()
        upload_folder = app.config['UPLOAD_FOLDER']
        
        # Monitor a special 'sync_inbox' folder or the old static folders
        sync_base = 'sync_inbox'
        if not os.path.exists(sync_base):
            os.makedirs(sync_base)
            
        observer = Observer()
        for sector in sectors:
            sector_path = os.path.join(sync_base, sector.name)
            if not os.path.exists(sector_path):
                os.makedirs(sector_path)
            
            handler = SyncHandler(sector.id, admin.id, upload_folder)
            observer.schedule(handler, sector_path, recursive=False)
            print(f"Monitorando: {sector_path}")

        observer.start()
        print("Serviço de Sincronização Automática iniciado. Pressione Ctrl+C para parar.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

if __name__ == '__main__':
    # You need to install watchdog: pip install watchdog
    start_sync()
