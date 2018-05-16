from importlib import import_module
import os
from flask import Flask, render_template, Response, request, send_from_directory
from werkzeug.utils import secure_filename
from tunes_operate import operate_snapshot, operate_makemovie
# import camera driver
if os.environ.get('CAMERA'):
    Camera = import_module('camera_' + os.environ['CAMERA']).Camera
else:
    from camera import Camera

# Raspberry Pi camera module (requires picamera package)
# from camera_pi import Camera

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','avi'])


@app.route('/', methods=['GET'])
def index():
    """Video streaming home page."""
    if request.method == 'GET':
        values = request.values
        # 。。。
        if values.get('snapshot'):
            operate_snapshot()
        if values.get('makemovie'):
            operate_makemovie()
    return render_template('index.html')


def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    snapshots = list()
    videos = list()
    if request.method == 'POST':
        files = request.files.getlist('images')
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
            else:
                continue
            # 如果是截图则放到截图文件夹里面 //还没补充完整
            if filename.split('.')[-1]:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'] + 'snapshot/', filename))
            elif filename.rsplit('.', 1)[1] == 'avi':
                file.save(os.path.join(app.config['UPLOAD_FOLDER'] + 'video/', filename))
            else:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'] + 'videoFrames/', filename))
    if request.method == 'GET':
        snapshots = os.listdir(app.config['UPLOAD_FOLDER'] + 'snapshot/')
        videos = os.listdir(app.config['UPLOAD_FOLDER'] + 'video/')
    return render_template('upload.html', snapshots=snapshots, videos= videos)


@app.route('/uploads/<snapshot>')
def uploaded_snapshot(snapshot):
    return send_from_directory(app.config['UPLOAD_FOLDER'] + 'snapshot/', snapshot)

@app.route('/uploads/<video>')
def uploaded_video(video):
    return send_from_directory(app.config['UPLOAD_FOLDER'] + 'video/', video)

if __name__ == '__main__':
    app.run(host='127.0.0.1', threaded=True)
