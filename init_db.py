import sqlite3

def criar_banco():
    conn = sqlite3.connect('intranet.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_arquivo TEXT NOT NULL,
            diretoria TEXT NOT NULL,
            descricao TEXT,
            data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    criar_banco()
    print("Banco de dados criado com sucesso!")

