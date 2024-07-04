from pytube import YouTube
import sys
import whisper


def on_progress(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage_of_completion = bytes_downloaded / total_size * 100
    progress = f'Download progress: {int(percentage_of_completion)}%'
    sys.stdout.write('\r' + progress)
    sys.stdout.flush()


link = input("Please provide YouTube video link: ")
yt = YouTube(link, on_progress_callback=on_progress)

resolution_choice = int(input("Please choose resolution, 1 - highest, 2 - lowest: "))

stream = None

if resolution_choice == 1:
    stream = yt.streams.get_highest_resolution()
elif resolution_choice == 2:
    stream = yt.streams.get_lowest_resolution()
else:
    print("Ups, you missclicked")

if resolution_choice == 1 or resolution_choice == 2:
    stream.download(filename="video_1.mp4")
    print("\nDownload complete!")

model = whisper.load_model("base")
result = model.transcribe(f"video_1.mp4")
with open(f"video_1.txt", "w") as file:
    file.write(result['text'])

print("Transcription saved")
