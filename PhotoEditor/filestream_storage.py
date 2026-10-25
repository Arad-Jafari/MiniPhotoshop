import os
import re
import tempfile
import uuid
from datetime import datetime, timezone

import pyodbc
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage


class SqlServerFileStreamStorage(Storage):
    """Persist media in SQL Server FILESTREAM while keeping a temp copy for OpenCV processing."""

    table_name = 'Media'
    file_name_field = 'FileName'
    content_field = 'Content'
    created_field = 'CreationDateTime'
    stream_id_field = 'stream_id'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.local_root = os.path.join(tempfile.gettempdir(), 'MiniPhotoShopMedia')
        os.makedirs(self.local_root, exist_ok=True)

    def _temp_local_path(self, name):
        safe_name = os.path.basename(str(name).replace('\\', '/'))
        if not safe_name:
            safe_name = f'{uuid.uuid4().hex}.bin'
        return os.path.join(self.local_root, safe_name)

    def _write_local_temp(self, name, content_bytes):
        local_path = self._temp_local_path(name)
        with open(local_path, 'wb') as temp_file:
            temp_file.write(content_bytes)
        return local_path

    def _connection_string(self):
        db = settings.DATABASES.get('filestream', settings.DATABASES.get('default', {}))
        options = db.get('OPTIONS', {})
        host = db.get('HOST', '.')
        port = db.get('PORT', '')
        database = db.get('NAME')
        user = db.get('USER')
        password = db.get('PASSWORD')
        driver = options.get('driver', 'ODBC Driver 18 for SQL Server')

        conn = [
            f'DRIVER={{{driver}}};',
            f'SERVER={host};',
            f'DATABASE={database};',
        ]
        if port:
            conn.append(f'PORT={port};')
        if user:
            conn.append(f'UID={user};')
            conn.append(f'PWD={password or ""};')
        else:
            conn.append('Trusted_Connection=Yes;')

        if options.get('Encrypt') is not None:
            conn.append(f'Encrypt={options.get("Encrypt")};')
        if options.get('TrustServerCertificate') is not None:
            conn.append(f'TrustServerCertificate={options.get("TrustServerCertificate")};')
        return ''.join(conn)

    def _open_connection(self):
        return pyodbc.connect(self._connection_string(), autocommit=True)

    def _table_columns(self):
        with self._open_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ?",
                (self.table_name,),
            )
            return {row[0] for row in cursor.fetchall()}

    def _resolve_logical_name(self, name):
        clean_name = str(name).replace('\\', '/').lstrip('/')
        return clean_name or f'{uuid.uuid4().hex}.bin'

    def _stream_id_from_name(self, name):
        value = str(name or '').strip()
        match = re.search(r'([0-9a-fA-F-]{36})', value)
        return match.group(1) if match else None

    def _read_blob(self, name):
        columns = self._table_columns()
        if self.file_name_field in columns:
            sql = f"SELECT {self.content_field} FROM {self.table_name} WHERE {self.file_name_field} = ?"
            params = (self._resolve_logical_name(name),)
        else:
            stream_id = self._stream_id_from_name(name)
            if not stream_id:
                raise FileNotFoundError(f'No stored blob found for {name}')
            sql = f"SELECT {self.content_field} FROM {self.table_name} WHERE CAST({self.stream_id_field} AS NVARCHAR(36)) = ?"
            params = (stream_id,)

        with self._open_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            row = cursor.fetchone()
            if not row:
                raise FileNotFoundError(f'No stored blob found for {name}')
            value = row[0]
            if isinstance(value, memoryview):
                return value.tobytes()
            if isinstance(value, bytearray):
                return bytes(value)
            if value is None:
                return b''
            return bytes(value)

    def _exists_by_name(self, name):
        columns = self._table_columns()
        if self.file_name_field in columns:
            sql = f"SELECT 1 FROM {self.table_name} WHERE {self.file_name_field} = ?"
            params = (self._resolve_logical_name(name),)
        else:
            stream_id = self._stream_id_from_name(name)
            if not stream_id:
                return False
            sql = f"SELECT 1 FROM {self.table_name} WHERE CAST({self.stream_id_field} AS NVARCHAR(36)) = ?"
            params = (stream_id,)

        with self._open_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchone() is not None

    def _save_with_file_name(self, name, content_bytes):
        created = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')
        file_name = self._resolve_logical_name(name)
        with self._open_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"INSERT INTO {self.table_name} ({self.file_name_field}, {self.content_field}, {self.created_field}) VALUES (?, ?, ?)",
                (file_name, bytes(content_bytes), created),
            )
            conn.commit()
        return file_name

    def _save_without_file_name(self, name, content_bytes):
        unique_id = str(uuid.uuid4())
        created = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')
        with self._open_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"INSERT INTO {self.table_name} ({self.stream_id_field}, {self.content_field}, {self.created_field}) VALUES (?, ?, ?)",
                (unique_id, bytes(content_bytes), created),
            )
            conn.commit()
        return unique_id

    def open(self, name, mode='rb'):
        temp_path = self._temp_local_path(name)
        if os.path.exists(temp_path):
            return open(temp_path, mode)
        file_bytes = self._read_blob(name)
        with open(temp_path, 'wb') as temp_file:
            temp_file.write(file_bytes)
        return open(temp_path, mode)

    def save(self, name, content, max_length=None):
        content_bytes = content.read() if hasattr(content, 'read') else content
        if not content_bytes:
            raise ValueError('Cannot save empty file content to SQL Server FILESTREAM.')

        self._write_local_temp(name, content_bytes)

        columns = self._table_columns()
        if self.file_name_field in columns:
            return self._save_with_file_name(name, content_bytes)
        return self._save_without_file_name(name, content_bytes)

    def delete(self, name):
        columns = self._table_columns()
        if self.file_name_field in columns:
            sql = f"DELETE FROM {self.table_name} WHERE {self.file_name_field} = ?"
            params = (self._resolve_logical_name(name),)
        else:
            stream_id = self._stream_id_from_name(name)
            if not stream_id:
                return False
            sql = f"DELETE FROM {self.table_name} WHERE CAST({self.stream_id_field} AS NVARCHAR(36)) = ?"
            params = (stream_id,)

        with self._open_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
        return True

    def exists(self, name):
        return self._exists_by_name(name)

    def url(self, name):
        url_name = str(name).replace('\\', '/').lstrip('/')
        return f'{settings.MEDIA_URL}{url_name}'

    def path(self, name):
        temp_path = self._temp_local_path(name)
        if os.path.exists(temp_path):
            return temp_path
        blob = self._read_blob(name)
        with open(temp_path, 'wb') as temp_file:
            temp_file.write(blob)
        return temp_path

    def size(self, name):
        return len(self._read_blob(name))

    def _open(self, name, mode='rb'):
        return ContentFile(self._read_blob(name), name=name)
