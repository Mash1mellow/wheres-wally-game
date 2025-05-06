import os
import random
import requests
from PIL import Image
from io import BytesIO
from flask import Flask, render_template, request, send_from_directory

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static'
app.config['PIXABAY_API_KEY'] = '49999731-63b76a3112e3bfd574ea17509'  # replace with your key

target_position = (0, 0)
target_size = (80, 80)

# === Fetch Decoy Images ===
def fetch_images(api_key, query="nature", count=99):
    url = f"https://pixabay.com/api/?key={api_key}&q={query}&image_type=photo&per_page={count}"
    res = requests.get(url).json()
    return [hit['largeImageURL'] for hit in res['hits']]

# === Download and Resize ===
def download_and_resize(urls, size):
    images = []
    for url in urls:
        try:
            img = Image.open(BytesIO(requests.get(url).content)).convert("RGB").resize(size)
            images.append(img)
        except: continue
    return images

# === Make Collage ===
def generate_collage(user_img_path, output_path):
    global target_position
    img_size = target_size
    padding = 10
    cols, rows = 10, 10
    canvas_w = cols * (img_size[0] + padding)
    canvas_h = rows * (img_size[1] + padding)

    collage = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))

    decoy_urls = fetch_images(app.config['PIXABAY_API_KEY'])
    decoys = download_and_resize(decoy_urls, img_size)
    target_img = Image.open(user_img_path).convert("RGB").resize(img_size)

    positions = [(x * (img_size[0] + padding), y * (img_size[1] + padding)) for y in range(rows) for x in range(cols)]
    random.shuffle(positions)

    for pos, decoy in zip(positions, decoys):
        collage.paste(decoy, pos)

    target_pos = positions[len(decoys)]
    collage.paste(target_img, target_pos)
    collage.save(output_path)

    target_position = target_pos

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['image']
        if file:
            user_path = os.path.join(app.config['UPLOAD_FOLDER'], 'target.jpg')
            file.save(user_path)

            output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'collage.jpg')
            generate_collage(user_path, output_path)

            return render_template('index.html', image='collage.jpg', show_result=False)

    return render_template('index.html')

@app.route('/click', methods=['POST'])
def check_click():
    global target_position, target_size
    x = int(request.form['x'])
    y = int(request.form['y'])

    tx, ty = target_position
    tw, th = target_size

    found = (tx <= x <= tx + tw and ty <= y <= ty + th)
    result = "🎯 You found Wally!" if found else "❌ Not Wally. Try again!"

    return render_template('index.html', image='collage.jpg', result=result, show_result=True)

@app.route('/static/<filename>')
def serve_file(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(debug=True)
