import os
import subprocess
import requests


def download_youtube_video(youtube_link, download_path):
    # Clean up any previous files
    if os.path.exists(download_path):
        os.remove(download_path)

    # Use an actual downloadable file for testing
    video_url = "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
    response = requests.get(video_url)

    # Log the HTTP status code
    print(f"Download HTTP status code: {response.status_code}")

    if response.status_code == 200:
        with open(download_path, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded file path: {download_path}")
    else:
        print(f"Download failed with status code {response.status_code}")
        return False

    # Check if file exists immediately after writing
    if os.path.exists(download_path):
        print(f"File exists after download: {download_path}")
        print(f"File size: {os.path.getsize(download_path)} bytes")
    else:
        print(f"File does not exist after download attempt: {download_path}")
        return False

    return True


def convert_audio(input_path, output_path):
    try:
        # Ensure absolute paths
        input_path = os.path.abspath(input_path)
        output_path = os.path.abspath(output_path)

        # Log the paths
        print(f"ffmpeg input path: {input_path}")
        print(f"ffmpeg output path: {output_path}")

        # Full path to ffmpeg
        ffmpeg_path = "/snap/bin/ffmpeg"

        # Check if input file exists
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file does not exist: {input_path}")

        # Call ffmpeg with full path
        result = subprocess.run([ffmpeg_path, '-y', '-i', input_path, '-vn', '-acodec', 'libmp3lame', output_path],
                                capture_output=True, text=True, check=True)
        print(f"ffmpeg output: {result.stdout}")
        print(f"ffmpeg error (if any): {result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg failed: {e.stderr}")
        raise
    except Exception as e:
        print(f"An error occurred: {e}")
        raise


def process_youtube_link(youtube_link):
    # Simplified paths for debugging
    downloaded_file_path = "/tmp/BigBuckBunny.mp4"
    temp_output_path = "/tmp/BigBuckBunny.mp3"

    # Log the paths
    print(f"Downloaded file path: {downloaded_file_path}")
    print(f"Temporary output path: {temp_output_path}")

    # Download the file
    success = download_youtube_video(youtube_link, downloaded_file_path)

    if not success:
        print("Download step failed.")
        return

    # Ensure the downloaded file exists
    if not os.path.exists(downloaded_file_path):
        print(f"File not found after download: {downloaded_file_path}")
        return

    # Convert the audio
    convert_audio(downloaded_file_path, temp_output_path)


# Example usage
if __name__ == '__main__':
    youtube_link = "https://www.youtube.com/watch?v=E8RQVx2gBFc"
    process_youtube_link(youtube_link)
