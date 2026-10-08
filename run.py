import os

from app import create_app

app = create_app()
#print("STATIC FOLDER:", app.static_folder)
if __name__ == "__main__":
    app.run(debug=True)

'''app.config['UPLOAD_FOLDER'] = os.path.join(
    app.static_folder,
    'uploads',
    'images'
)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

print("UPLOAD FOLDER:", app.config['UPLOAD_FOLDER'])'''