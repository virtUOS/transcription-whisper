import os
import subprocess
import requests

def download_youtube_video(youtube_link, download_path):
    # Ensure the directory exists
    os.makedirs(os.path.dirname(download_path), exist_ok=True)

    # Simulate the download process
    with open(download_path, 'wb') as f:
        f.write(b'Simulated file content')
    print(f"Downloaded file path: {download_path}")

def convert_audio(input_path, output_path):
    try:
        # Ensure absolute paths
        input_path = os.path.abspath(input_path)
        output_path = os.path.abspath(output_path)

        # Log the paths
        print(f"ffmpeg input path: {input_path}")
        print(f"ffmpeg output path: {output_path}")

        # Check if input file exists
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file does not exist: {input_path}")

        # Call ffmpeg
        result = subprocess.run(['ffmpeg', '-y', '-i', input_path, output_path], capture_output=True, text=True, check=True)
        print(f"ffmpeg output: {result.stdout}")
        print(f"ffmpeg error (if any): {result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg failed: {e.stderr}")
        raise
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

def process_youtube_link(youtube_link):
    # Simulate the download process, replace with actual download logic
    downloaded_file_path = "/tmp/E8RQVx2gBFc.webm"  # Simplified path for debugging
    temp_output_path = "/tmp/E8RQVx2gBFc.mp3"

    # Log the paths
    print(f"Downloaded file path: {downloaded_file_path}")
    print(f"Temporary output path: {temp_output_path}")

    # Download the file
    download_youtube_video(youtube_link, downloaded_file_path)

    # Ensure the download made the file available
    if not os.path.exists(downloaded_file_path):
        print(f"File not found after download: {downloaded_file_path}")
        return

    # Convert the audio
    convert_audio(downloaded_file_path, temp_output_path)

# Example usage
if __name__ == '__main__':
    youtube_link = "https://www.youtube.com/watch?v=E8RQVx2gBFc"
    process_youtube_link(youtube_link)
