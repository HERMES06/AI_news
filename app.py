from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import subprocess
import threading
import time
import os

app = Flask(__name__)
app.secret_key = 'akshofnoanieldm2309nla09na902rl'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/form')
def form():
    source = request.args.get('source', 'unknown')
    return render_template('form.html', source=source)

@app.route('/submit', methods=['POST'])
def submit():
    gender = request.form.get('gender')
    politics = request.form.get('politics')
    age = request.form.get('age')
    source = request.form.get('source')
    
    if not age.isdigit() or int(age) < 17:
        flash('만 17세 미만은 이용할 수 없는 서비스입니다.')
        return redirect(url_for('form', source=source))
    
    if not gender or not politics or not source:
        flash('모든 필드를 채워주세요.')
        return redirect(url_for('form', source=source))

    task_id = 'v1'
    thread = threading.Thread(target=run_script, args=(task_id, source, gender, politics, age))
    thread.start()

    return render_template('loading.html', task_id=task_id)

@app.route('/runcode', methods=['POST'])
def run_script(task_id, source, gender, politics, age):
    status_file = f'task_status_v1.txt'
    video_filename = f'newsGenerator_v1.avi'
    with open(status_file, 'w', encoding='utf-8') as f:
        f.write('RUNNING')

    try:
        subprocess.run(['python', 'C:\\Users\\460_2\\OneDrive - 세종과학예술영재학교 (1)\\문서\\VScode\\coding\\python\\AI_Projects\\2024_AI_project_NewsCrolling\\script.py', source, gender, politics, age, video_filename], check=True)
        with open(status_file, 'w', encoding='utf-8') as f:
            f.write(f'SUCCESS:{video_filename}')
    except subprocess.CalledProcessError as e:
        with open(status_file, 'w', encoding='utf-8') as f:
            f.write('FAILED')


@app.route('/task_status/<task_id>')
def task_status(task_id):
    status_file = f'task_status_v1.txt'
    if os.path.exists(status_file):
        with open(status_file, 'r', encoding='utf-8') as f:
            status = f.read().strip()
        if status.startswith('SUCCESS'):
            _, video_filename = status.split(':')
            app.logger.info(f'Task v1 succeeded with file {video_filename}')
            return jsonify({'state': 'SUCCESS', 'video_filename': video_filename})
        app.logger.info(f'Task v1 status: v1')
        return jsonify({'state': status})
    app.logger.warning(f'Task v1 status unknown')
    return jsonify({'state': 'UNKNOWN'})


## real ##
@app.route('/success')
def success():
    video_filename = request.args.get('filename', 'default_video.mp4')
    return render_template('success.html', video_filename=video_filename)

## test ## 
# @app.route('/success')
# def success():
#     video_filename = 'newsGenerator_v1.avi'
#     return render_template('success.html', video_filename=video_filename)


@app.route('/dcinside')
def dcinside():
    return render_template('dcinside.html')

@app.route('/everytime')
def everytime():
    return render_template('everytime.html')

@app.route('/peverytime')
def peverytime():
    return render_template('everytime_privacy.html')

@app.route('/nate')
def nate():
    return render_template('nate.html')

@app.route('/pnate')
def pnate():
    return render_template('nate_privacy.html')

from flask import send_file


## real ##
@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join('C:\\Users\\460_2\\OneDrive - 세종과학예술영재학교 (1)\\문서\\VScode\\coding\\python\\AI_Projects\\2024_AI_project_NewsCrolling', filename), as_attachment=True)


## test ##
# @app.route('/download')
# def download():
#     file_path = 'C:\\Users\\460_2\\OneDrive - 세종과학예술영재학교 (1)\\문서\\VScode\\coding\\python\\newsGenerator_v1.avi'
#     if os.path.exists(file_path):
#         return send_file(file_path, as_attachment=True)
#     else:
#         return "File not found", 404


if __name__ == '__main__':
    app.run(debug=True)
