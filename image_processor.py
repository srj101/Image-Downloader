import os
import requests
from PIL import Image
from io import BytesIO
import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

# Pixabay API key
API_KEY = "47512298-52269222e6aa19ed58fe13d24"

# Function to get all image files
def get_image_files(directory):
    image_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.jpg', '.png')):
                image_files.append(os.path.join(root, file))
    return image_files

# Function to get image dimensions
def get_image_dimensions(image_path):
    with Image.open(image_path) as img:
        return img.size

# Search for images on Pixabay
def search_images_on_pixabay(keyword, min_width=0, min_height=0, per_page=40, total_images_needed=0):
    url = "https://pixabay.com/api/"
    params = {
        "key": API_KEY,
        "q": keyword,
        "image_type": "photo",
        "per_page": per_page,
        "safesearch": "true"
    }

    image_urls = []
    page = 1
    while len(image_urls) < total_images_needed:
        params["page"] = page
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            if data["hits"]:
                for hit in data["hits"]:
                    if hit["imageWidth"] >= min_width and hit["imageHeight"] >= min_height:
                        image_urls.append(hit["largeImageURL"])
            page += 1
        else:
            break

    return list(set(image_urls))  # Remove duplicates

# Generate a hash for an image
def hash_image(image):
    hasher = hashlib.sha256()
    hasher.update(image.tobytes())
    return hasher.hexdigest()

# Download an image
def download_image(image_url):
    response = requests.get(image_url)
    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    else:
        raise Exception(f"Failed to download image from {image_url}")

# Replicate directory structure
def replicate_directory_structure(input_dir, output_dir, file_path):
    relative_path = os.path.relpath(file_path, input_dir)
    output_path = os.path.join(output_dir, relative_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    return output_path

# Process images
def process_images(input_dir, output_dir, keyword, log_text):
    image_files = get_image_files(input_dir)

    if not image_files:
        messagebox.showerror("Error", "No image files found in the input directory.")
        return

    total_images_needed = len(image_files)
    log_text.insert(tk.END, f"Found {total_images_needed} images in input directory.\n")

    image_urls = search_images_on_pixabay(
        keyword, min_width=0, min_height=0, per_page=40, total_images_needed=total_images_needed)

    if not image_urls:
        messagebox.showerror("Error", f"No suitable images found for keyword '{keyword}'.")
        return

    processed_hashes = set()
    used_urls = set()

    for index, image_file in enumerate(image_files):
        try:
            width, height = get_image_dimensions(image_file)
            _, file_extension = os.path.splitext(image_file)
            file_extension = file_extension.lower()

            unique_url_found = False
            for image_url in image_urls:
                if image_url in used_urls:
                    continue
                original_image = download_image(image_url)
                image_hash = hash_image(original_image)

                if image_hash not in processed_hashes:
                    processed_hashes.add(image_hash)
                    used_urls.add(image_url)
                    unique_url_found = True
                    break

            if not unique_url_found:
                log_text.insert(tk.END, f"Skipped duplicate for {image_file}\n")
                continue

            resized_image = original_image.resize((width, height), Image.Resampling.LANCZOS)
            output_path = replicate_directory_structure(input_dir, output_dir, image_file)
            output_path = os.path.splitext(output_path)[0] + file_extension
            resized_image.save(output_path, format=resized_image.format)
            log_text.insert(tk.END, f"Processed {image_file} -> {output_path}\n")
            log_text.see(tk.END)

        except Exception as e:
            log_text.insert(tk.END, f"Error processing {image_file}: {e}\n")
            log_text.see(tk.END)

    messagebox.showinfo("Success", "Image processing completed!")

# GUI Implementation
def main_gui():
    def browse_input_dir():
        path = filedialog.askdirectory()
        if path:
            input_dir.set(path)

    def browse_output_dir():
        path = filedialog.askdirectory()
        if path:
            output_dir.set(path)

    def start_processing():
        input_path = input_dir.get()
        output_path = output_dir.get()
        keyword = keyword_entry.get()

        if not input_path or not output_path or not keyword:
            messagebox.showerror("Error", "All fields are required!")
            return

        log_text.delete(1.0, tk.END)
        process_images(input_path, output_path, keyword, log_text)

    # Create main window
    root = tk.Tk()
    root.title("Image Processor")
    root.geometry("600x500")

    # Variables
    input_dir = tk.StringVar()
    output_dir = tk.StringVar()

    # Layout
    tk.Label(root, text="Input Directory:").pack(pady=5)
    input_frame = tk.Frame(root)
    input_frame.pack(pady=5)
    tk.Entry(input_frame, textvariable=input_dir, width=50).pack(side=tk.LEFT, padx=5)
    tk.Button(input_frame, text="Browse", command=browse_input_dir).pack(side=tk.LEFT)

    tk.Label(root, text="Output Directory:").pack(pady=5)
    output_frame = tk.Frame(root)
    output_frame.pack(pady=5)
    tk.Entry(output_frame, textvariable=output_dir, width=50).pack(side=tk.LEFT, padx=5)
    tk.Button(output_frame, text="Browse", command=browse_output_dir).pack(side=tk.LEFT)

    tk.Label(root, text="Keyword for Pixabay Search:").pack(pady=5)
    keyword_entry = tk.Entry(root, width=50)
    keyword_entry.pack(pady=5)

    tk.Button(root, text="Start Processing", command=start_processing).pack(pady=10)

    tk.Label(root, text="Log:").pack(pady=5)
    log_text = scrolledtext.ScrolledText(root, height=15, width=70)
    log_text.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    main_gui()
