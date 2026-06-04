import sqlite3
import os

# Usa um nome diferente para evitar conflito com arquivo aberto
db_path = 'bd.sqlite3'
if os.path.exists(db_path):
    os.remove(db_path)
    print(f'Banco antigo "{db_path}" removido.')

# Cria o novo banco
conn = sqlite3.connect(db_path)
conn.execute('PRAGMA foreign_keys = ON')

with open('criar_banco_modelagem.sql', 'r', encoding='utf-8') as f:
    script = f.read()

conn.executescript(script)
print('Banco criado com sucesso!')

cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
print('Tabelas criadas:')
for row in cursor.fetchall():
    print(f'  - {row[0]}')

# Verificar foreign keys de cada tabela
print('\n--- Verificação de Foreign Keys ---')
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence' ORDER BY name")
for (table_name,) in cursor.fetchall():
    fk_cursor = conn.execute(f'PRAGMA foreign_key_list("{table_name}")')
    fks = fk_cursor.fetchall()
    if fks:
        print(f'\n  {table_name}:')
        for fk in fks:
            print(f'    {fk[3]} -> {fk[2]}({fk[4]})')

conn.close()
print(f'\nArquivo gerado: {os.path.abspath(db_path)}')
print(f'Tamanho: {os.path.getsize(db_path)} bytes')
