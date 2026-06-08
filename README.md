# MyDrive


**Introduction**
---------------

MyDrive is a cloud storage service built using Django REST Framework (DRF) and Python 3.x. It provides features like file upload, folder creation, renaming, moving, and downloading files.

**Features**
-------------

*   User authentication through username and password
*   File upload with validation for file type and size
*   Folder creation and management with permission control
*   File renaming and moving within folders
*   Downloading files as zip archives

**Endpoints**
--------------

### User Endpoints

#### Retrieve a list of users

`GET /user/`

Returns a list of all registered users.

#### Retrieve a user by ID

`GET /user/{id}/`

Returns the details of a specific user.

#### Create a new user

`POST /user/`

Creates a new user with the provided credentials. The request body should contain `username` and `password` fields.

### File Endpoints

#### List all files in a folder

`GET /files/`

Returns a list of all files within the authenticated user's root directory. The query parameter `parent` can be used to filter files by their parent folder ID.

#### Create a new file

`POST /files/`

Creates a new file within the authenticated user's root directory. The request body should contain `name` and `file` fields. The `file` field should contain the uploaded file content.

#### Retrieve a file by ID

`GET /files/{id}/`

Returns the details of a specific file, including its name, parent folder, size, and upload date.

#### Rename a file

`PATCH /files/{id}/rename/`

Renames a file within the authenticated user's root directory. The request body should contain `name` field.

#### Move a file to another folder

`POST /files/{id}/move/`

Moves a file from its current parent folder to another folder within the authenticated user's root directory. The request body should contain `parent` field, which is the ID of the destination folder.

### Folder Endpoints

#### List all folders in a user's account

`GET /folders/`

Returns a list of all folders within the authenticated user's root directory. The query parameter `parent` can be used to filter folders by their parent folder ID.

#### Create a new folder

`POST /folders/`

Creates a new folder within the authenticated user's root directory. The request body should contain `name` field.

#### Retrieve a folder by ID

`GET /folders/{id}/`

Returns the details of a specific folder, including its name and parent folder.

#### Rename a folder

`PATCH /folders/{id}/rename/`

Renames a folder within the authenticated user's root directory. The request body should contain `name` field.

#### Move a folder to another location

`POST /folders/{id}/move/`

Moves a folder from its current parent folder to another folder within the authenticated user's root directory. The request body should contain `parent` field, which is the ID of the destination folder.

### Download Endpoints

#### Download a file as a zip archive

`GET /files/{id}/download/`

Downloads a specific file as a zip archive, including all its contents.

**Authentication**
-----------------

MyDrive API uses token-based authentication. To obtain an access token, you need to send a `POST` request with your credentials (username and password) to the `/login/` endpoint.

```bash
curl -X POST \
  http://localhost:8000/login/ \
  -H 'Content-Type: application/json' \
  -d '{"username": "your_username", "password": "your_password"}'
```

This will return a JSON response containing the access token, which you can use in subsequent requests by including it as an `Authorization` header.

```bash
curl -X GET \
  http://localhost:8000/files/ \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json'
```

