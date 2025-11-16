import os
import tempfile
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from sftp_client import SFTPConfig, list_files, upload_file, download_file

SFTP_HOST = os.getenv("SFTP_HOST", "your.sftp.host")
SFTP_PORT = os.getenv("SFTP_PORT", "22")
SFTP_USERNAME = os.getenv("SFTP_USERNAME", "username")
SFTP_PASSWORD = os.getenv("SFTP_PASSWORD", None)
SFTP_KEYFILE = os.getenv("SFTP_KEYFILE", None)
SFTP_REMOTE_DIR = os.getenv("SFTP_REMOTE_DIR", "/uploads")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-in-production")

sftp_config = SFTPConfig(
    host=SFTP_HOST,
    port=SFTP_PORT,
    username=SFTP_USERNAME,
    password=SFTP_PASSWORD,
    key_filename=SFTP_KEYFILE,
    remote_dir=SFTP_REMOTE_DIR,
)

@app.route("/", methods=["GET"])
def index():
    try:
        files = list_files(sftp_config)
    except Exception as e:
        flash(f"Failed to list remote files: {e}", "danger")
        files = []
    return render_template("index.html", files=files, remote_dir=sftp_config.remote_dir)

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file or file.filename == "":
        flash("No file selected.", "warning")
        return redirect(url_for("index"))

    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        upload_file(sftp_config, tmp_path, file.filename)
        flash(f"Uploaded '{file.filename}' to SFTP.", "success")
    except Exception as e:
        flash(f"Upload failed: {e}", "danger")
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

    return redirect(url_for("index"))

@app.route("/download/<path:filename>", methods=["GET"])
def download(filename):
    try:
        tmp_fd, tmp_path = tempfile.mkstemp()
        os.close(tmp_fd)
        download_file(sftp_config, filename, tmp_path)
        return send_file(tmp_path, as_attachment=True, download_name=filename)
    except Exception as e:
        flash(f"Download failed: {e}", "danger")
        return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
